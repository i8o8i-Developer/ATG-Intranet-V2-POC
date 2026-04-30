from Backend.Apps.Users.apis import TenantContextAPIView
from Backend.Apps.Users.interviewgod import InterviewGodClient
from Backend.Apps.Users.services import InterviewSyncService
from rest_framework.response import Response


class RunInterviewSyncAPIView(TenantContextAPIView):
    def post(self, request):
        result = InterviewSyncService.sync_interns(
            self.get_context(request),
            employee_id=request.data.get("employee") or request.data.get("user"),
            dry_run=request.data.get("dry_run", True),
            send_links=request.data.get("send_links", False),
            client=InterviewGodClient() if not request.data.get("dry_run", True) else None,
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class CreateInterviewCandidatesAPIView(TenantContextAPIView):
    def post(self, request):
        result = InterviewSyncService.sync_interns(
            self.get_context(request),
            employee_id=request.data.get("employee") or request.data.get("user"),
            dry_run=request.data.get("dry_run", True),
            send_links=False,
            mode="create_candidates",
            client=InterviewGodClient() if not request.data.get("dry_run", True) else None,
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class SendInterviewsAPIView(TenantContextAPIView):
    def post(self, request):
        result = InterviewSyncService.sync_interns(
            self.get_context(request),
            employee_id=request.data.get("employee") or request.data.get("user"),
            dry_run=request.data.get("dry_run", True),
            send_links=True,
            mode="send_interviews",
            client=InterviewGodClient() if not request.data.get("dry_run", True) else None,
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)


class SendInterviewForUserAPIView(SendInterviewsAPIView):
    def post(self, request, user_id):
        result = InterviewSyncService.sync_interns(
            self.get_context(request),
            employee_id=user_id,
            dry_run=request.data.get("dry_run", True),
            send_links=True,
            mode="send_interviews",
            client=InterviewGodClient() if not request.data.get("dry_run", True) else None,
        )
        return Response(result.data if result.ok else result.errors, status=result.status_code)
