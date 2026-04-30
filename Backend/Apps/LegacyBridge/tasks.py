from Backend.Apps.LegacyBridge.services import LegacyMappingService, LegacyMigrationService


def seed_default_app_map(context):
    return LegacyMappingService.seed_default_app_map(context)


def start_migration_run(context, source_app_label, **kwargs):
    return LegacyMigrationService.start_run(context, source_app_label, **kwargs)


def record_crosswalk(context, data):
    return LegacyMigrationService.record_crosswalk(context, data)