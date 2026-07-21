#!/usr/bin/env python3
"""
Generate Live Match JSON from source sports data.
Converts Bangladesh time (Asia/Dhaka) to UTC Unix timestamp in milliseconds.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests
import pytz

# Source URL
SOURCE_URL = "https://raw.githubusercontent.com/sm-monirulislam/Upcoming-and-Live-Sports-Data/refs/heads/main/Sports_data.json"

# Output file path
OUTPUT_FILE = "app/json/livematch.json"

# Category icons mapping - EDIT THIS TO CUSTOMIZE ICONS
CATEGORY_ICONS = {
    "Cricket": "https://img.icons8.com/color/96/000000/cricket.png",
    "Football": "https://img.icons8.com/color/96/000000/football.png",
    "Tennis": "https://img.icons8.com/color/96/000000/tennis-ball.png",
    "Basketball": "https://img.icons8.com/color/96/000000/basketball.png",
    "Volleyball": "https://img.icons8.com/color/96/000000/volleyball.png",
    "Badminton": "https://img.icons8.com/color/96/000000/badminton.png",
    "Table Tennis": "https://img.icons8.com/color/96/000000/table-tennis.png",
    "Rugby": "https://img.icons8.com/color/96/000000/rugby.png",
    "Boxing": "https://img.icons8.com/color/96/000000/boxing.png",
    "MMA": "https://img.icons8.com/color/96/000000/mma.png",
    "WWE": "https://img.icons8.com/color/96/000000/wrestling.png",
    "Golf": "https://img.icons8.com/color/96/000000/golf.png",
    "Motorsport": "https://img.icons8.com/color/96/000000/race-car.png",
    "E-Sports": "https://img.icons8.com/color/96/000000/esports.png",
    "NBA": "https://img.icons8.com/color/96/000000/basketball.png",
    "NFL": "https://img.icons8.com/color/96/000000/american-football.png",
    "MLB": "https://img.icons8.com/color/96/000000/baseball.png",
    "NHL": "https://img.icons8.com/color/96/000000/hockey.png",
    "Soccer": "https://img.icons8.com/color/96/000000/soccer-ball.png",
    "FIFA": "https://img.icons8.com/color/96/000000/soccer-ball.png",
    "UEFA": "https://img.icons8.com/color/96/000000/soccer-ball.png",
    "Bundesliga": "https://img.icons8.com/color/96/000000/soccer-ball.png",
    "La Liga": "https://img.icons8.com/color/96/000000/soccer-ball.png",
    "Serie A": "https://img.icons8.com/color/96/000000/soccer-ball.png",
    "Premier League": "https://img.icons8.com/color/96/000000/soccer-ball.png",
    "Ligue 1": "https://img.icons8.com/color/96/000000/soccer-ball.png",
    "IPL": "https://img.icons8.com/color/96/000000/cricket.png",
    "Big Bash": "https://img.icons8.com/color/96/000000/cricket.png",
    "PSL": "https://img.icons8.com/color/96/000000/cricket.png",
    "CPL": "https://img.icons8.com/color/96/000000/cricket.png",
    "The Hundred": "https://img.icons8.com/color/96/000000/cricket.png",
}

# Bangladesh timezone
BDT_TIMEZONE = pytz.timezone("Asia/Dhaka")


def fetch_source_data() -> Dict[str, Any]:
    """Fetch the source JSON data from the URL."""
    try:
        print(f"📡 Fetching data from: {SOURCE_URL}")
        response = requests.get(SOURCE_URL, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Successfully fetched data")
        print(f"   Total matches: {data.get('total_matches', 0)}")
        print(f"   Live matches: {data.get('live_match', 0)}")
        
        return data
    except requests.RequestException as e:
        print(f"❌ Failed to fetch source data: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        raise


def convert_bdt_to_utc_timestamp(start_time: str) -> str:
    """Convert Bangladesh local time to UTC Unix timestamp in milliseconds."""
    if not start_time:
        print(f"⚠️  Warning: Empty start_time, using current time")
        return str(int(datetime.now().timestamp() * 1000))
    
    try:
        parts = start_time.strip().split()
        if len(parts) < 3:
            raise ValueError(f"Invalid time format: {start_time}")
        
        date_str = parts[0]
        time_str = parts[1]
        ampm = parts[2]
        
        day, month, year = map(int, date_str.split('-'))
        hour, minute = map(int, time_str.split(':'))
        
        if ampm.upper() == "PM" and hour != 12:
            hour += 12
        elif ampm.upper() == "AM" and hour == 12:
            hour = 0
        
        naive_dt = datetime(year, month, day, hour, minute)
        bdt_dt = BDT_TIMEZONE.localize(naive_dt)
        utc_dt = bdt_dt.astimezone(pytz.UTC)
        timestamp_ms = int(utc_dt.timestamp() * 1000)
        
        return str(timestamp_ms)
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to convert time '{start_time}': {e}")
        return str(int(datetime.now().timestamp() * 1000))


def transform_match(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform a single match from source format to target format."""
    try:
        event_info = match.get("eventInfo", {})
        streams = match.get("streams", [])
        
        team_a = event_info.get("teamA", "")
        team_b = event_info.get("teamB", "")
        team_a_flag = event_info.get("teamAFlag", "")
        team_b_flag = event_info.get("teamBFlag", "")
        start_time = event_info.get("startTime", "")
        category = match.get("Category", "Unknown")
        event_name = event_info.get("eventName", "")
        match_event_name = match.get("event_name", "")
        
        if not team_a or not team_b:
            print(f"⚠️  Skipping match: Missing team names")
            return None
        
        if category and event_name:
            league_name = f"{category} || {event_name}"
        elif category:
            league_name = category
        elif event_name:
            league_name = event_name
        else:
            league_name = "Unknown League"
        
        league_icon = CATEGORY_ICONS.get(category, "")
        timestamp = convert_bdt_to_utc_timestamp(start_time)
        
        live_links = []
        for stream in streams:
            stream_url = stream.get("stream_url", "")
            if stream_url:
                live_links.append({
                    "link_title": match_event_name or f"{team_a} vs {team_b}",
                    "channel_url": stream_url
                })
        
        transformed = {
            "team1_name": team_a,
            "team2_name": team_b,
            "team1_logo_url": team_a_flag,
            "team2_logo_url": team_b_flag,
            "time": timestamp,
            "league_name": league_name,
            "league_icon": league_icon,
            "category": category,
            "live_links": live_links
        }
        
        return transformed
        
    except Exception as e:
        print(f"⚠️  Error transforming match: {e}")
        return None


def main():
    """Main execution function."""
    print("🚀 Starting Live Match JSON Generator")
    print("=" * 50)
    
    try:
        source_data = fetch_source_data()
        matches = source_data.get("matches", [])
        
        if not matches:
            print("⚠️  No matches found in source data")
            transformed_matches = []
        else:
            print(f"\n🔄 Processing {len(matches)} matches...")
            transformed_matches = []
            skipped = 0
            
            for idx, match in enumerate(matches, 1):
                transformed = transform_match(match)
                if transformed:
                    transformed_matches.append(transformed)
                    print(f"   ✓ Match {idx}: {transformed.get('team1_name')} vs {transformed.get('team2_name')}")
                else:
                    skipped += 1
                    print(f"   ✗ Match {idx}: Skipped")
            
            print(f"\n✅ Successfully transformed {len(transformed_matches)} matches")
            if skipped > 0:
                print(f"   ⚠️  Skipped {skipped} matches")
        
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(transformed_matches, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Generated: {OUTPUT_FILE}")
        print(f"   File size: {os.path.getsize(OUTPUT_FILE)} bytes")
        print(f"   Matches: {len(transformed_matches)}")
        
        print("\n✅ Done!")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
