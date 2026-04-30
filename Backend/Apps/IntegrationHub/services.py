from django.utils import timezone

from Backend.Apps.IntegrationHub.models import IntegrationAttempt, IntegrationProvider, IntegrationSyncJob, WebhookInboxEvent
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class IntegrationJobService:
    @staticmethod
    def queue_sync(context, connection, job_type, cursor=""):
        job = IntegrationSyncJob.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            connection=connection,
            job_type=job_type,
            cursor=cursor,
            created_by=context.actor,
        )
        OutboxService.publish(context, "IntegrationSyncJob", job.id, "IntegrationSyncQueued", {"jobType": job_type, "connectionId": connection.id})
        return ServiceResult.success(job, status_code=201)

    @staticmethod
    def record_attempt(context, connection, operation, request_payload=None, response_payload=None, status="Pending"):
        attempt = IntegrationAttempt.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            connection=connection,
            operation=operation,
            status=status,
            request_payload=request_payload or {},
            response_payload=response_payload or {},
            created_by=context.actor,
        )
        return ServiceResult.success(attempt, status_code=201)

    @staticmethod
    def start_job(context, job_id):
        job = IntegrationSyncJob.objects.filter(tenant=context.tenant, id=job_id).first()
        if not job:
            return ServiceResult.failure({"job": "Integration sync job not found."}, status_code=404)
        job.status = "Running"
        job.started_at = timezone.now()
        job.attempt_count += 1
        job.updated_by = context.actor
        job.save(update_fields=["status", "started_at", "attempt_count", "updated_by", "updated_at"])
        return ServiceResult.success(job)

    @staticmethod
    def complete_job(context, job_id, result_payload=None):
        job = IntegrationSyncJob.objects.filter(tenant=context.tenant, id=job_id).first()
        if not job:
            return ServiceResult.failure({"job": "Integration sync job not found."}, status_code=404)
        job.status = "Completed"
        job.finished_at = timezone.now()
        job.result_payload = result_payload or job.result_payload
        job.failure_reason = ""
        job.updated_by = context.actor
        job.save(update_fields=["status", "finished_at", "result_payload", "failure_reason", "updated_by", "updated_at"])
        OutboxService.publish(context, "IntegrationSyncJob", job.id, "IntegrationSyncCompleted", {"jobType": job.job_type})
        return ServiceResult.success(job)

    @staticmethod
    def fail_job(context, job_id, failure_reason):
        job = IntegrationSyncJob.objects.filter(tenant=context.tenant, id=job_id).first()
        if not job:
            return ServiceResult.failure({"job": "Integration sync job not found."}, status_code=404)
        job.status = "Failed"
        job.finished_at = timezone.now()
        job.failure_reason = failure_reason
        job.updated_by = context.actor
        job.save(update_fields=["status", "finished_at", "failure_reason", "updated_by", "updated_at"])
        return ServiceResult.success(job)

    @staticmethod
    def retry_failed_jobs(context, connection=None):
        jobs = IntegrationSyncJob.objects.filter(tenant=context.tenant, status="Failed")
        if connection:
            jobs = jobs.filter(connection=connection)
        queued = []
        for job in jobs:
            retry = IntegrationSyncJob.objects.create(
                tenant=context.tenant,
                workspace=context.workspace or job.workspace,
                connection=job.connection,
                job_type=job.job_type,
                cursor=job.cursor,
                result_payload={"retryOf": job.id},
                created_by=context.actor,
                updated_by=context.actor,
            )
            queued.append(retry.id)
        return ServiceResult.success({"count": len(queued), "jobIds": queued}, status_code=201)


class WebhookInboxService:
    @staticmethod
    def receive(context, provider_id=None, event_type="unknown", external_event_id="", payload=None, headers=None):
        provider = IntegrationProvider.objects.filter(tenant=context.tenant, id=provider_id).first() if provider_id else None
        event = WebhookInboxEvent.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            provider=provider,
            event_type=event_type,
            external_event_id=external_event_id,
            payload=payload or {},
            headers=headers or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        OutboxService.publish(context, "WebhookInboxEvent", event.id, "WebhookReceived", {"eventType": event_type, "providerId": provider_id})
        return ServiceResult.success(event, status_code=201)

    @staticmethod
    def mark_processed(context, event_id, status="Processed", failure_reason=""):
        event = WebhookInboxEvent.objects.filter(tenant=context.tenant, id=event_id).first()
        if not event:
            return ServiceResult.failure({"webhook": "Webhook event not found."}, status_code=404)
        event.status = status
        event.processed_at = timezone.now()
        event.failure_reason = failure_reason
        event.processing_attempts += 1
        event.updated_by = context.actor
        event.save(update_fields=["status", "processed_at", "failure_reason", "processing_attempts", "updated_by", "updated_at"])
        return ServiceResult.success(event)
