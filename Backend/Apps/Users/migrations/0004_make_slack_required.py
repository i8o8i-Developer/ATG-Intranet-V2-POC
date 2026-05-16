from django.db import migrations, models


def set_default_slack(apps, schema_editor):
    EmployeeProfile = apps.get_model('Users', 'EmployeeProfile')
    EmployeeProfile.objects.filter(slack_username__isnull=True).update(slack_username='')
    EmployeeProfile.objects.filter(slack_username='').update(slack_username=models.F('employee_code'))


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0003_add_profile_fields'),
    ]

    operations = [
        migrations.RunPython(set_default_slack, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='employeeprofile',
            name='slack_username',
            field=models.CharField(max_length=120),
        ),
    ]
