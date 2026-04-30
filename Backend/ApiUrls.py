from django.urls import include, path

urlpatterns = [
    path("EnterpriseCore/", include("Backend.EnterpriseCore.urls")),
    path("Users/", include("Backend.Apps.Users.urls")),
    path("MainApp/", include("Backend.Apps.MainApp.urls")),
    path("Project/", include("Backend.Apps.Project.urls")),
    path("TasksDashboard/", include("Backend.Apps.TasksDashboard.urls")),
    path("Banao/", include("Backend.Apps.Banao.urls")),
    path("Lms/", include("Backend.Apps.Lms.urls")),
    path("AtgDocs/", include("Backend.Apps.AtgDocs.urls")),
    path("Assesment/", include("Backend.Apps.Assesment.urls")),
    path("L3/", include("Backend.Apps.L3.urls")),
    path("GithubExtension/", include("Backend.Apps.GithubExtension.urls")),
    path("Git/", include("Backend.Apps.Git.urls")),
    path("HtmlTemplate/", include("Backend.Apps.HtmlTemplate.urls")),
    path("WorkflowIntelligence/", include("Backend.Apps.WorkflowIntelligence.urls")),
    path("FinanceAndPayroll/", include("Backend.Apps.FinanceAndPayroll.urls")),
    path("IntegrationHub/", include("Backend.Apps.IntegrationHub.urls")),
    path("McpAccessLayer/", include("Backend.Apps.McpAccessLayer.urls")),
    path("LegacyBridge/", include("Backend.Apps.LegacyBridge.urls")),
]
