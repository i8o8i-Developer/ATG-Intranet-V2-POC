from dataclasses import dataclass

from django.conf import settings
from django.db import models
from django.utils import timezone

import requests

from Backend.Apps.Users.models import EmployeeProfile, InterviewProgress
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class InterviewGodError(Exception):
    pass


class InterviewGodAuthError(InterviewGodError):
    pass


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: dict | None = None


class InterviewGodClient:
    def __init__(self, base_url=None, auth_token=None, refresh_token=None, timeout=15, session=None):
        self.base_url = (base_url or getattr(settings, "INTERVIEWGOD_BASE_URL", "")).rstrip("/")
        self.auth_token = auth_token or getattr(settings, "INTERVIEWGOD_AUTH_TOKEN", "")
        self.refresh_token = refresh_token or getattr(settings, "INTERVIEWGOD_REFRESH_TOKEN", "")
        self.timeout = timeout
        self.session = session or requests.Session()

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def _request(self, method, endpoint, **kwargs):
        if not self.base_url:
            raise InterviewGodAuthError("InterviewGod base URL is not configured.")
        response = self.session.request(method, f"{self.base_url}{endpoint}", headers=self._headers(), timeout=self.timeout, **kwargs)
        if response.status_code == 401 and self.refresh_token:
            self.refresh_access_token()
            response = self.session.request(method, f"{self.base_url}{endpoint}", headers=self._headers(), timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    def refresh_access_token(self):
        endpoint = getattr(settings, "INTERVIEWGOD_REFRESH_ENDPOINT", "/auth/refresh")
        payload = {"refresh_token": self.refresh_token}
        response = self.session.post(f"{self.base_url}{endpoint}", json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token") or data.get("token")
        if not token:
            raise InterviewGodAuthError("InterviewGod refresh response did not include an access token.")
        self.auth_token = token
        return token

    def create_candidate(self, employee, payload=None):
        endpoint = getattr(settings, "INTERVIEWGOD_CANDIDATE_ENDPOINT", "/candidates")
        return self._request("post", endpoint, json=payload or InterviewGodService.build_candidate_payload(employee))

    def send_interview(self, interview_progress, payload=None):
        endpoint = getattr(settings, "INTERVIEWGOD_SEND_ENDPOINT", "/interviews/send")
        body = payload or {
            "candidate_id": interview_progress.candidate_id,
            "job_id": interview_progress.job_id,
            "employee_code": interview_progress.employee.employee_code,
        }
        return self._request("post", endpoint, json=body)

    @staticmethod
    def extract_candidate_id(payload):
        if not isinstance(payload, dict):
            return ""
        for key in ["candidate_id", "candidateId", "id"]:
            if payload.get(key):
                return str(payload[key])
        data = payload.get("data")
        if isinstance(data, dict):
            return InterviewGodClient.extract_candidate_id(data)
        return ""


class InterviewGodService:
    @staticmethod
    def validate_employee(employee):
        errors = {}
        if not employee.user.email:
            errors["email"] = "Employee user email is required."
        if not employee.display_name:
            errors["display_name"] = "Employee display name is required."
        return ValidationResult(ok=not errors, errors=errors or None)

    @staticmethod
    def build_candidate_payload(employee, extra=None):
        payload = {
            "name": employee.display_name,
            "email": employee.user.email,
            "employee_code": employee.employee_code,
            "department": employee.department.name if employee.department_id else "",
            "position": employee.position.title if employee.position_id else "",
            "metadata": {"employee_id": employee.id, "tenant_id": employee.tenant_id},
        }
        if extra:
            payload.update(extra)
        return payload

    @staticmethod
    def intern_queryset(context, employee_id=None):
        queryset = EmployeeProfile.objects.filter(tenant=context.tenant, is_active=True).select_related("user", "department", "position")
        if employee_id:
            return queryset.filter(id=employee_id)
        return queryset.filter(models.Q(employment_type__icontains="intern") | models.Q(position__title__icontains="intern"))

    @staticmethod
    def run_scheduler(context, employee_id=None, mode="sync", dry_run=True, send_links=False, client=None):
        client = client or (None if dry_run else InterviewGodClient())
        rows = []
        for employee in InterviewGodService.intern_queryset(context, employee_id=employee_id):
            validation = InterviewGodService.validate_employee(employee)
            progress, _created = InterviewProgress.objects.get_or_create(
                tenant=context.tenant,
                workspace=context.workspace or employee.workspace,
                employee=employee,
                defaults={"status": "Pending", "created_by": context.actor, "updated_by": context.actor},
            )
            if not validation.ok:
                progress.status = "ValidationFailed"
                progress.last_error = str(validation.errors)
                progress.save(update_fields=["status", "last_error", "updated_at"])
                rows.append({"employeeId": employee.id, "status": progress.status, "errors": validation.errors})
                continue
            if dry_run:
                rows.append({"employeeId": employee.id, "status": progress.status, "dryRun": True, "mode": mode})
                continue
            try:
                if mode in {"sync", "create_candidates"} and not progress.candidate_id:
                    candidate_payload = client.create_candidate(employee)
                    progress.candidate_id = InterviewGodClient.extract_candidate_id(candidate_payload)
                    progress.metadata = {**progress.metadata, "candidate_response": candidate_payload}
                    progress.status = "CandidateCreated" if progress.candidate_id else "Pending"
                if mode in {"sync", "send_interviews"} and send_links and progress.candidate_id:
                    send_payload = client.send_interview(progress)
                    progress.metadata = {**progress.metadata, "send_response": send_payload}
                    progress.status = "InterviewSent"
                    progress.last_sent_at = timezone.now()
                progress.last_error = ""
            except Exception as exc:
                progress.status = "Failed"
                progress.last_error = str(exc)
            progress.updated_by = context.actor
            progress.save(update_fields=["candidate_id", "status", "last_sent_at", "last_error", "metadata", "updated_by", "updated_at"])
            OutboxService.publish(context, "InterviewProgress", progress.id, "InterviewGodSyncRecorded", {"employeeId": employee.id, "status": progress.status})
            rows.append({"employeeId": employee.id, "status": progress.status, "candidateId": progress.candidate_id})
        return ServiceResult.success({"count": len(rows), "rows": rows, "mode": mode})
