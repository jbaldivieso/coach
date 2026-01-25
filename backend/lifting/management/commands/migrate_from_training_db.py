"""
Migrate data from the old training.db SQLite database to the new Django models.

Mapping:
    Source (training.db)              Target (Django)
    -----------------------------------------------
    lifting_sessions.name         ->  Session.title
    lifting_sessions.date         ->  Session.date
    lifting_sessions.notes        ->  Session.comments
    (default)                     ->  Session.session_type = "volume"
    (argument)                    ->  Session.user_id

    lifting_exercises.exercise_name -> Exercise.title
    lifting_exercises.session_id    -> Exercise.session_id (remapped)
    lifting_exercises.weight        -> Exercise.weight_lbs (rounded to int)
    lifting_exercises.rest_seconds  -> Exercise.rest_seconds
    lifting_exercises.reps_per_set  -> Exercise.reps
    lifting_exercises.notes         -> Exercise.comments

Usage:
    python manage.py migrate_from_training_db /path/to/training.db --user-id 1
    python manage.py migrate_from_training_db /path/to/training.db --user-id 1 --dry-run
"""

import json
import sqlite3
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction

from lifting.models import Session, Exercise


class Command(BaseCommand):
    help = "Migrate lifting sessions and exercises from an old training.db SQLite database"

    def add_arguments(self, parser):
        parser.add_argument(
            "source_db",
            type=str,
            help="Path to the source training.db SQLite file",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            default=1,
            help="User ID to assign migrated sessions to (default: 1)",
        )
        parser.add_argument(
            "--session-type",
            type=str,
            default="volume",
            choices=["volume", "weight", "endurance", "recovery"],
            help="Session type for all migrated sessions (default: volume)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without making changes",
        )

    def handle(self, *args, **options):
        source_db = options["source_db"]
        user_id = options["user_id"]
        session_type = options["session_type"]
        dry_run = options["dry_run"]

        # Validate user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise CommandError(f"User with ID {user_id} does not exist")

        self.stdout.write(f"Migrating from: {source_db}")
        self.stdout.write(f"Assigning to user: {user.username} (ID: {user_id})")
        self.stdout.write(f"Session type: {session_type}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be made"))

        # Connect to source database
        try:
            conn = sqlite3.connect(source_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        except sqlite3.Error as e:
            raise CommandError(f"Failed to open source database: {e}")

        # Read all sessions from source
        cursor.execute(
            "SELECT id, date, name, notes FROM lifting_sessions ORDER BY id"
        )
        source_sessions = cursor.fetchall()

        # Read all exercises from source
        cursor.execute(
            "SELECT id, session_id, exercise_name, weight, reps_per_set, rest_seconds, notes "
            "FROM lifting_exercises ORDER BY session_id, id"
        )
        source_exercises = cursor.fetchall()

        conn.close()

        self.stdout.write(f"\nFound {len(source_sessions)} sessions and {len(source_exercises)} exercises")

        # Group exercises by session_id
        exercises_by_session = {}
        for ex in source_exercises:
            session_id = ex["session_id"]
            if session_id not in exercises_by_session:
                exercises_by_session[session_id] = []
            exercises_by_session[session_id].append(ex)

        if dry_run:
            self._dry_run_report(source_sessions, exercises_by_session, session_type)
            return

        # Perform the migration
        sessions_created = 0
        exercises_created = 0

        with transaction.atomic():
            for src_session in source_sessions:
                # Create the Session
                new_session = Session.objects.create(
                    title=src_session["name"],
                    date=src_session["date"],
                    comments=src_session["notes"] or "",
                    session_type=session_type,
                    user=user,
                )
                sessions_created += 1

                # Create exercises for this session
                src_exercises = exercises_by_session.get(src_session["id"], [])
                for src_ex in src_exercises:
                    # Parse reps_per_set JSON
                    try:
                        reps = json.loads(src_ex["reps_per_set"])
                    except (json.JSONDecodeError, TypeError):
                        reps = []
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Warning: Invalid reps_per_set for exercise {src_ex['id']}: {src_ex['reps_per_set']}"
                            )
                        )

                    # Convert weight to int (rounding)
                    weight = src_ex["weight"]
                    weight_lbs = round(weight) if weight is not None else None

                    Exercise.objects.create(
                        title=src_ex["exercise_name"],
                        session=new_session,
                        weight_lbs=weight_lbs,
                        rest_seconds=src_ex["rest_seconds"] or 0,
                        reps=reps,
                        comments=src_ex["notes"] or "",
                    )
                    exercises_created += 1

                self.stdout.write(
                    f"  Migrated: {src_session['name']} ({src_session['date']}) - {len(src_exercises)} exercises"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nMigration complete: {sessions_created} sessions, {exercises_created} exercises"
            )
        )

    def _dry_run_report(self, source_sessions, exercises_by_session, session_type):
        """Print a detailed report of what would be migrated."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("MIGRATION PREVIEW")
        self.stdout.write("=" * 60)

        for src_session in source_sessions:
            src_exercises = exercises_by_session.get(src_session["id"], [])
            self.stdout.write(
                f"\nSession: {src_session['name']} ({src_session['date']})"
            )
            self.stdout.write(f"  Type: {session_type}")
            if src_session["notes"]:
                self.stdout.write(f"  Notes: {src_session['notes'][:50]}...")

            for src_ex in src_exercises:
                weight = src_ex["weight"]
                weight_str = f"{round(weight)} lbs" if weight else "bodyweight"
                self.stdout.write(
                    f"    - {src_ex['exercise_name']}: {weight_str}, reps={src_ex['reps_per_set']}"
                )

        self.stdout.write("\n" + "=" * 60)
