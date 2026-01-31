# Generated data migration to convert weight_lbs + reps to sets format

from django.db import migrations


def convert_to_sets(apps, schema_editor):
    """
    Convert weight_lbs=50, reps=[10,15,20] to
    sets=[{"weight":50, "reps":10}, {"weight":50, "reps":15}, {"weight":50, "reps":20}]
    """
    Exercise = apps.get_model("lifting", "Exercise")
    for exercise in Exercise.objects.all():
        reps_list = exercise.reps or []
        weight = exercise.weight_lbs  # Can be None for bodyweight
        exercise.sets = [{"weight": weight, "reps": r} for r in reps_list]
        exercise.save()


def convert_from_sets(apps, schema_editor):
    """
    Reverse migration: convert sets back to weight_lbs + reps.
    Uses the weight from the first set (or None if no sets).
    """
    Exercise = apps.get_model("lifting", "Exercise")
    for exercise in Exercise.objects.all():
        sets_list = exercise.sets or []
        if sets_list:
            # Take weight from first set
            exercise.weight_lbs = sets_list[0].get("weight")
            exercise.reps = [s.get("reps") for s in sets_list if s.get("reps") is not None]
        else:
            exercise.weight_lbs = None
            exercise.reps = []
        exercise.save()


class Migration(migrations.Migration):

    dependencies = [
        ("lifting", "0002_add_sets_field"),
    ]

    operations = [
        migrations.RunPython(convert_to_sets, convert_from_sets),
    ]
