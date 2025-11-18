#!/usr/bin/env python3
"""
Flask web application for training plan management.
"""

import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

import markdown
from flask import Flask, flash, redirect, render_template, request, url_for
from markupsafe import Markup

app = Flask(__name__)
app.secret_key = "your-secret-key-here-change-in-production"


@app.template_filter("markdown")
def markdown_filter(text):
    """Convert markdown text to HTML."""
    if not text:
        return ""
    return Markup(markdown.markdown(text, extensions=["nl2br", "fenced_code"]))


DB_PATH = "training.db"


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    """Home page."""
    return render_template("index.html")


@app.route("/log-lifting", methods=["GET", "POST"])
def log_lifting():
    """Log a lifting session."""
    if request.method == "POST":
        # Get session data
        date = request.form.get("date")
        name = request.form.get("name")
        session_notes = request.form.get("session_notes", "").strip()

        # Validate required fields
        if not date or not name:
            flash("Date and session name are required", "danger")
            return redirect(url_for("log_lifting"))

        # Get exercises data (multiple exercises)
        exercise_names = request.form.getlist("exercise_name[]")
        weights = request.form.getlist("weight[]")
        reps_inputs = request.form.getlist("reps[]")
        rest_times = request.form.getlist("rest_seconds[]")
        exercise_notes = request.form.getlist("exercise_notes[]")

        # Validate at least one exercise
        if not exercise_names or not any(exercise_names):
            flash("At least one exercise is required", "danger")
            return redirect(url_for("log_lifting"))

        # Insert into database
        conn = get_db()
        cursor = conn.cursor()

        try:
            # Insert session
            cursor.execute(
                """
                INSERT INTO lifting_sessions (date, name, notes)
                VALUES (?, ?, ?)
            """,
                (date, name, session_notes if session_notes else None),
            )

            session_id = cursor.lastrowid

            # Insert exercises
            exercises_added = 0
            for i, exercise_name in enumerate(exercise_names):
                if not exercise_name.strip():
                    continue

                # Parse reps (comma-separated or space-separated)
                reps_str = reps_inputs[i].strip()
                reps_list = [
                    int(r.strip())
                    for r in reps_str.replace(",", " ").split()
                    if r.strip().isdigit()
                ]

                if not reps_list:
                    continue

                # Convert reps to JSON
                reps_json = json.dumps(reps_list)

                # Get weight (can be empty for bodyweight exercises)
                weight = float(weights[i]) if weights[i].strip() else None

                # Get rest time (can be empty)
                rest = int(rest_times[i]) if rest_times[i].strip() else None

                # Get notes (can be empty)
                notes = exercise_notes[i].strip() if exercise_notes[i].strip() else None

                cursor.execute(
                    """
                    INSERT INTO lifting_exercises
                    (session_id, exercise_name, weight, reps_per_set, rest_seconds, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (session_id, exercise_name.strip(), weight, reps_json, rest, notes),
                )

                exercises_added += 1

            conn.commit()
            flash(
                f"Lifting session logged successfully! ({exercises_added} exercises)",
                "success",
            )
            return redirect(url_for("view_lifting"))

        except Exception as e:
            conn.rollback()
            flash(f"Error logging session: {str(e)}", "danger")
            return redirect(url_for("log_lifting"))

        finally:
            conn.close()

    # GET request - show form
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("log_lifting.html", today=today)


@app.route("/view-lifting")
def view_lifting():
    """View recent lifting sessions with full exercise details."""
    conn = get_db()
    cursor = conn.cursor()

    # Get recent sessions
    cursor.execute("""
        SELECT id, date, name, notes
        FROM lifting_sessions
        ORDER BY date DESC
        LIMIT 20
    """)

    sessions_raw = cursor.fetchall()

    # Build sessions with exercises
    sessions = []
    for session in sessions_raw:
        # Get exercises for this session
        cursor.execute(
            """
            SELECT exercise_name, weight, reps_per_set, rest_seconds, notes
            FROM lifting_exercises
            WHERE session_id = ?
            ORDER BY id
        """,
            (session["id"],),
        )

        exercises = cursor.fetchall()

        # Parse reps JSON for each exercise
        exercises_data = []
        for exercise in exercises:
            reps_list = json.loads(exercise["reps_per_set"])
            exercises_data.append(
                {
                    "exercise_name": exercise["exercise_name"],
                    "weight": exercise["weight"],
                    "reps_per_set": exercise["reps_per_set"],  # Keep JSON for template
                    "reps_list": reps_list,  # Parsed list
                    "reps_display": ", ".join(map(str, reps_list)),  # Display string
                    "num_sets": len(reps_list),
                    "rest_seconds": exercise["rest_seconds"],
                    "notes": exercise["notes"] or "",
                }
            )

        sessions.append(
            {
                "id": session["id"],
                "date": session["date"],
                "name": session["name"],
                "notes": session["notes"],
                "exercises": exercises_data,
                "exercise_count": len(exercises_data),
            }
        )

    conn.close()

    return render_template("view_lifting.html", sessions=sessions)


@app.route("/view-lifting/<int:session_id>")
def view_lifting_detail(session_id):
    """View detailed lifting session."""
    conn = get_db()
    cursor = conn.cursor()

    # Get session
    cursor.execute("SELECT * FROM lifting_sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()

    if not session:
        flash("Session not found", "danger")
        return redirect(url_for("view_lifting"))

    # Get exercises
    cursor.execute(
        """
        SELECT * FROM lifting_exercises
        WHERE session_id = ?
        ORDER BY id
    """,
        (session_id,),
    )

    exercises = cursor.fetchall()
    conn.close()

    return render_template(
        "view_lifting_detail.html", session=session, exercises=exercises
    )


@app.route("/edit-lifting/<int:session_id>", methods=["GET", "POST"])
def edit_lifting(session_id):
    """Edit a lifting session."""
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        # Get session data
        date = request.form.get("date")
        name = request.form.get("name")
        session_notes = request.form.get("session_notes", "").strip()

        # Validate required fields
        if not date or not name:
            flash("Date and session name are required", "danger")
            return redirect(url_for("edit_lifting", session_id=session_id))

        # Get exercises data (multiple exercises)
        exercise_names = request.form.getlist("exercise_name[]")
        weights = request.form.getlist("weight[]")
        reps_inputs = request.form.getlist("reps[]")
        rest_times = request.form.getlist("rest_seconds[]")
        exercise_notes = request.form.getlist("exercise_notes[]")

        # Validate at least one exercise
        if not exercise_names or not any(exercise_names):
            flash("At least one exercise is required", "danger")
            return redirect(url_for("edit_lifting", session_id=session_id))

        try:
            # Update session
            cursor.execute(
                """
                UPDATE lifting_sessions
                SET date = ?, name = ?, notes = ?
                WHERE id = ?
            """,
                (date, name, session_notes if session_notes else None, session_id),
            )

            # Delete existing exercises
            cursor.execute(
                "DELETE FROM lifting_exercises WHERE session_id = ?", (session_id,)
            )

            # Insert updated exercises
            exercises_added = 0
            for i, exercise_name in enumerate(exercise_names):
                if not exercise_name.strip():
                    continue

                # Parse reps (comma-separated or space-separated)
                reps_str = reps_inputs[i].strip()
                reps_list = [
                    int(r.strip())
                    for r in reps_str.replace(",", " ").split()
                    if r.strip().isdigit()
                ]

                if not reps_list:
                    continue

                # Convert reps to JSON
                reps_json = json.dumps(reps_list)

                # Get weight (can be empty for bodyweight exercises)
                weight = float(weights[i]) if weights[i].strip() else None

                # Get rest time (can be empty)
                rest = int(rest_times[i]) if rest_times[i].strip() else None

                # Get notes (can be empty)
                notes = exercise_notes[i].strip() if exercise_notes[i].strip() else None

                cursor.execute(
                    """
                    INSERT INTO lifting_exercises
                    (session_id, exercise_name, weight, reps_per_set, rest_seconds, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (session_id, exercise_name.strip(), weight, reps_json, rest, notes),
                )

                exercises_added += 1

            conn.commit()
            flash(
                f"Session updated successfully! ({exercises_added} exercises)",
                "success",
            )
            return redirect(url_for("view_lifting_detail", session_id=session_id))

        except Exception as e:
            conn.rollback()
            flash(f"Error updating session: {str(e)}", "danger")
            return redirect(url_for("edit_lifting", session_id=session_id))

        finally:
            conn.close()

    # GET request - load existing data
    cursor.execute("SELECT * FROM lifting_sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()

    if not session:
        flash("Session not found", "danger")
        conn.close()
        return redirect(url_for("view_lifting"))

    # Get exercises
    cursor.execute(
        """
        SELECT * FROM lifting_exercises
        WHERE session_id = ?
        ORDER BY id
    """,
        (session_id,),
    )

    exercises = cursor.fetchall()
    conn.close()

    # Parse reps JSON for each exercise
    exercises_data = []
    for exercise in exercises:
        reps_list = json.loads(exercise["reps_per_set"])
        reps_str = ", ".join(map(str, reps_list))
        exercises_data.append(
            {
                "exercise_name": exercise["exercise_name"],
                "weight": exercise["weight"] or "",
                "reps": reps_str,
                "rest_seconds": exercise["rest_seconds"] or "",
                "notes": exercise["notes"] or "",
            }
        )

    return render_template(
        "edit_lifting.html", session=session, exercises=exercises_data
    )


@app.route("/running-stats")
def running_stats():
    """View running statistics by week."""
    # Get number of weeks to show (default 6, can load more)
    weeks_to_show = int(request.args.get("weeks", 6))

    conn = get_db()
    cursor = conn.cursor()

    # Get all running activities (Run + TrailRun)
    cursor.execute("""
        SELECT date, distance, total_elevation_gain
        FROM activities
        WHERE sport_type IN ('Run', 'TrailRun')
        ORDER BY date DESC
    """)

    activities = cursor.fetchall()
    conn.close()

    # Group activities by week (Monday-Sunday)
    weekly_data = defaultdict(
        lambda: {
            "days": defaultdict(lambda: {"distance": 0, "count": 0}),
            "total_distance": 0,
            "total_elevation": 0,
            "start_date": None,
            "end_date": None,
        }
    )

    for activity in activities:
        date_str = activity["date"]
        distance = activity["distance"]
        elevation = activity["total_elevation_gain"] or 0

        # Parse date
        date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        # Get Monday of that week
        days_since_monday = date_obj.weekday()
        monday = date_obj - timedelta(days=days_since_monday)
        week_key = monday.strftime("%Y-%m-%d")

        # Day of week (0=Monday, 6=Sunday)
        day_of_week = date_obj.weekday()

        # Aggregate data
        weekly_data[week_key]["days"][day_of_week]["distance"] += distance
        weekly_data[week_key]["days"][day_of_week]["count"] += 1
        weekly_data[week_key]["total_distance"] += distance
        weekly_data[week_key]["total_elevation"] += elevation

        # Set date range
        if weekly_data[week_key]["start_date"] is None:
            weekly_data[week_key]["start_date"] = monday
            weekly_data[week_key]["end_date"] = monday + timedelta(days=6)

    # Sort weeks by date (most recent first) and limit
    sorted_weeks = sorted(weekly_data.items(), key=lambda x: x[0], reverse=True)[
        :weeks_to_show
    ]

    # Convert to list of week objects
    weeks = []
    for week_key, data in sorted_weeks:
        # Create array of 7 days (Monday-Sunday)
        days = []
        for day_num in range(7):
            day_data = data["days"].get(day_num, {"distance": 0, "count": 0})
            days.append(
                {
                    "distance_km": day_data["distance"] / 1000,
                    "distance_miles": day_data["distance"] / 1000 * 0.621371,
                    "count": day_data["count"],
                }
            )

        weeks.append(
            {
                "start_date": data["start_date"].strftime("%Y-%m-%d"),
                "end_date": data["end_date"].strftime("%Y-%m-%d"),
                "start_date_display": data["start_date"].strftime("%b %d"),
                "end_date_display": data["end_date"].strftime("%b %d, %Y"),
                "total_distance_km": data["total_distance"] / 1000,
                "total_distance_miles": data["total_distance"] / 1000 * 0.621371,
                "total_elevation_m": data["total_elevation"],
                "total_elevation_ft": data["total_elevation"] * 3.28084,
                "days": days,
            }
        )

    # Check if there are more weeks to load
    total_weeks_available = len(weekly_data)
    has_more = weeks_to_show < total_weeks_available

    return render_template(
        "running_stats.html", weeks=weeks, weeks_shown=weeks_to_show, has_more=has_more
    )


@app.route("/plan")
def weekly_plan():
    """View weekly plan - redirects to current week."""
    # Get current Monday
    today = datetime.now()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    week_start = monday.strftime("%Y-%m-%d")

    return redirect(url_for("weekly_plan_detail", week_start_date=week_start))


@app.route("/plan/week/<week_start_date>")
def weekly_plan_detail(week_start_date):
    """View detailed weekly plan for a specific week."""
    conn = get_db()
    cursor = conn.cursor()

    # Parse the week start date
    try:
        week_start = datetime.strptime(week_start_date, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format", "danger")
        return redirect(url_for("weekly_plan"))

    # Get the weekly plan
    cursor.execute(
        """
        SELECT id, week_start_date, week_number, total_weeks, objective, description
        FROM weekly_plans
        WHERE week_start_date = ?
    """,
        (week_start_date,),
    )

    weekly_plan = cursor.fetchone()

    # Get planned runs for the week
    if weekly_plan:
        cursor.execute(
            """
            SELECT id, date, distance, type, description, priority
            FROM planned_runs
            WHERE weekly_plan_id = ?
            ORDER BY date
        """,
            (weekly_plan["id"],),
        )
        planned_runs = {row["date"]: dict(row) for row in cursor.fetchall()}

        # Get planned lifting sessions
        cursor.execute(
            """
            SELECT id, date, name, description, priority
            FROM planned_lifting_sessions
            WHERE weekly_plan_id = ?
            ORDER BY date
        """,
            (weekly_plan["id"],),
        )
        planned_lifting = {row["date"]: dict(row) for row in cursor.fetchall()}
    else:
        planned_runs = {}
        planned_lifting = {}

    # Get actual activities for the week
    week_end = week_start + timedelta(days=6)
    cursor.execute(
        """
        SELECT date, distance, total_elevation_gain
        FROM activities
        WHERE sport_type IN ('Run', 'TrailRun')
        AND date >= ?
        AND date < ?
        ORDER BY date
    """,
        (week_start_date, (week_end + timedelta(days=1)).strftime("%Y-%m-%d")),
    )

    actual_activities = cursor.fetchall()
    conn.close()

    # Build day-by-day data
    today = datetime.now().date()
    days = []
    for day_num in range(7):
        day_date = week_start + timedelta(days=day_num)
        day_date_str = day_date.strftime("%Y-%m-%d")
        day_date_obj = day_date.date()
        is_past = day_date_obj < today

        # Get actual runs for this day
        day_activities = [
            a
            for a in actual_activities
            if datetime.fromisoformat(a["date"].replace("Z", "+00:00")).date()
            == day_date_obj
        ]

        # Calculate total distance for actual runs
        actual_distance_m = sum(a["distance"] for a in day_activities)
        actual_distance_km = actual_distance_m / 1000
        actual_distance_miles = actual_distance_km * 0.621371

        # Get planned run
        planned_run = planned_runs.get(day_date_str)

        # Get planned lifting
        planned_lift = planned_lifting.get(day_date_str)

        # Determine what to show for running
        if is_past and actual_distance_m > 0:
            # Show actual run for past days
            run_data = {
                "type": "actual",
                "distance_km": actual_distance_km,
                "distance_miles": actual_distance_miles,
                "count": len(day_activities),
            }
        elif planned_run:
            # Show planned run for current/future days
            run_data = {
                "type": "planned",
                "distance_km": planned_run["distance"],
                "distance_miles": planned_run["distance"] * 0.621371
                if planned_run["distance"]
                else None,
                "run_type": planned_run["type"],
                "description": planned_run["description"],
                "id": planned_run["id"],
            }
        else:
            run_data = None

        days.append(
            {
                "date": day_date_str,
                "date_display": day_date.strftime("%b %d"),
                "day_name": day_date.strftime("%a"),
                "is_past": is_past,
                "run": run_data,
                "lifting": planned_lift,
            }
        )

    # Calculate next/prev week dates
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    # Check if we should allow going back (not into the past relative to today)
    today_monday = datetime.now().date()
    days_since_monday = today_monday.weekday()
    current_monday = today_monday - timedelta(days=days_since_monday)
    can_go_prev = prev_week.date() >= current_monday

    return render_template(
        "weekly_plan.html",
        weekly_plan=weekly_plan,
        days=days,
        week_start_date=week_start_date,
        week_start_display=week_start.strftime("%b %d"),
        week_end_display=(week_start + timedelta(days=6)).strftime("%b %d"),
        prev_week_date=prev_week.strftime("%Y-%m-%d"),
        next_week_date=next_week.strftime("%Y-%m-%d"),
        can_go_prev=can_go_prev,
    )


@app.route("/plan/running/<int:weekly_plan_id>")
def weekly_running_plan(weekly_plan_id):
    """View detailed running plan for a specific week."""
    conn = get_db()
    cursor = conn.cursor()

    # Get the weekly plan
    cursor.execute(
        """
        SELECT id, week_start_date, week_number, total_weeks, objective, description
        FROM weekly_plans
        WHERE id = ?
    """,
        (weekly_plan_id,),
    )

    weekly_plan = cursor.fetchone()

    if not weekly_plan:
        flash("Weekly plan not found", "danger")
        return redirect(url_for("weekly_plan"))

    # Get planned runs
    cursor.execute(
        """
        SELECT id, date, distance, type, description, priority
        FROM planned_runs
        WHERE weekly_plan_id = ?
        ORDER BY date
    """,
        (weekly_plan_id,),
    )

    planned_runs = cursor.fetchall()

    # Get actual runs for comparison
    week_start = datetime.strptime(weekly_plan["week_start_date"], "%Y-%m-%d")
    week_end = week_start + timedelta(days=6)

    cursor.execute(
        """
        SELECT date, distance, total_elevation_gain, moving_time
        FROM activities
        WHERE sport_type IN ('Run', 'TrailRun')
        AND date >= ?
        AND date < ?
        ORDER BY date
    """,
        (
            weekly_plan["week_start_date"],
            (week_end + timedelta(days=1)).strftime("%Y-%m-%d"),
        ),
    )

    actual_runs = cursor.fetchall()
    conn.close()

    # Build comparison data
    runs = []
    for planned in planned_runs:
        planned_date = datetime.strptime(planned["date"], "%Y-%m-%d").date()

        # Find matching actual runs
        matching_actuals = [
            a
            for a in actual_runs
            if datetime.fromisoformat(a["date"].replace("Z", "+00:00")).date()
            == planned_date
        ]

        # Calculate totals for actual runs
        if matching_actuals:
            actual_distance_m = sum(a["distance"] for a in matching_actuals)
            actual_distance_km = actual_distance_m / 1000
            actual_elevation_m = sum(
                a["total_elevation_gain"] or 0 for a in matching_actuals
            )
            actual_time_min = sum(a["moving_time"] for a in matching_actuals) / 60
        else:
            actual_distance_km = None
            actual_elevation_m = None
            actual_time_min = None

        runs.append(
            {
                "date": planned["date"],
                "date_display": datetime.strptime(planned["date"], "%Y-%m-%d").strftime(
                    "%a, %b %d"
                ),
                "planned_distance_km": planned["distance"],
                "planned_distance_miles": planned["distance"] * 0.621371
                if planned["distance"]
                else None,
                "planned_type": planned["type"],
                "planned_description": planned["description"],
                "priority": planned["priority"],
                "actual_distance_km": actual_distance_km,
                "actual_distance_miles": actual_distance_km * 0.621371
                if actual_distance_km
                else None,
                "actual_elevation_m": actual_elevation_m,
                "actual_elevation_ft": actual_elevation_m * 3.28084
                if actual_elevation_m
                else None,
                "actual_time_min": actual_time_min,
                "has_actual": actual_distance_km is not None,
            }
        )

    return render_template(
        "weekly_running_plan.html",
        weekly_plan=weekly_plan,
        runs=runs,
        week_start_display=week_start.strftime("%b %d"),
        week_end_display=week_end.strftime("%b %d, %Y"),
    )


@app.route("/plan/lifting/<int:planned_session_id>")
def planned_lifting_detail(planned_session_id):
    """View detailed planned lifting session."""
    conn = get_db()
    cursor = conn.cursor()

    # Get the planned session
    cursor.execute(
        """
        SELECT pls.id, pls.date, pls.name, pls.description, pls.priority,
               wp.week_start_date
        FROM planned_lifting_sessions pls
        JOIN weekly_plans wp ON pls.weekly_plan_id = wp.id
        WHERE pls.id = ?
    """,
        (planned_session_id,),
    )

    session = cursor.fetchone()

    if not session:
        flash("Planned lifting session not found", "danger")
        return redirect(url_for("weekly_plan"))

    # Get planned exercises
    cursor.execute(
        """
        SELECT exercise_name, target_weight, reps_per_set, rest_seconds, notes
        FROM planned_lifting_exercises
        WHERE planned_session_id = ?
        ORDER BY id
    """,
        (planned_session_id,),
    )

    exercises = cursor.fetchall()
    conn.close()

    # Parse reps for each exercise
    exercises_data = []
    for exercise in exercises:
        reps_list = json.loads(exercise["reps_per_set"])
        exercises_data.append(
            {
                "exercise_name": exercise["exercise_name"],
                "target_weight": exercise["target_weight"],
                "reps_list": reps_list,
                "reps_display": " × ".join(map(str, reps_list)),
                "num_sets": len(reps_list),
                "rest_seconds": exercise["rest_seconds"],
                "rest_display": f"{exercise['rest_seconds'] // 60}:{exercise['rest_seconds'] % 60:02d}"
                if exercise["rest_seconds"]
                else None,
                "notes": exercise["notes"],
            }
        )

    return render_template(
        "planned_lifting_detail.html",
        session=session,
        exercises=exercises_data,
        week_start_date=session["week_start_date"],
    )


@app.route("/api/search-exercises")
def search_exercises():
    """Search exercises by name with fuzzy matching."""
    query = request.args.get("q", "").strip().lower()

    if not query:
        return {"exercises": []}

    conn = get_db()
    cursor = conn.cursor()

    # Get all exercises with session dates
    cursor.execute("""
        SELECT
            le.exercise_name,
            le.weight,
            le.reps_per_set,
            le.rest_seconds,
            le.notes,
            ls.date as session_date,
            ls.name as session_name
        FROM lifting_exercises le
        JOIN lifting_sessions ls ON le.session_id = ls.id
        ORDER BY ls.date DESC
    """)

    all_exercises = cursor.fetchall()
    conn.close()

    # Fuzzy search: match exercises where query appears anywhere in the name
    matching_exercises = []
    for exercise in all_exercises:
        exercise_name_lower = exercise["exercise_name"].lower()

        # Simple fuzzy matching: check if query is substring of exercise name
        if query in exercise_name_lower:
            reps_list = json.loads(exercise["reps_per_set"])

            matching_exercises.append(
                {
                    "exercise_name": exercise["exercise_name"],
                    "session_date": exercise["session_date"],
                    "session_name": exercise["session_name"],
                    "weight": exercise["weight"],
                    "reps_display": ", ".join(map(str, reps_list)),
                    "num_sets": len(reps_list),
                    "rest_seconds": exercise["rest_seconds"],
                    "notes": exercise["notes"] or "",
                }
            )

    return {"exercises": matching_exercises}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
