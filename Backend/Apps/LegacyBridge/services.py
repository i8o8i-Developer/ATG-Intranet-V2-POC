from Backend.Apps.LegacyBridge.legacy_app_map import LEGACY_APP_TO_BACKEND_APP
from Backend.Apps.LegacyBridge.models import LegacyApplicationMap, LegacyMigrationIssue, LegacyModelCrosswalk, MigrationRun
from Backend.EnterpriseCore.services import OutboxService, ServiceResult
from django.utils import timezone


class LegacyMappingService:
    @staticmethod
    def seed_default_app_map(context):
        created = []
        for legacy_app, backend_app in LEGACY_APP_TO_BACKEND_APP.items():
            item, was_created = LegacyApplicationMap.objects.get_or_create(
                tenant=context.tenant,
                workspace=context.workspace,
                legacy_app_label=legacy_app,
                backend_app_label=backend_app,
                defaults={"created_by": context.actor},
            )
            if was_created:
                created.append(item.id)
        return ServiceResult.success({"createdIds": created, "count": len(created)})

    @staticmethod
    def preview_default_app_map(context):
        rows = []
        for legacy_app, backend_app in LEGACY_APP_TO_BACKEND_APP.items():
            mapped = LegacyApplicationMap.objects.filter(tenant=context.tenant, legacy_app_label=legacy_app, backend_app_label=backend_app).exists()
            rows.append({"legacy_app_label": legacy_app, "backend_app_label": backend_app, "mapped": mapped})
        return ServiceResult.success({"count": len(rows), "rows": rows})


class LegacyMigrationService:
    @staticmethod
    def start_run(context, source_app_label, target_app_label="", mode="Preview", dry_run=True, batch_id="", total_rows=0):
        target_app_label = target_app_label or LEGACY_APP_TO_BACKEND_APP.get(source_app_label, source_app_label)
        run = MigrationRun.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            batch_id=batch_id or f"{source_app_label}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            source_app_label=source_app_label,
            target_app_label=target_app_label,
            mode=mode,
            dry_run=dry_run,
            status="Running",
            started_at=timezone.now(),
            total_rows=total_rows or 0,
            created_by=context.actor,
            updated_by=context.actor,
        )
        OutboxService.publish(context, "MigrationRun", run.id, "LegacyMigrationStarted", {"source": source_app_label, "dryRun": dry_run})
        return ServiceResult.success(run, status_code=201)

    @staticmethod
    def complete_run(context, run_id, migrated_rows=0, skipped_rows=0, result_payload=None):
        run = MigrationRun.objects.filter(tenant=context.tenant, id=run_id).first()
        if not run:
            return ServiceResult.failure({"migrationRun": "Migration run not found."}, status_code=404)
        run.status = "Completed"
        run.finished_at = timezone.now()
        run.migrated_rows = migrated_rows
        run.skipped_rows = skipped_rows
        run.result_payload = result_payload or run.result_payload
        run.updated_by = context.actor
        run.save(update_fields=["status", "finished_at", "migrated_rows", "skipped_rows", "result_payload", "updated_by", "updated_at"])
        OutboxService.publish(context, "MigrationRun", run.id, "LegacyMigrationCompleted", {"migratedRows": migrated_rows})
        return ServiceResult.success(run)

    @staticmethod
    def fail_run(context, run_id, failure_reason):
        run = MigrationRun.objects.filter(tenant=context.tenant, id=run_id).first()
        if not run:
            return ServiceResult.failure({"migrationRun": "Migration run not found."}, status_code=404)
        run.status = "Failed"
        run.finished_at = timezone.now()
        run.failure_reason = failure_reason
        run.updated_by = context.actor
        run.save(update_fields=["status", "finished_at", "failure_reason", "updated_by", "updated_at"])
        LegacyMigrationIssue.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or run.workspace,
            migration_run=run,
            severity="Error",
            source_app_label=run.source_app_label,
            message=failure_reason,
            created_by=context.actor,
            updated_by=context.actor,
        )
        return ServiceResult.success(run)

    @staticmethod
    def record_crosswalk(context, data):
        crosswalk, _created = LegacyModelCrosswalk.objects.update_or_create(
            tenant=context.tenant,
            legacy_app_label=data["legacy_app_label"],
            legacy_model_name=data["legacy_model_name"],
            legacy_object_id=str(data["legacy_object_id"]),
            defaults={
                "workspace": context.workspace,
                "backend_app_label": data.get("backend_app_label", LEGACY_APP_TO_BACKEND_APP.get(data["legacy_app_label"], data["legacy_app_label"])),
                "backend_model_name": data.get("backend_model_name", ""),
                "backend_object_id": str(data.get("backend_object_id", "")),
                "direction": data.get("direction", "LegacyToBackend"),
                "sync_status": data.get("sync_status", "Synced"),
                "migration_batch_id": data.get("migration_batch_id", ""),
                "checksum": data.get("checksum", ""),
                "last_synced_at": timezone.now(),
                "metadata": data.get("metadata") or {},
                "updated_by": context.actor,
            },
        )
        return ServiceResult.success(crosswalk, status_code=201)

    @staticmethod
    def rollback_run(context, run_id):
        run = MigrationRun.objects.filter(tenant=context.tenant, id=run_id).first()
        if not run:
            return ServiceResult.failure({"migrationRun": "Migration run not found."}, status_code=404)
        count = LegacyModelCrosswalk.objects.filter(tenant=context.tenant, migration_batch_id=run.batch_id).update(sync_status="RolledBack", is_active=False, updated_by=context.actor)
        run.status = "RolledBack"
        run.finished_at = timezone.now()
        run.result_payload = {**run.result_payload, "rolledBackCrosswalks": count}
        run.updated_by = context.actor
        run.save(update_fields=["status", "finished_at", "result_payload", "updated_by", "updated_at"])
        return ServiceResult.success({"runId": run.id, "rolledBackCrosswalks": count})
