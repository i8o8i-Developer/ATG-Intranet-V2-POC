# Generated manually - adds new profile fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0002_department_base_pay_department_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeeprofile',
            name='city',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='college_name',
            field=models.CharField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='year_of_graduation',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='availability_hours',
            field=models.PositiveIntegerField(default=40),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='calendar_id',
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='slack_username',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='payprofile',
            name='performance_pay',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
    ]
