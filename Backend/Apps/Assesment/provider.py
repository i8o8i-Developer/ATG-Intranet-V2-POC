from django.conf import settings

import requests


class ExternalAssessmentProviderClient:
    def __init__(self, base_url=None, timeout=15, session=None):
        self.base_url = (base_url or getattr(settings, "ASSESSMENT_PROVIDER_BASE_URL", "https://assessmntbackend.atg.world")).rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def generate_link(self, email, assessment_id):
        response = self.session.post(
            f"{self.base_url}/users/generate-links",
            json={"assessment_template_id": assessment_id, "emails": [email]},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return self._normalize_generated_payload(response.json())

    def send_link(self, payload):
        request_payload = payload.get("send_payload", payload) if isinstance(payload, dict) else payload
        response = self.session.post(f"{self.base_url}/users/send-links", json=request_payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def fetch_status(self, external_user_id, assessment_id, assignment_id=None):
        response = self.session.get(
            f"{self.base_url}/users/user",
            params={"id": external_user_id, "assessment_id": assessment_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _normalize_generated_payload(payload):
        send_payload = payload.get("result") if isinstance(payload, dict) else None
        if not isinstance(send_payload, dict):
            send_payload = payload if isinstance(payload, dict) else {}
        links = send_payload.get("links") or payload.get("links") or []
        first_link = links[0] if links else {}
        external_user_id = (
            first_link.get("userId")
            or first_link.get("user_id")
            or send_payload.get("userId")
            or send_payload.get("user_id")
            or payload.get("user_id")
            or ""
        )
        assessment_url = (
            first_link.get("link")
            or first_link.get("url")
            or send_payload.get("assessment_url")
            or payload.get("assessment_url")
            or ""
        )
        return {
            "raw": payload,
            "send_payload": send_payload,
            "external_user_id": external_user_id,
            "assessment_url": assessment_url,
            "assessment_template_id": send_payload.get("assessment_template_id") or payload.get("assessment_template_id") or "",
        }
