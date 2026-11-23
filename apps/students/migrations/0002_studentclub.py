# Generated for the student-to-club relationship transition.
import django_jalali.db.models
import jdatetime
from django.db import migrations, models
import django.db.models.deletion


def create_legacy_memberships(apps, schema_editor):
    Student = apps.get_model('students', 'Student')
    StudentClub = apps.get_model('students', 'StudentClub')
    db_alias = schema_editor.connection.alias

    StudentClub.objects.using(db_alias).bulk_create(
        [
            StudentClub(
                student_id=student_id,
                club_id=club_id,
                is_active=True,
                joined_at=joined_at,
            )
            for student_id, club_id, joined_at in Student.objects.using(db_alias).values_list(
                'id', 'club_id', 'joined_at'
            )
        ],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0002_organization'),
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentClub',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('joined_at', django_jalali.db.models.jDateField(default=jdatetime.date.today, verbose_name='تاریخ عضویت')),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='student_memberships', to='clubs.club', verbose_name='باشگاه')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='club_memberships', to='students.student', verbose_name='هنرجو')),
            ],
            options={
                'verbose_name': 'عضویت هنرجو در باشگاه',
                'verbose_name_plural': 'عضویت هنرجویان در باشگاه‌ها',
            },
        ),
        migrations.AddConstraint(
            model_name='studentclub',
            constraint=models.UniqueConstraint(fields=('student', 'club'), name='unique_student_club_membership'),
        ),
        migrations.RunPython(create_legacy_memberships, migrations.RunPython.noop),
    ]
