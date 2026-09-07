#!/usr/bin/env python3
"""
Generate Live Match JSON from source sports data.
Converts Bangladesh time (Asia/Dhaka) to UTC Unix timestamp in milliseconds.
Filters out matches with status "FINISHED".
Auto-removes matches based on sport-specific time limits:
- Football, Basketball, Baseball: 4 hours
- Cricket: 12 hours
Supports event_logo for league icons.
Supports both drm_key and kid+key DRM formats.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import requests
import pytz

# Source URL
SOURCE_URL = "https://raw.githubusercontent.com/sm-monirulislam/Upcoming-and-Live-Sports-Data/refs/heads/main/Sports_data.json"

# Output file path
OUTPUT_FILE = "app/json/livematch.json"

# Cache file path (if provided by environment)
CACHE_FILE = os.environ.get("SOURCE_DATA_CACHE", "")

# Fallback video URL when no streams are available
FALLBACK_VIDEO_URL = "https://raw.githubusercontent.com/nightbirdscompany/4kstreamzdata/refs/heads/main/app/video/4K%20Streamz%20Intro.mp4"

# Fallback image URL when team flags are missing
FALLBACK_IMAGE_URL = "https://via.placeholder.com/96x96/cccccc/666666?text=Team"

# Statuses to exclude (matches with these statuses will be skipped)
EXCLUDED_STATUSES = ["FINISHED", "COMPLETED", "ENDED"]

# Sport-specific expiry hours (how long a match should stay after start time)
SPORT_EXPIRY_HOURS = {
    "Football": 4,
    "Basketball": 4,
    "Baseball": 4,
    "Cricket": 12,
    "Tennis": 6,
    "Volleyball": 3,
    "Badminton": 3,
    "Table Tennis": 3,
    "Rugby": 4,
    "Boxing": 3,
    "MMA": 3,
    "WWE": 3,
    "Golf": 8,
    "Motorsport": 6,
    "Motogp": 6,
    "E-Sports": 4,
    "NBA": 4,
    "NFL": 6,
    "MLB": 4,
    "NHL": 4,
    "Soccer": 4,
    "FIFA": 4,
    "UEFA": 4,
    "Bundesliga": 4,
    "La Liga": 4,
    "Serie A": 4,
    "Premier League": 4,
    "Ligue 1": 4,
    "IPL": 12,
    "Big Bash": 12,
    "PSL": 12,
    "CPL": 12,
    "The Hundred": 12,
}

# Default expiry hours for unknown sports
DEFAULT_EXPIRY_HOURS = 6

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
    "NBA": "https://img.sofascore.com/api/v1/unique-tournament/132/image",
    "NFL": "https://img.sofascore.com/api/v1/unique-tournament/9464/image",
    "MLB": "https://img.sofascore.com/api/v1/unique-tournament/11205/image",
    "NHL": "https://img.icons8.com/color/96/000000/hockey.png",
    "Soccer": "https://img.icons8.com/color/96/000000/soccer-ball.png",
    "FIFA": "https://img.icons8.com/color/96/000000/soccer-ball.png",
    "UEFA": "https://img.sofascore.com/api/v1/unique-tournament/7/image",
    "Bundesliga": "https://img.sofascore.com/api/v1/unique-tournament/35/image",
    "La Liga": "https://img.sofascore.com/api/v1/unique-tournament/8/image",
    "Serie A": "https://img.sofascore.com/api/v1/unique-tournament/23/image",
    "Premier League": "https://img.sofascore.com/api/v1/unique-tournament/17/image",
    "Ligue 1": "https://img.sofascore.com/api/v1/unique-tournament/34/image",
    "IPL": "https://img.icons8.com/color/96/000000/cricket.png",
    "Big Bash": "https://img.icons8.com/color/96/000000/cricket.png",
    "PSL": "https://img.icons8.com/color/96/000000/cricket.png",
    "CPL": "https://img.icons8.com/color/96/000000/cricket.png",
    "The Hundred": "https://img.icons8.com/color/96/000000/cricket.png",
}

# Bangladesh timezone
BDT_TIMEZONE = pytz.timezone("Asia/Dhaka")


def fetch_source_data() -> Dict[str, Any]:
    """Fetch the source JSON data from the URL or cache."""
    # Try to use cached data first
    if CACHE_FILE and os.path.exists(CACHE_FILE):
        try:
            print(f"📂 Loading source data from cache: {CACHE_FILE}")
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Successfully loaded cached data")
            print(f"   Total matches: {data.get('total_matches', 0)}")
            print(f"   Live matches: {data.get('live_match', 0)}")
            return data
        except Exception as e:
            print(f"⚠️  Failed to load cached data: {e}")
    
    # Fallback to fetching from URL
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


def convert_bdt_to_datetime(start_time: str) -> Optional[datetime]:
    """Convert Bangladesh local time string to datetime object."""
    if not start_time:
        return None
    
    try:
        # Handle different date formats
        start_time = start_time.strip()
        
        # Try format: "20/08/2026 04:00:00 PM"
        if '/' in start_time:
            parts = start_time.split()
            if len(parts) >= 2:
                date_part = parts[0]
                time_part = parts[1]
                ampm = parts[2] if len(parts) > 2 else ""
                
                day, month, year = map(int, date_part.split('/'))
                
                # Parse time (could be "04:00:00" or "04:00")
                if ':' in time_part:
                    time_parts = time_part.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                else:
                    hour = int(time_part)
                    minute = 0
                
                if ampm.upper() == "PM" and hour != 12:
                    hour += 12
                elif ampm.upper() == "AM" and hour == 12:
                    hour = 0
                
                naive_dt = datetime(year, month, day, hour, minute)
                bdt_dt = BDT_TIMEZONE.localize(naive_dt)
                utc_dt = bdt_dt.astimezone(pytz.UTC)
                return utc_dt
        
        # Try format: "20-08-2026 04:00 PM"
        parts = start_time.strip().split()
        if len(parts) < 3:
            return None
        
        date_str = parts[0]
        time_str = parts[1]
        ampm = parts[2]
        
        # Handle different date separators
        if '-' in date_str:
            day, month, year = map(int, date_str.split('-'))
        elif '/' in date_str:
            day, month, year = map(int, date_str.split('/'))
        else:
            return None
        
        # Parse time (could be "04:00:00" or "04:00")
        if ':' in time_str:
            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
        else:
            hour = int(time_str)
            minute = 0
        
        if ampm.upper() == "PM" and hour != 12:
            hour += 12
        elif ampm.upper() == "AM" and hour == 12:
            hour = 0
        
        naive_dt = datetime(year, month, day, hour, minute)
        bdt_dt = BDT_TIMEZONE.localize(naive_dt)
        utc_dt = bdt_dt.astimezone(pytz.UTC)
        
        return utc_dt
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to parse time '{start_time}': {e}")
        return None


def convert_bdt_to_utc_timestamp(start_time: str) -> str:
    """Convert Bangladesh local time to UTC Unix timestamp in milliseconds."""
    if not start_time:
        print(f"⚠️  Warning: Empty start_time, using current time")
        return str(int(datetime.now().timestamp() * 1000))
    
    try:
        # Try to use the improved parser
        utc_dt = convert_bdt_to_datetime(start_time)
        if utc_dt:
            timestamp_ms = int(utc_dt.timestamp() * 1000)
            return str(timestamp_ms)
        
        # Fallback to original parsing
        parts = start_time.strip().split()
        if len(parts) < 3:
            raise ValueError(f"Invalid time format: {start_time}")
        
        date_str = parts[0]
        time_str = parts[1]
        ampm = parts[2]
        
        # Handle different date separators
        if '-' in date_str:
            day, month, year = map(int, date_str.split('-'))
        elif '/' in date_str:
            day, month, year = map(int, date_str.split('/'))
        else:
            raise ValueError(f"Invalid date format: {date_str}")
        
        # Parse time (could be "04:00:00" or "04:00")
        if ':' in time_str:
            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
        else:
            hour = int(time_str)
            minute = 0
        
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


def get_expiry_hours(category: str) -> int:
    """
    Get the expiry hours for a specific sport category.
    Returns the number of hours after which a match should be removed.
    """
    # Check if the category has a specific expiry time
    if category in SPORT_EXPIRY_HOURS:
        return SPORT_EXPIRY_HOURS[category]
    
    # Check for partial matches (e.g., "Football - Premier League" -> "Football")
    for sport, hours in SPORT_EXPIRY_HOURS.items():
        if sport.lower() in category.lower() or category.lower() in sport.lower():
            return hours
    
    # Return default if no match found
    return DEFAULT_EXPIRY_HOURS


def is_match_expired(start_time: str, category: str) -> bool:
    """
    Check if a match has exceeded its sport-specific expiry time.
    Returns True if the match should be removed.
    """
    if not start_time:
        return False
    
    utc_dt = convert_bdt_to_datetime(start_time)
    if not utc_dt:
        return False
    
    # Get expiry hours for this sport
    expiry_hours = get_expiry_hours(category)
    
    # Check if match has exceeded the expiry time
    now_utc = datetime.now(pytz.UTC)
    time_diff = now_utc - utc_dt
    
    is_expired = time_diff > timedelta(hours=expiry_hours)
    
    if is_expired:
        print(f"   🕐 Match expired: {category} started {time_diff.total_seconds() / 3600:.1f}h ago (limit: {expiry_hours}h)")
    
    return is_expired


def get_valid_url(url: str, fallback: str = None) -> str:
    """
    Return a valid URL. If the URL is empty or None, return the fallback.
    If no fallback is provided, use FALLBACK_IMAGE_URL.
    """
    if url and isinstance(url, str) and url.strip():
        return url.strip()
    return fallback if fallback else FALLBACK_IMAGE_URL


def build_stream_url(stream_url: str, drm_key: str = None, kid: str = None, key: str = None) -> str:
    """
    Build the final stream URL with DRM parameters.
    Supports both drm_key format and kid+key format.
    
    Examples:
        1. drm_key format: "drm_key" -> "?|drmScheme=clearkey&drmLicense=drm_key"
        2. kid+key format: kid="abc", key="123" -> "?|drmScheme=clearkey&drmLicense=abc:123"
    
    Args:
        stream_url: The stream URL
        drm_key: Combined DRM key (format: "kid:key")
        kid: Key ID (used with key parameter)
        key: Key value (used with kid parameter)
    """
    if not stream_url or not stream_url.strip():
        return ""
    
    stream_url = stream_url.strip()
    
    # Remove everything after .mpd (including |user-agent=...)
    if '.mpd' in stream_url:
        # Find the position of .mpd and keep everything up to and including .mpd
        mpd_pos = stream_url.find('.mpd')
        if mpd_pos != -1:
            stream_url = stream_url[:mpd_pos + 4]  # +4 to include '.mpd'
    
    # Build DRM license string
    drm_license = None
    
    # Priority 1: Use kid + key combination (new format)
    if kid and key and kid.strip() and key.strip():
        drm_license = f"{kid.strip()}:{key.strip()}"
        print(f"   🔑 Using kid+key DRM format: {drm_license[:20]}...")
    # Priority 2: Use combined drm_key (old format)
    elif drm_key and drm_key.strip():
        drm_license = drm_key.strip()
        print(f"   🔑 Using drm_key format: {drm_license[:20]}...")
    
    # If DRM license exists, append to URL with ?|
    if drm_license:
        return f"{stream_url}?|drmScheme=clearkey&drmLicense={drm_license}"
    
    return stream_url


def is_match_finished(status: str) -> bool:
    """
    Check if a match is finished (should be excluded).
    Returns True if the match should be removed.
    """
    if not status:
        return False
    
    status_upper = status.upper().strip()
    return status_upper in EXCLUDED_STATUSES


def transform_match(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform a single match from source format to target format."""
    try:
        event_info = match.get("eventInfo", {})
        streams = match.get("streams", [])
        
        team_a = event_info.get("teamA", "Unknown")
        team_b = event_info.get("teamB", "Unknown")
        team_a_flag = event_info.get("teamAFlag", "")
        team_b_flag = event_info.get("teamBFlag", "")
        start_time = event_info.get("startTime", "")
        category = match.get("Category", "Unknown")
        event_name = event_info.get("eventName", "")
        match_event_name = match.get("event_name", "")
        status = match.get("status", "")
        
        # Get event_logo if available (new field)
        event_logo = event_info.get("event_logo", "")
        
        if not team_a or not team_b:
            print(f"⚠️  Skipping match: Missing team names")
            return None
        
        # Check if match is finished (exclude it)
        if is_match_finished(status):
            print(f"   🏁 Skipping finished match: {team_a} vs {team_b} (Status: {status})")
            return None
        
        # Check if match has expired based on sport-specific time limit
        if is_match_expired(start_time, category):
            expiry_hours = get_expiry_hours(category)
            print(f"   🕐 Removing expired match: {team_a} vs {team_b} ({category} - limit: {expiry_hours}h)")
            return None
        
        if category and event_name:
            league_name = f"{category} || {event_name}"
        elif category:
            league_name = category
        elif event_name:
            league_name = event_name
        else:
            league_name = "Unknown League"
        
        # Get league icon: prefer event_logo, fallback to category icon
        league_icon = ""
        if event_logo and event_logo.strip():
            league_icon = get_valid_url(event_logo)
            print(f"   🏷️  Using event_logo for league icon: {league_icon}")
        else:
            # Fallback to category icon
            league_icon = CATEGORY_ICONS.get(category, "")
            league_icon = get_valid_url(league_icon, "https://via.placeholder.com/96x96/cccccc/666666?text=Sport")
        
        timestamp = convert_bdt_to_utc_timestamp(start_time)
        
        # Build live links
        live_links = []
        
        # If streams exist and are not empty, use them
        if streams and len(streams) > 0:
            for stream in streams:
                stream_url = stream.get("stream_url", "")
                drm_key = stream.get("drm_key", "")
                # Support both "name" and "channel_name" fields
                stream_name = stream.get("name", "") or stream.get("channel_name", "")
                
                # Get kid and key for new DRM format
                kid = stream.get("kid", "")
                key = stream.get("key", "")
                
                # Get user_agent if available (for future use)
                user_agent = stream.get("user_agent", "")
                
                if stream_url and stream_url.strip():
                    # Build the final URL with DRM if available (supports both formats)
                    final_url = build_stream_url(stream_url, drm_key, kid, key)
                    
                    # If user_agent exists, we could append it, but keeping it simple for now
                    # You can extend this to add user_agent to the URL if needed
                    
                    # Use stream name if available, otherwise use match name
                    if stream_name and stream_name.strip():
                        link_title = stream_name
                    else:
                        # If no stream name, use match event name or team names
                        link_title = match_event_name if match_event_name and match_event_name.strip() else f"{team_a} vs {team_b}"
                    
                    live_links.append({
                        "link_title": link_title,
                        "channel_url": final_url
                    })
        
        # If no live links were added, add the intro video
        if not live_links:
            print(f"   ℹ️  No valid streams found for {team_a} vs {team_b}, adding intro video")
            live_links.append({
                "link_title": "Intro",
                "channel_url": FALLBACK_VIDEO_URL
            })
        
        # Ensure ALL image URLs are valid (not empty)
        team_a_flag = get_valid_url(team_a_flag)
        team_b_flag = get_valid_url(team_b_flag)
        
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
    print(f"⏰ Current UTC time: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("📋 Excluding matches with status: FINISHED, COMPLETED, ENDED")
    print("📋 Sport-specific expiry rules:")
    print("   • Football, Basketball, Baseball: 4 hours")
    print("   • Cricket: 12 hours")
    print("   • Other sports: 6 hours (default)")
    print("📋 League icon priority: event_logo > category icon > fallback")
    print("📋 DRM support: drm_key (combined) OR kid+key (separate)")
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
            finished = 0
            expired = 0
            
            for idx, match in enumerate(matches, 1):
                status = match.get("status", "Unknown")
                category = match.get("Category", "Unknown")
                transformed = transform_match(match)
                if transformed:
                    transformed_matches.append(transformed)
                    live_links_count = len(transformed.get('live_links', []))
                    print(f"   ✓ Match {idx}: {transformed.get('team1_name')} vs {transformed.get('team2_name')} (Status: {status}, Category: {category}, Links: {live_links_count})")
                else:
                    # Check why it was skipped
                    if is_match_finished(status):
                        finished += 1
                    elif match.get("eventInfo", {}).get("startTime") and is_match_expired(
                        match.get("eventInfo", {}).get("startTime", ""), 
                        category
                    ):
                        expired += 1
                    else:
                        skipped += 1
                    print(f"   ✗ Match {idx}: Skipped (Status: {status}, Category: {category})")
            
            print(f"\n✅ Successfully transformed {len(transformed_matches)} matches")
            if skipped > 0:
                print(f"   ⚠️  Skipped {skipped} matches (missing required fields)")
            if finished > 0:
                print(f"   🏁 Excluded {finished} finished matches (Status: FINISHED/COMPLETED/ENDED)")
            if expired > 0:
                print(f"   🕐 Removed {expired} expired matches (exceeded sport-specific time limit)")
        
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(transformed_matches, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Generated: {OUTPUT_FILE}")
        print(f"   File size: {os.path.getsize(OUTPUT_FILE)} bytes")
        print(f"   Matches: {len(transformed_matches)}")
        
        # Check for any empty URLs in the output
        print("\n🔍 Validating generated JSON...")
        has_empty_urls = False
        for i, match in enumerate(transformed_matches):
            for key, value in match.items():
                if isinstance(value, str) and (not value or not value.strip()):
                    print(f"   ⚠️  Match {i+1} has empty field: {key}")
                    has_empty_urls = True
            # Check live_links
            for link in match.get('live_links', []):
                for key, value in link.items():
                    if isinstance(value, str) and (not value or not value.strip()):
                        print(f"   ⚠️  Match {i+1} live_link has empty field: {key}")
                        has_empty_urls = True
        
        if has_empty_urls:
            print("   ❌ WARNING: Found empty URL fields in generated JSON!")
        else:
            print("   ✅ All URL fields are valid")
        
        print("\n✅ Done!")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
