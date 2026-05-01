from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Banao", "0002_leadnote_leadtest_workflowstatushistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="leadaccount",
            name="action_item",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="leadaccount",
            name="connection_id",
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AddField(
            model_name="leadaccount",
            name="industry",
            field=models.CharField(blank=True, db_index=True, max_length=120),
        ),
        migrations.AddField(
            model_name="leadaccount",
            name="latest_comment",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="leadaccount",
            name="next_follow_up_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="leadaccount",
            name="source_page_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="leadaccount",
            name="source_page_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="leadaccount",
            name="website_url",
            field=models.URLField(blank=True),
        ),
    ]