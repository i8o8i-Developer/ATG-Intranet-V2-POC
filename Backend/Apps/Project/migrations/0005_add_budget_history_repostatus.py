from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0003_add_profile_fields'),
        ('Project', '0004_add_milestone_flag'),
        ('EnterpriseCore', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectBudget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('total_budget', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('role_and_budget', models.JSONField(blank=True, default=dict)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to='Project.projectworkspace')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='EnterpriseCore.tenant')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='EnterpriseCore.workspace')),
            ],
            options={'ordering': ['tenant_id', '-created_at']},
        ),
        migrations.CreateModel(
            name='TeamAssignmentHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('action', models.CharField(choices=[('added', 'Added'), ('removed', 'Removed'), ('replaced', 'Replaced'), ('added_back', 'Added Back'), ('status_changed', 'Status Changed')], max_length=40)),
                ('comment', models.TextField(blank=True)),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='team_history_changes', to='Users.employeeprofile')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('team_assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='Project.teamassignment')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='EnterpriseCore.tenant')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='EnterpriseCore.workspace')),
            ],
            options={'ordering': ['tenant_id', '-created_at']},
        ),
        migrations.CreateModel(
            name='UserRepositoryStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('status', models.CharField(blank=True, max_length=80)),
                ('last_checked', models.DateTimeField(default=django.utils.timezone.now)),
                ('days_since', models.PositiveIntegerField(default=0)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repository_statuses', to='Users.employeeprofile')),
                ('repository', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_statuses', to='Project.repositorylink')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='EnterpriseCore.tenant')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='EnterpriseCore.workspace')),
            ],
            options={'ordering': ['tenant_id', '-last_checked']},
        ),
        migrations.AddConstraint(
            model_name='userrepositorystatus',
            constraint=models.UniqueConstraint(fields=['tenant', 'repository', 'employee'], name='project_user_repo_status_once'),
        ),
    ]
