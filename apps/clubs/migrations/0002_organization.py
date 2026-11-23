# Generated for the initial multi-tenant foundation.
from django.db import migrations, models
import django.db.models.deletion


def attach_existing_clubs_to_default_organization(apps, schema_editor):
    Organization = apps.get_model('clubs', 'Organization')
    Club = apps.get_model('clubs', 'Club')

    organization, _ = Organization.objects.get_or_create(
        slug='default',
        defaults={'name': 'مجموعه پیش‌فرض'},
    )
    Club.objects.filter(organization__isnull=True).update(organization=organization)


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='نام مجموعه')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='شناسه یکتا')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
            ],
            options={
                'verbose_name': 'مجموعه',
                'verbose_name_plural': 'مجموعه‌ها',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='club',
            name='organization',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='branches',
                to='clubs.organization',
                verbose_name='مجموعه',
            ),
        ),
        migrations.RunPython(attach_existing_clubs_to_default_organization, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='club',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='branches',
                to='clubs.organization',
                verbose_name='مجموعه',
            ),
        ),
    ]
