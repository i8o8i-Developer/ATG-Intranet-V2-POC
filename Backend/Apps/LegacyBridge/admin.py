from django.contrib import admin

from Backend.Apps.LegacyBridge.models import LegacyApplicationMap, LegacyMigrationIssue, LegacyModelCrosswalk, MigrationRun


admin.site.register(LegacyApplicationMap)
admin.site.register(LegacyModelCrosswalk)
admin.site.register(MigrationRun)
admin.site.register(LegacyMigrationIssue)