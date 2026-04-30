from rest_framework.routers import DefaultRouter

from Backend.Apps.MainApp import views

router = DefaultRouter()
router.register("OnboardingOffers", views.OnboardingOfferViewSet, basename="mainapp-onboarding-offers")
router.register("LeaveRequests", views.LeaveRequestViewSet, basename="mainapp-leave-requests")
router.register("Notifications", views.NotificationItemViewSet, basename="mainapp-notifications")
router.register("CredentialVaultItems", views.CredentialVaultItemViewSet, basename="mainapp-credential-vault-items")
router.register("CredentialShareGrants", views.CredentialShareGrantViewSet, basename="mainapp-credential-share-grants")
router.register("ExternalIssueReferences", views.ExternalIssueReferenceViewSet, basename="mainapp-external-issue-references")
router.register("NotificationSnoozeRecords", views.NotificationSnoozeRecordViewSet, basename="mainapp-notification-snooze-records")
router.register("ManagerScopes", views.ManagerScopeViewSet, basename="mainapp-manager-scopes")

urlpatterns = router.urls
