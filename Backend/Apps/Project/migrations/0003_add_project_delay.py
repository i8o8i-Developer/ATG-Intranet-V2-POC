# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Project', '0002_complianceassignment_score_and_more'),
        ('EnterpriseCore', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectDelay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('delay_type', models.CharField(db_index=True, max_length=40)),
                ('item_id', models.PositiveIntegerField()),
                ('days', models.PositiveIntegerField(default=0)),
                ('reason', models.TextField()),
                ('status', models.CharField(db_index=True, default='Active', max_length=40)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_delays', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='project_projectdelay', to='EnterpriseCore.tenant')),
                ('workspace', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_projectdelay', to='EnterpriseCore.workspace')),
            ],
            options={
                'ordering': ['tenant_id', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='projectdelay',
            index=models.Index(fields=['tenant', 'delay_type', 'status'], name='Project_pro_tenant__idx'),
        ),
        migrations.AddIndex(
            model_name='projectdelay',
            index=models.Index(fields=['tenant', 'item_id'], name='Project_pro_tenant_2_idx'),
        ),
    ]
