# Generated for organization-level user membership.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clubs', '0002_organization'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ عضویت')),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='memberships',
                    to='clubs.organization',
                    verbose_name='مجموعه',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='organization_memberships',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='کاربر',
                )),
            ],
            options={
                'verbose_name': 'عضویت مجموعه',
                'verbose_name_plural': 'عضویت‌های مجموعه',
            },
        ),
        migrations.AddConstraint(
            model_name='organizationmembership',
            constraint=models.UniqueConstraint(
                fields=('user', 'organization'),
                name='uniq_org_membership_user_org',
            ),
        ),
    ]
