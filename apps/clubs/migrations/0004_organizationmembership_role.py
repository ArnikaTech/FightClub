from django.conf import settings
from django.db import migrations, models


def backfill_organization_managers(apps, schema_editor):
    OrganizationMembership = apps.get_model('clubs', 'OrganizationMembership')
    ClubMembership = apps.get_model('clubs', 'ClubMembership')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    db_alias = schema_editor.connection.alias

    manager_ids = User.objects.using(db_alias).filter(is_club_manager=True).values_list('pk', flat=True)
    memberships = ClubMembership.objects.using(db_alias).filter(
        user_id__in=manager_ids,
        is_active=True,
    ).select_related('club')

    seen = set()
    for membership in memberships:
        organization_id = membership.club.organization_id
        key = (membership.user_id, organization_id)
        if key in seen:
            continue
        seen.add(key)
        OrganizationMembership.objects.using(db_alias).get_or_create(
            user_id=membership.user_id,
            organization_id=organization_id,
            defaults={'role': 'manager', 'is_active': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0003_organizationmembership'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationmembership',
            name='role',
            field=models.CharField(
                choices=[('manager', 'مدیر مجموعه')],
                default='manager',
                max_length=20,
                verbose_name='نقش',
            ),
        ),
        migrations.RunPython(backfill_organization_managers, migrations.RunPython.noop),
    ]
