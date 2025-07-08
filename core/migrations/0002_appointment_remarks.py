from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='Appointment',
            name='remarks',
            field=models.TextField(
                blank=True, help_text='Important information or medication details (editable by professional only)'
            ),
        ),
    ]