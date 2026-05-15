from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0003_add_profile_fields'),
        ('Banao', '0003_leadaccount_legacy_public_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='leadaccount',
            name='call_status',
            field=models.CharField(blank=True, db_index=True, max_length=30),
        ),
        migrations.AddField(
            model_name='leadaccount',
            name='call_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leadaccount',
            name='takeover_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leads_taken_over', to='Users.employeeprofile'),
        ),
    ]
