from Backend.Apps.IntegrationHub.services import IntegrationJobService, WebhookInboxService


def queue_sync(context, connection, job_type="ManualSync", cursor=""):
    return IntegrationJobService.queue_sync(context, connection, job_type, cursor=cursor)


def receive_webhook(context, **kwargs):
    return WebhookInboxService.receive(context, **kwargs)


def retry_failed_jobs(context, connection=None):
    return IntegrationJobService.retry_failed_jobs(context, connection=connection)