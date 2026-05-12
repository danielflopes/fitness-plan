#!/usr/bin/env python3
"""
Fetch recent activities from the Strava API.

Uses OAuth 2.0 with a refresh token to get an access token, then pulls
activities for the specified period. Outputs JSON to stdout.

Setup:
    1. Create a Strava API app at https://www.strava.com/settings/api
    2. Get initial tokens via OAuth flow (authorize URL + token exchange)
    3. Set env vars:
        STRAVA_CLIENT_ID=your_client_id
        STRAVA_CLIENT_SECRET=your_client_secret
        STRAVA_REFRESH_TOKEN=your_refresh_token

Usage:
    python3 fitness-plan/fetch_strava.py --days 30
    python3 fitness-plan/fetch_strava.py --days 30 --detail    # include splits/streams
    python3 fitness-plan/fetch_strava.py --days 7 --type Run
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip3 install requests")

try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


# ── Config ────────────────────────────────────────────────────────────

TOKEN_URL = "https://www.strava.com/oauth/token"
API_BASE = "https://www.strava.com/api/v3"

SPORT_TYPES = {
    "Run", "WeightTraining", "Ride", "Walk", "Hike",
    "Workout", "Yoga", "VirtualRide", "TrailRun",
}


# ── Auth ──────────────────────────────────────────────────────────────

def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Exchange refresh token for a fresh access token."""
    resp = requests.post(TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Print new refresh token if it rotated (Strava rotates tokens)
    new_refresh = data.get("refresh_token")
    if new_refresh and new_refresh != refresh_token:
        print(
            f"⚠️  Strava rotated your refresh token. Update STRAVA_REFRESH_TOKEN:\n"
            f"   {new_refresh}",
            file=sys.stderr,
        )

    return data["access_token"]


# ── Fetch ─────────────────────────────────────────────────────────────

def fetch_activities(
    access_token: str,
    after_epoch: int,
    sport_type: str | None = None,
    page_size: int = 50,
) -> list[dict]:
    """Fetch all activities after a given epoch timestamp."""
    headers = {"Authorization": f"Bearer {access_token}"}
    activities = []
    page = 1

    while True:
        params = {"after": after_epoch, "per_page": page_size, "page": page}
        resp = requests.get(
            f"{API_BASE}/athlete/activities",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        activities.extend(batch)
        if len(batch) < page_size:
            break
        page += 1

    # Filter by sport type if requested
    if sport_type:
        activities = [a for a in activities if a.get("sport_type") == sport_type]

    return activities


def fetch_activity_detail(access_token: str, activity_id: int) -> dict:
    """Fetch detailed activity data including splits and laps."""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(
        f"{API_BASE}/activities/{activity_id}",
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_activity_zones(access_token: str, activity_id: int) -> list[dict]:
    """Fetch HR zone distribution for an activity."""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(
        f"{API_BASE}/activities/{activity_id}/zones",
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# ── Formatting ────────────────────────────────────────────────────────

def format_activity_summary(activity: dict) -> dict:
    """Extract the fields the trainer agent cares about."""
    sport = activity.get("sport_type", activity.get("type", "Unknown"))
    summary = {
        "id": activity["id"],
        "name": activity.get("name", ""),
        "sport_type": sport,
        "date": activity.get("start_date_local", "")[:10],
        "start_time": activity.get("start_date_local", "")[11:16],
        "duration_min": round(activity.get("moving_time", 0) / 60, 1),
        "distance_km": round(activity.get("distance", 0) / 1000, 2),
    }

    # HR data (if available)
    if activity.get("average_heartrate"):
        summary["avg_hr"] = round(activity["average_heartrate"])
        summary["max_hr"] = round(activity.get("max_heartrate", 0))

    # Pace for runs (min/km)
    if sport in ("Run", "TrailRun") and activity.get("distance", 0) > 0:
        pace_s_per_km = activity.get("moving_time", 0) / (activity["distance"] / 1000)
        mins = int(pace_s_per_km // 60)
        secs = int(pace_s_per_km % 60)
        summary["pace_min_km"] = f"{mins}:{secs:02d}"

    # Elevation
    if activity.get("total_elevation_gain"):
        summary["elevation_m"] = round(activity["total_elevation_gain"])

    # Calories
    if activity.get("calories"):
        summary["calories"] = round(activity["calories"])

    # Suffer score
    if activity.get("suffer_score"):
        summary["suffer_score"] = activity["suffer_score"]

    return summary


def format_activity_detail(detail: dict) -> dict:
    """Format detailed activity with splits."""
    summary = format_activity_summary(detail)

    # Splits (for runs)
    if detail.get("splits_metric"):
        summary["splits_km"] = []
        for split in detail["splits_metric"]:
            s = {
                "km": split.get("split", 0),
                "time_s": split.get("moving_time", 0),
                "elevation_diff": split.get("elevation_difference", 0),
            }
            if split.get("average_heartrate"):
                s["avg_hr"] = round(split["average_heartrate"])
            if split.get("distance", 0) > 0:
                pace = split["moving_time"] / (split["distance"] / 1000)
                mins = int(pace // 60)
                secs = int(pace % 60)
                s["pace"] = f"{mins}:{secs:02d}"
            summary["splits_km"].append(s)

    # Laps
    if detail.get("laps"):
        summary["laps"] = len(detail["laps"])

    return summary


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch Strava activities")
    parser.add_argument("--days", type=int, default=30, help="Look back N days (default: 30)")
    parser.add_argument("--type", type=str, default=None, help="Filter by sport type (Run, WeightTraining, Ride, etc.)")
    parser.add_argument("--detail", action="store_true", help="Fetch detailed data with splits for each activity")
    parser.add_argument("--client-id", type=str, default=None)
    parser.add_argument("--client-secret", type=str, default=None)
    parser.add_argument("--refresh-token", type=str, default=None)
    args = parser.parse_args()

    client_id = args.client_id or os.environ.get("STRAVA_CLIENT_ID")
    client_secret = args.client_secret or os.environ.get("STRAVA_CLIENT_SECRET")
    refresh_token = args.refresh_token or os.environ.get("STRAVA_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        sys.exit(
            "Missing Strava credentials. Set env vars:\n"
            "  STRAVA_CLIENT_ID\n"
            "  STRAVA_CLIENT_SECRET\n"
            "  STRAVA_REFRESH_TOKEN\n"
            "Or pass --client-id, --client-secret, --refresh-token"
        )

    # Calculate epoch for --days lookback
    after_dt = datetime.now(timezone.utc) - timedelta(days=args.days)
    after_epoch = int(after_dt.timestamp())

    # Auth
    print(f"🔄 Refreshing Strava access token...", file=sys.stderr)
    access_token = get_access_token(client_id, client_secret, refresh_token)

    # Fetch activities
    print(f"📥 Fetching activities from last {args.days} days...", file=sys.stderr)
    activities = fetch_activities(access_token, after_epoch, sport_type=args.type)
    print(f"   Found {len(activities)} activities", file=sys.stderr)

    # Format
    if args.detail:
        results = []
        for i, act in enumerate(activities):
            print(f"   Fetching detail {i+1}/{len(activities)}: {act.get('name', '')}...", file=sys.stderr)
            detail = fetch_activity_detail(access_token, act["id"])
            results.append(format_activity_detail(detail))
    else:
        results = [format_activity_summary(a) for a in activities]

    # Sort by date descending
    results.sort(key=lambda x: x.get("date", ""), reverse=True)

    # Output
    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "period_days": args.days,
        "sport_type_filter": args.type,
        "count": len(results),
        "activities": results,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
