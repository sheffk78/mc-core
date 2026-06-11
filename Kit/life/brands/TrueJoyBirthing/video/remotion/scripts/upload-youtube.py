#!/usr/bin/env python3
"""
YouTube Upload — Upload TJB city guide videos to YouTube.
Manages playlists per state + master "All City Guides" playlist.

Usage:
    python3 scripts/upload-youtube.py denver-co

Requires:
    - .youtube-oauth/token.json (created by youtube-auth-setup.py)
    - ./out/{slug}-city-guide.mp4 (rendered video)
    - ./out/yt-thumb-{slug}.png (optional thumbnail)
"""
import os, sys, json, re, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OAUTH_DIR = os.path.join(PROJECT_DIR, '.youtube-oauth')
TOKEN_PATH = os.path.join(OAUTH_DIR, 'token.json')

# State abbreviation → full name
STATE_NAMES = {
    'al': 'Alabama', 'ak': 'Alaska', 'az': 'Arizona', 'ar': 'Arkansas', 'ca': 'California',
    'co': 'Colorado', 'ct': 'Connecticut', 'de': 'Delaware', 'fl': 'Florida', 'ga': 'Georgia',
    'hi': 'Hawaii', 'id': 'Idaho', 'il': 'Illinois', 'in': 'Indiana', 'ia': 'Iowa',
    'ks': 'Kansas', 'ky': 'Kentucky', 'la': 'Louisiana', 'me': 'Maine', 'md': 'Maryland',
    'ma': 'Massachusetts', 'mi': 'Michigan', 'mn': 'Minnesota', 'ms': 'Mississippi', 'mo': 'Missouri',
    'mt': 'Montana', 'ne': 'Nebraska', 'nv': 'Nevada', 'nh': 'New Hampshire', 'nj': 'New Jersey',
    'nm': 'New Mexico', 'ny': 'New York', 'nc': 'North Carolina', 'nd': 'North Dakota', 'oh': 'Ohio',
    'ok': 'Oklahoma', 'or': 'Oregon', 'pa': 'Pennsylvania', 'ri': 'Rhode Island', 'sc': 'South Carolina',
    'sd': 'South Dakota', 'tn': 'Tennessee', 'tx': 'Texas', 'ut': 'Utah', 'vt': 'Vermont',
    'va': 'Virginia', 'wa': 'Washington', 'wv': 'West Virginia', 'wi': 'Wisconsin', 'wy': 'Wyoming',
}

MASTER_PLAYLIST_NAME = "All City Birth Guides"
MASTER_PLAYLIST_DESC = "City-by-city birth guides for doulas, midwives, hospitals, costs, and insurance. Built by True Joy Birthing."


def parse_state(slug):
    """Extract state abbreviation from slug (e.g. 'denver-co' → 'co')."""
    parts = slug.rsplit('-', 1)
    if len(parts) == 2 and parts[1] in STATE_NAMES:
        return parts[1].lower()
    return None


def get_state_name(slug):
    """Get full state name from slug."""
    abbr = parse_state(slug)
    if abbr is None:
        return ''
    return STATE_NAMES.get(abbr, '')


# ─── City metadata ───
CITY_META = {
    'denver-co': {
        'title': 'Denver Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Denver — now what? This guide walks you through everything: doulas and midwives serving Denver, hospital policies, real costs, and whether Colorado Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Denver doula directory → https://truejoybirthing.com/birth-support/denver-co/

▸ Find Denver doulas & midwives
▸ Compare hospital options (UCHealth, Saint Joseph, PSL)
▸ Know what doula care actually costs ($1,000–$3,000)
▸ Understand Colorado Medicaid doula coverage ($750/birth)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Denver
0:09 — Where Denver Families Deliver (Hospitals)
1:04 — Doulas & Midwives in Denver
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,000–$3,000)
2:37 — Insurance & Colorado Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#denverdoula #denverbirth #coloradomedicaid #birthplan #doula #pregnancydenver""",
        'tags': [
            'Denver doula', 'Denver birth doula', 'Colorado Medicaid doula',
            'Denver pregnancy guide', 'birth plan template', 'first time mom Denver',
            'Denver hospital maternity', 'Denver doula cost', 'Colorado birth support',
            'doula near me', 'Denver midwife', 'pregnancy Colorado',
            'free birth plan', 'doula services Denver', 'birth preparation'
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'tacoma-wa': {
        'title': 'Tacoma Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Tacoma — now what? This guide walks you through everything: doulas and midwives serving Tacoma, hospital policies, real costs, and whether Washington Apple Health covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Tacoma doula directory → https://truejoybirthing.com/birth-support/tacoma-wa/

▸ Find Tacoma doulas & midwives
▸ Compare hospital options (Tacoma General Level IV, St. Joseph Level III, Good Samaritan Level II)
▸ Know what doula care actually costs ($1,200–$3,500)
▸ Understand Washington Apple Health doula coverage ($1,500/birth)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Tacoma
0:11 — Where Tacoma Families Deliver (Hospitals)
1:24 — Doulas & Midwives in Tacoma
1:56 — The True Joy Birthing App
2:19 — Cost Reality ($1,200–$3,500)
2:36 — Insurance & Washington Apple Health
3:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#tacomadoula #tacomabirth #washingtonmedicaid #birthplan #doula #pregnancytacoma""",
        'tags': [
            'Tacoma doula', 'Tacoma birth doula', 'Washington Apple Health doula',
            'Tacoma pregnancy guide', 'birth plan template', 'first time mom Tacoma',
            'Tacoma hospital maternity', 'Tacoma doula cost', 'Washington birth support',
            'doula near me', 'Tacoma midwife', 'pregnancy Washington',
            'free birth plan', 'doula services Tacoma', 'birth preparation',
            'Tacoma General Hospital', 'St. Joseph Medical Center Tacoma',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'norfolk-va': {
        'title': 'Norfolk Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Norfolk — now what? This guide walks you through everything: doulas and midwives serving Norfolk, hospital policies, real costs, and whether Virginia Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Norfolk doula directory → https://truejoybirthing.com/birth-support/norfolk-va/

▸ Find Norfolk doulas & midwives
▸ Compare hospital options (Sentara Norfolk General, CHKD)
▸ Know what doula care actually costs ($1,200–$2,500)
▸ Understand Virginia Medicaid doula coverage (covered since 2024)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Norfolk
0:11 — Where Norfolk Families Deliver (Hospitals)
1:02 — Doulas & Midwives in Norfolk
1:15 — The True Joy Birthing App
1:40 — Cost Reality ($1,200–$2,500)
2:05 — Insurance & Virginia Medicaid
2:36 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#norfolkdoula #norfolkbirth #virginiamedicaid #birthplan #doula #pregnancynorfolk""",
        'tags': [
            'Norfolk doula', 'Norfolk birth doula', 'Virginia Medicaid doula',
            'Norfolk pregnancy guide', 'birth plan template', 'first time mom Norfolk',
            'Norfolk hospital maternity', 'Norfolk doula cost', 'Virginia birth support',
            'doula near me', 'Norfolk midwife', 'pregnancy Virginia',
            'free birth plan', 'doula services Norfolk', 'birth preparation',
            'Sentara Norfolk General', 'CHKD Norfolk',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
}


def get_access_token():
    """Get a fresh access token using the saved refresh token."""
    if not os.path.exists(TOKEN_PATH):
        print("ERROR: token.json not found. Run scripts/youtube-auth-setup.py first.")
        sys.exit(1)

    with open(TOKEN_PATH) as f:
        token_data = json.load(f)

    import requests
    resp = requests.post(token_data.get('token_uri', 'https://oauth2.googleapis.com/token'), data={
        'client_id': token_data['client_id'],
        'client_secret': token_data['client_secret'],
        'refresh_token': token_data['refresh_token'],
        'grant_type': 'refresh_token',
    }, timeout=30)

    if resp.status_code != 200:
        print(f"ERROR: Token refresh failed ({resp.status_code})")
        print(resp.text[:300])
        sys.exit(1)

    return resp.json()['access_token']


def get_or_create_playlist(token, name, description="", privacy="public"):
    """Find playlist by name, or create it. Returns playlist ID."""
    import requests
    auth = f"Bearer {token}"

    # Search for existing playlist
    page_token = None
    while True:
        params = {
            'part': 'snippet,status',
            'mine': 'true',
            'maxResults': '50',
        }
        if page_token:
            params['pageToken'] = page_token

        resp = requests.get(
            'https://www.googleapis.com/youtube/v3/playlists',
            headers={'Authorization': auth},
            params=params,
            timeout=15
        )

        if resp.status_code != 200:
            print(f"  ⚠️ Playlist search failed ({resp.status_code})")
            return None

        data = resp.json()
        for item in data.get('items', []):
            if item['snippet']['title'] == name:
                print(f"  📁 Found playlist: \"{name}\"")
                return item['id']

        page_token = data.get('nextPageToken')
        if not page_token:
            break

    # Not found — create it
    create_body = {
        'snippet': {
            'title': name,
            'description': description or f"True Joy Birthing {name}",
        },
        'status': {
            'privacyStatus': privacy,
        },
    }

    create_resp = requests.post(
        'https://www.googleapis.com/youtube/v3/playlists?part=snippet,status',
        headers={
            'Authorization': auth,
            'Content-Type': 'application/json',
        },
        json=create_body,
        timeout=15,
    )

    if create_resp.status_code in (200, 201):
        playlist_id = create_resp.json()['id']
        print(f"  📁 Created playlist: \"{name}\" ({playlist_id})")
        return playlist_id
    else:
        print(f"  ⚠️ Failed to create playlist \"{name}\": {create_resp.status_code}")
        return None


def add_video_to_playlist(token, playlist_id, video_id):
    """Add a video to a playlist."""
    import requests

    resp = requests.post(
        'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet',
        headers={
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json',
        },
        json={
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id,
                },
            },
        },
        timeout=15,
    )

    if resp.status_code in (200, 201):
        print(f"    ✅ Added to playlist")
        return True
    else:
        print(f"    ⚠️ Failed to add to playlist ({resp.status_code}): {resp.text[:150]}")
        return False


def upload_video(slug, video_path, thumb_path=None):
    """Upload video to YouTube with resumable upload protocol."""
    import requests

    meta = CITY_META.get(slug)
    if not meta:
        print(f"ERROR: No metadata configured for slug '{slug}'")
        print("Add an entry to CITY_META in this script.")
        sys.exit(1)

    token = get_access_token()
    auth_header = f"Bearer {token}"

    # Step 1: Get resumable upload URL
    body = {
        'snippet': {
            'title': meta['title'],
            'description': meta['description'],
            'tags': meta['tags'],
            'categoryId': meta['category_id'],
        },
        'status': {
            'privacyStatus': meta['privacy_status'],
            'selfDeclaredMadeForKids': meta['made_for_kids'],
        },
    }

    upload_url = 'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status'

    init_resp = requests.post(
        upload_url,
        headers={
            'Authorization': auth_header,
            'Content-Type': 'application/json',
            'X-Upload-Content-Length': str(os.path.getsize(video_path)),
            'X-Upload-Content-Type': 'video/mp4',
        },
        json=body,
        timeout=30,
    )

    if init_resp.status_code != 200:
        print(f"ERROR: Upload init failed ({init_resp.status_code})")
        print(init_resp.text[:500])
        return None

    session_uri = init_resp.headers.get('Location')
    if not session_uri:
        print("ERROR: No Location header in upload init response")
        return None

    print(f"  Resumable upload URL obtained. Uploading video...")

    # Step 2: Upload the video file
    file_size = os.path.getsize(video_path)
    with open(video_path, 'rb') as f:
        video_data = f.read()

    upload_resp = requests.put(
        session_uri,
        data=video_data,
        headers={
            'Content-Length': str(file_size),
            'Content-Type': 'video/*',
        },
        timeout=600,
    )

    if upload_resp.status_code not in (200, 201):
        print(f"ERROR: Upload failed ({upload_resp.status_code})")
        print(upload_resp.text[:500])
        return None

    result = upload_resp.json()
    video_id = result.get('id')
    print(f"  ✅ Video uploaded! ID: {video_id}")
    print(f"  URL: https://youtu.be/{video_id}")

    # Step 3: Upload thumbnail
    if thumb_path and os.path.exists(thumb_path):
        print(f"  Uploading thumbnail...")
        thumb_url = f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}"

        thumb_resp = requests.post(
            thumb_url,
            headers={'Authorization': auth_header},
            files={'media': (os.path.basename(thumb_path), open(thumb_path, 'rb'), 'image/png')},
            timeout=60,
        )

        if thumb_resp.status_code in (200, 201):
            print(f"  ✅ Thumbnail uploaded!")
        else:
            print(f"  ⚠️ Thumbnail upload failed ({thumb_resp.status_code})")

    return video_id


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/upload-youtube.py <slug>")
        print("Example: python3 scripts/upload-youtube.py denver-co")
        sys.exit(1)

    slug = sys.argv[1]
    video_path = os.path.join(PROJECT_DIR, 'out', f'{slug}-city-guide.mp4')
    thumb_path = os.path.join(PROJECT_DIR, 'out', f'yt-thumb-{slug}.png')

    state_name = get_state_name(slug)
    if not state_name:
        print(f"WARNING: Could not determine state from slug '{slug}'. Playlist management skipped.")
    else:
        print(f"\n  State: {state_name}")

    if not os.path.exists(video_path):
        print(f"ERROR: Video not found at {video_path}")
        print(f"Render it first: npx remotion render {slug}-City-Guide out/{slug}-city-guide.mp4")
        sys.exit(1)

    print(f"\n{'=' * 50}")
    print(f"  Uploading: {slug}")
    print(f"  Video:     {os.path.basename(video_path)} ({os.path.getsize(video_path) / 1024 / 1024:.1f}MB)")
    print(f"{'=' * 50}\n")

    video_id = upload_video(slug, video_path, thumb_path)

    if not video_id:
        print(f"\n❌ Upload failed.")
        sys.exit(1)

    # Save video ID
    result_file = os.path.join(PROJECT_DIR, 'out', f'{slug}-youtube-id.txt')
    with open(result_file, 'w') as f:
        f.write(video_id)

    print(f"\n✅ Upload to YouTube complete!")
    print(f"   https://youtu.be/{video_id}")
    print(f"   Embed:  https://www.youtube-nocookie.com/embed/{video_id}")

    # ─── Playlist management ───
    if state_name:
        token = get_access_token()
        token_short = token[:10]
        print(f"\n   Managing playlists...")

        # 1. State playlist
        state_playlist_name = f"{state_name} Birth Guides"
        state_playlist_desc = f"True Joy Birthing city-by-city birth guides for {state_name}. Find doulas, midwives, hospital info, costs, and Medicaid coverage."
        state_playlist_id = get_or_create_playlist(token, state_playlist_name, state_playlist_desc)
        if state_playlist_id:
            add_video_to_playlist(token, state_playlist_id, video_id)

        # 2. Master playlist
        master_playlist_id = get_or_create_playlist(token, MASTER_PLAYLIST_NAME, MASTER_PLAYLIST_DESC)
        if master_playlist_id:
            add_video_to_playlist(token, master_playlist_id, video_id)

        print(f"   Playlist management complete.")

    print(f"   Saved ID to: out/{slug}-youtube-id.txt")


if __name__ == '__main__':
    main()