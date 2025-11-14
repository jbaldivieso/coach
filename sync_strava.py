#!/usr/bin/env python3
"""
Sync Strava activities to local SQLite database.
Supports incremental syncing to avoid API rate limits.
"""

import sqlite3
import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "training.db"


def init_database():
    """Initialize the database with the schema."""
    print("Initializing database...")

    conn = sqlite3.connect(DB_PATH)

    # Read and execute schema
    with open("schema.sql", "r") as f:
        schema = f.read()

    conn.executescript(schema)

    # Add metadata table for tracking sync state
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    print(f"✓ Database initialized: {DB_PATH}")


def get_last_sync_time(conn):
    """Get the last successful sync timestamp."""
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM sync_metadata WHERE key = 'last_sync_time'")
    result = cursor.fetchone()

    if result:
        return int(result[0])
    return None


def update_sync_time(conn, timestamp):
    """Update the last sync timestamp."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
        VALUES ('last_sync_time', ?, CURRENT_TIMESTAMP)
    """,
        (str(timestamp),),
    )
    conn.commit()


def refresh_access_token():
    """Refresh the access token using the refresh token."""
    CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
    CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
    )

    if response.status_code != 200:
        print(f"Error refreshing token: {response.status_code}")
        return None

    token_data = response.json()

    # Update .env file
    with open(".env", "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("STRAVA_ACCESS_TOKEN="):
            new_lines.append(f"STRAVA_ACCESS_TOKEN={token_data['access_token']}\n")
        else:
            new_lines.append(line)

    with open(".env", "w") as f:
        f.writelines(new_lines)

    return token_data["access_token"]


def get_access_token():
    """Get valid access token, refreshing if necessary."""
    access_token = os.getenv("STRAVA_ACCESS_TOKEN")

    # Test if token works
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)

    if response.status_code == 401:
        print("Access token expired, refreshing...")
        access_token = refresh_access_token()

    return access_token


def get_activities_since(access_token, after_timestamp, per_page=200):
    """
    Fetch activities from Strava since a given timestamp.

    Args:
        access_token: Strava API access token
        after_timestamp: Unix timestamp (activities after this time)
        per_page: Number of activities per page
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    all_activities = []
    page = 1

    after_date = datetime.fromtimestamp(after_timestamp).strftime("%Y-%m-%d")
    print(f"Fetching activities since {after_date}...")

    while True:
        params = {"per_page": per_page, "page": page, "after": after_timestamp}

        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers=headers,
            params=params,
        )

        if response.status_code != 200:
            print(f"Error fetching activities: {response.status_code}")
            break

        activities = response.json()

        if not activities:
            break

        all_activities.extend(activities)
        print(f"  Fetched page {page} ({len(activities)} activities)")

        if len(activities) < per_page:
            break

        page += 1

    print(f"✓ Total activities fetched: {len(all_activities)}")
    return all_activities


def get_activity_detail(access_token, activity_id):
    """Fetch detailed data for a specific activity (includes splits)."""
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(
        f"https://www.strava.com/api/v3/activities/{activity_id}", headers=headers
    )

    if response.status_code != 200:
        return None

    return response.json()


def insert_activity(conn, activity_data):
    """Insert or update an activity in the database."""
    cursor = conn.cursor()

    # Check if activity already exists
    cursor.execute(
        "SELECT id FROM activities WHERE strava_id = ?", (activity_data["id"],)
    )
    existing = cursor.fetchone()

    if existing:
        # Skip if already exists (or update if you want)
        return existing[0], False

    # Insert new activity
    cursor.execute(
        """
        INSERT INTO activities (
            strava_id, name, date, sport_type, workout_type,
            distance, moving_time, elapsed_time,
            total_elevation_gain, elev_high, elev_low,
            average_speed, max_speed,
            has_heartrate, average_heartrate, max_heartrate,
            suffer_score, calories, perceived_exertion,
            device_name, trainer, commute,
            description, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            activity_data["id"],
            activity_data["name"],
            activity_data["start_date_local"],
            activity_data.get("sport_type") or activity_data.get("type"),
            activity_data.get("workout_type"),
            activity_data["distance"],
            activity_data["moving_time"],
            activity_data["elapsed_time"],
            activity_data.get("total_elevation_gain"),
            activity_data.get("elev_high"),
            activity_data.get("elev_low"),
            activity_data.get("average_speed"),
            activity_data.get("max_speed"),
            activity_data.get("has_heartrate", False),
            activity_data.get("average_heartrate"),
            activity_data.get("max_heartrate"),
            activity_data.get("suffer_score"),
            activity_data.get("calories"),
            activity_data.get("perceived_exertion"),
            activity_data.get("device_name"),
            activity_data.get("trainer", False),
            activity_data.get("commute", False),
            activity_data.get("description"),
            None,  # notes - for manual entry later
        ),
    )

    conn.commit()
    return cursor.lastrowid, True


def insert_splits(conn, activity_db_id, splits, split_type):
    """Insert splits for an activity."""
    if not splits:
        return 0

    cursor = conn.cursor()
    inserted = 0

    for split_data in splits:
        cursor.execute(
            """
            INSERT INTO activity_splits (
                activity_id, split_number, split_type,
                distance, elapsed_time, moving_time, elevation_difference,
                average_speed, average_grade_adjusted_speed,
                average_heartrate, pace_zone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                activity_db_id,
                split_data["split"],
                split_type,
                split_data["distance"],
                split_data["elapsed_time"],
                split_data["moving_time"],
                split_data.get("elevation_difference"),
                split_data.get("average_speed"),
                split_data.get("average_grade_adjusted_speed"),
                split_data.get("average_heartrate"),
                split_data.get("pace_zone"),
            ),
        )
        inserted += 1

    conn.commit()
    return inserted


def sync_activities(access_token, conn, after_timestamp=None, fetch_splits=True):
    """
    Sync activities from Strava to local database.

    Args:
        access_token: Strava API token
        conn: Database connection
        after_timestamp: Only fetch activities after this time (unix timestamp)
        fetch_splits: Whether to fetch detailed split data for runs
    """
    # If no after_timestamp provided, default to Jan 1, 2025
    if after_timestamp is None:
        # Current year start
        current_year = datetime.now().year
        after_timestamp = int(
            datetime(current_year, 1, 1, tzinfo=timezone.utc).timestamp()
        )

    # Get activities
    activities = get_activities_since(access_token, after_timestamp)

    if not activities:
        print("No new activities to sync")
        return

    print(f"\nSyncing {len(activities)} activities to database...")

    new_count = 0
    splits_count = 0
    sync_start_time = int(datetime.now(timezone.utc).timestamp())

    for i, activity in enumerate(activities, 1):
        # Insert activity
        activity_db_id, is_new = insert_activity(conn, activity)

        if is_new:
            new_count += 1

            # Fetch detailed data for splits (only for running activities)
            if fetch_splits and "run" in activity.get("sport_type", "").lower():
                detail = get_activity_detail(access_token, activity["id"])

                if detail:
                    # Insert metric splits (per km)
                    if "splits_metric" in detail and detail["splits_metric"]:
                        count = insert_splits(
                            conn, activity_db_id, detail["splits_metric"], "metric"
                        )
                        splits_count += count

        # Progress indicator
        if i % 10 == 0:
            print(f"  Processed {i}/{len(activities)} activities...")

    # Update last sync time
    update_sync_time(conn, sync_start_time)

    print("✓ Sync complete!")
    print(f"  New activities: {new_count}")
    print(f"  Total splits: {splits_count}")


def show_stats(conn):
    """Show some basic stats from the database."""
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("DATABASE STATS")
    print("=" * 80)

    # Last sync time
    last_sync = get_last_sync_time(conn)
    if last_sync:
        last_sync_date = datetime.fromtimestamp(last_sync).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\nLast sync: {last_sync_date}")

    # Total activities
    cursor.execute("SELECT COUNT(*) FROM activities")
    total = cursor.fetchone()[0]
    print(f"Total activities: {total}")

    # By sport type
    cursor.execute("""
        SELECT sport_type, COUNT(*),
               SUM(distance)/1000.0 as total_km,
               SUM(total_elevation_gain) as total_elev
        FROM activities
        GROUP BY sport_type
        ORDER BY COUNT(*) DESC
    """)

    print("\nBy sport type:")
    for row in cursor.fetchall():
        sport, count, km, elev = row
        print(f"  {sport}: {count} activities, {km:.1f} km, {elev:.0f}m elevation")

    # Recent activities
    cursor.execute("""
        SELECT date, name, distance/1000.0 as km, total_elevation_gain
        FROM activities
        ORDER BY date DESC
        LIMIT 5
    """)

    print("\nMost recent activities:")
    for row in cursor.fetchall():
        date, name, km, elev = row
        date_obj = datetime.fromisoformat(date.replace("Z", "+00:00"))
        print(f"  {date_obj.strftime('%Y-%m-%d')}: {name} ({km:.1f} km, {elev:.0f}m)")

    # Total splits
    cursor.execute("SELECT COUNT(*) FROM activity_splits")
    total_splits = cursor.fetchone()[0]
    print(f"\nTotal splits: {total_splits}")

    print("=" * 80 + "\n")


def main():
    import sys

    # Check if database exists
    db_exists = os.path.exists(DB_PATH)

    if not db_exists:
        print(f"Database does not exist. Creating {DB_PATH}...")
        init_database()

    # Open database connection
    conn = sqlite3.connect(DB_PATH)

    # Get access token
    access_token = get_access_token()

    if not access_token:
        print("Error: Could not get valid access token")
        conn.close()
        return

    # Determine sync mode
    last_sync = get_last_sync_time(conn)
    fetch_splits = "--no-splits" not in sys.argv

    if last_sync:
        print(
            f"Incremental sync mode (last sync: {datetime.fromtimestamp(last_sync).strftime('%Y-%m-%d %H:%M')})"
        )
        sync_activities(
            access_token, conn, after_timestamp=last_sync, fetch_splits=fetch_splits
        )
    else:
        print(
            f"Initial sync mode (fetching activities from {datetime.now().year}-01-01)"
        )
        sync_activities(
            access_token, conn, after_timestamp=None, fetch_splits=fetch_splits
        )

    # Show stats
    show_stats(conn)

    conn.close()


if __name__ == "__main__":
    main()
