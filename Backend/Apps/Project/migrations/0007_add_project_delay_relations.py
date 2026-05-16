# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('TasksDashboard', '0001_initial'),
        ('Users', '0001_initial'),
        ('Project', '0006_add_apm_pm_fields'),
        ('EnterpriseCore', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectdelay',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='delays', to='Project.projectworkspace'),
        ),
        migrations.AddField(
            model_name='projectdelay',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='delays', to='TasksDashboard.workitem'),
        ),
        migrations.AddField(
            model_name='projectdelay',
            name='reported_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reported_delays', to='Users.employeeprofile'),
        ),
    ]
