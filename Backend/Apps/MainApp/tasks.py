from Backend.Apps.MainApp.services import OfferLifecycleService


def check_and_send_reminders(context):
    return OfferLifecycleService.queue_offer_reminders(context)


def send_offer_reminder(context, offer):
    return OfferLifecycleService.issue_offer(context, offer.id)