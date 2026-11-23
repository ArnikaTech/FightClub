# Generated to synchronize FeeDue.month field metadata.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_paymenttransaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedue',
            name='month',
            field=models.CharField(
                help_text='مثلاً: 1405/05',
                max_length=7,
                verbose_name='ماه',
            ),
        ),
    ]
