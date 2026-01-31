# Generated migration to add sets JSONField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lifting", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="exercise",
            name="sets",
            field=models.JSONField(default=list),
        ),
    ]
