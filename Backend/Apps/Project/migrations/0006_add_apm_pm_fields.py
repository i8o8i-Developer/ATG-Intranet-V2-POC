from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0003_add_profile_fields'),
        ('Project', '0005_add_budget_history_repostatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectworkspace',
            name='associate_project_manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='apm_projects', to='Users.employeeprofile'),
        ),
        migrations.AddField(
            model_name='projectworkspace',
            name='project_manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pm_projects', to='Users.employeeprofile'),
        ),
    ]
