# Generated migration to remove old weight_lbs and reps fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("lifting", "0003_migrate_to_sets"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="exercise",
            name="weight_lbs",
        ),
        migrations.RemoveField(
            model_name="exercise",
            name="reps",
        ),
    ]
