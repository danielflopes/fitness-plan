#!/usr/bin/env python3
"""
Fetch body composition data from the Withings API.

Uses OAuth 2.0 with a refresh token to get an access token, then pulls
body measurements (weight, body fat %, muscle mass, bone mass, water %)
for the specified period. Outputs JSON to stdout.

Setup:
    1. Create a Withings app at https://developer.withings.com/dashboard/
    2. Get initial tokens via OAuth flow (authorize URL + token exchange)
       Required scope: user.metrics
    3. Set env vars:
        WITHINGS_CLIENT_ID=your_client_id
        WITHINGS_CLIENT_SECRET=your_client_secret
        WITHINGS_REFRESH_TOKEN=your_refresh_token

Usage:
    python3 fitness-plan/fetch_withings.py --days 30
    python3 fitness-plan/fetch_withings.py --days 90
"""

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip3 install requests")

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)
except ImportError:
    pass


def update_env_var(key: str, value: str) -> bool:
    """Rewrite KEY=VALUE in .env atomically. Returns True on success."""
    if not ENV_PATH.exists():
        return False
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    text = ENV_PATH.read_text()
    new_line = f"{key}={value}"
    if pattern.search(text):
        text = pattern.sub(new_line, text)
    else:
        text = text.rstrip("\n") + f"\n{new_line}\n"
    fd, tmp_path = tempfile.mkstemp(dir=ENV_PATH.parent, prefix=".env.")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp_path, ENV_PATH)
        return True
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False


# ── Config ────────────────────────────────────────────────────────────

TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
MEASURE_URL = "https://wbsapi.withings.net/measure"

# Withings measure type IDs
# Spec: https://developer.withings.com/api-reference/#tag/measure
MEASURE_TYPES = {
    1: "weight_kg",
    6: "fat_percent",       # Fat Ratio (%)
    8: "fat_mass_kg",       # Fat Mass Weight (kg)
    76: "muscle_mass_kg",
    77: "hydration_kg",
    88: "bone_mass_kg",
    91: "pulse_wave_velocity",
}

# The types we care about for body comp
WANTED_TYPES = {1, 6, 8, 76, 77, 88}


# ── Auth ──────────────────────────────────────────────────────────────

def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> tuple[str, str]:
    """Exchange refresh token for a fresh access token.

    Returns (access_token, new_refresh_token).
    Withings always rotates the refresh token on each use.
    """
    resp = requests.post(TOKEN_URL, data={
        "action": "requesttoken",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != 0:
        sys.exit(
            f"Withings auth error (status {data.get('status')}): "
            f"{data.get('error', 'unknown')}\n"
            f"You may need to re-authorize. See setup instructions in this script."
        )

    body = data["body"]
    new_refresh = body["refresh_token"]

    if new_refresh != refresh_token:
        if update_env_var("WITHINGS_REFRESH_TOKEN", new_refresh):
            print(
                f"🔁 Withings rotated refresh token — .env updated.",
                file=sys.stderr,
            )
        else:
            print(
                f"⚠️  Withings rotated your refresh token but .env write failed. "
                f"Update WITHINGS_REFRESH_TOKEN manually:\n   {new_refresh}",
                file=sys.stderr,
            )

    return body["access_token"], new_refresh


# ── Fetch ─────────────────────────────────────────────────────────────

def fetch_measures(
    access_token: str,
    start_epoch: int,
    end_epoch: int,
) -> list[dict]:
    """Fetch body measurements from Withings Measure - Getmeas."""
    resp = requests.post(MEASURE_URL, data={
        "action": "getmeas",
        "meastypes": ",".join(str(t) for t in WANTED_TYPES),
        "category": 1,  # Real measurements only (not user objectives)
        "startdate": start_epoch,
        "enddate": end_epoch,
    }, headers={
        "Authorization": f"Bearer {access_token}",
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != 0:
        sys.exit(
            f"Withings API error (status {data.get('status')}): "
            f"{data.get('error', 'unknown')}"
        )

    return data.get("body", {}).get("measuregrps", [])


# ── Formatting ────────────────────────────────────────────────────────

def parse_measure_groups(groups: list[dict]) -> list[dict]:
    """Parse Withings measure groups into clean records.

    Each group is one weigh-in session (one step on the scale).
    A group can contain multiple measure types (weight, BF%, etc.).
    """
    records = []

    for grp in groups:
        ts = grp.get("date", 0)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)

        record = {
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M"),
            "timestamp": ts,
        }

        for measure in grp.get("measures", []):
            mtype = measure.get("type")
            if mtype not in WANTED_TYPES:
                continue

            # Withings stores values as: real_value = value * 10^unit
            value = measure["value"] * (10 ** measure["unit"])
            field = MEASURE_TYPES.get(mtype, f"type_{mtype}")
            record[field] = round(value, 2)

        records.append(record)

    # Sort by date descending
    records.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return records


def compute_trends(records: list[dict]) -> dict:
    """Compute simple trends from the measurement records."""
    if len(records) < 2:
        return {}

    latest = records[0]
    oldest = records[-1]
    trends = {}

    for field in ["weight_kg", "fat_percent", "muscle_mass_kg", "bone_mass_kg"]:
        if field in latest and field in oldest:
            delta = latest[field] - oldest[field]
            direction = "↑" if delta > 0 else "↓" if delta < 0 else "→"
            trends[field] = {
                "latest": latest[field],
                "oldest": oldest[field],
                "delta": round(delta, 2),
                "direction": direction,
            }

    return trends


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch Withings body composition data")
    parser.add_argument("--days", type=int, default=30, help="Look back N days (default: 30)")
    parser.add_argument("--client-id", type=str, default=None)
    parser.add_argument("--client-secret", type=str, default=None)
    parser.add_argument("--refresh-token", type=str, default=None)
    args = parser.parse_args()

    client_id = args.client_id or os.environ.get("WITHINGS_CLIENT_ID")
    client_secret = args.client_secret or os.environ.get("WITHINGS_CLIENT_SECRET")
    refresh_token = args.refresh_token or os.environ.get("WITHINGS_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        sys.exit(
            "Missing Withings credentials. Set env vars:\n"
            "  WITHINGS_CLIENT_ID\n"
            "  WITHINGS_CLIENT_SECRET\n"
            "  WITHINGS_REFRESH_TOKEN\n"
            "Or pass --client-id, --client-secret, --refresh-token"
        )

    # Calculate epoch range
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=args.days)
    start_epoch = int(start.timestamp())
    end_epoch = int(now.timestamp())

    # Auth
    print(f"🔄 Refreshing Withings access token...", file=sys.stderr)
    access_token, _new_refresh = get_access_token(client_id, client_secret, refresh_token)

    # Fetch
    print(f"📥 Fetching body comp data from last {args.days} days...", file=sys.stderr)
    groups = fetch_measures(access_token, start_epoch, end_epoch)
    print(f"   Found {len(groups)} measurement sessions", file=sys.stderr)

    # Parse
    records = parse_measure_groups(groups)
    trends = compute_trends(records)

    # Output
    output = {
        "fetched_at": now.isoformat(),
        "period_days": args.days,
        "count": len(records),
        "trends": trends,
        "measurements": records,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
