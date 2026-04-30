from django import forms

from Backend.Apps.LegacyBridge.models import LegacyApplicationMap, LegacyMigrationIssue, LegacyModelCrosswalk, MigrationRun


class LegacyApplicationMapForm(forms.ModelForm):
    class Meta:
        model = LegacyApplicationMap
        fields = ["legacy_app_label", "backend_app_label", "target_domain", "route_prefix", "migration_status", "notes", "metadata"]


class LegacyModelCrosswalkForm(forms.ModelForm):
    class Meta:
        model = LegacyModelCrosswalk
        fields = ["legacy_app_label", "legacy_model_name", "legacy_object_id", "backend_app_label", "backend_model_name", "backend_object_id", "direction", "sync_status", "migration_batch_id", "checksum", "metadata"]


class MigrationRunForm(forms.ModelForm):
    class Meta:
        model = MigrationRun
        fields = ["batch_id", "source_app_label", "target_app_label", "mode", "dry_run", "status", "total_rows", "migrated_rows", "skipped_rows", "result_payload", "failure_reason"]


class LegacyMigrationIssueForm(forms.ModelForm):
    class Meta:
        model = LegacyMigrationIssue
        fields = ["migration_run", "severity", "source_app_label", "legacy_model_name", "legacy_object_id", "message", "resolution_status", "metadata"]