# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Project', '0003_add_project_delay'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryalert',
            name='milestone',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='flags', to='Project.deliverymilestone'),
        ),
    ]
