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
0:11 — Where Norfolk Families Deliver
0:29 — Sentara Norfolk General Hospital
0:57 — Children's Hospital of The King's Daughters
1:22 — Doulas & Midwives in Norfolk
1:37 — The True Joy Birthing App
2:02 — Cost Reality ($1,200–$2,500)
2:26 — Insurance & Virginia Medicaid
2:57 — Your Next Step

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
    'fremont-ca': {
        'title': 'Fremont Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Fremont — now what? This guide walks you through everything: doulas and midwives serving Fremont, hospital policies, real costs, and California's Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Fremont doula directory → https://truejoybirthing.com/birth-support/fremont-ca/

▸ Find Fremont doulas & midwives (33 providers)
▸ Compare hospital options (Washington Hospital, El Camino Mountain View)
▸ Know what doula care actually costs ($1,500–$3,000)
▸ Understand California Medi-Cal PAVE doula coverage ($1,587/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Fremont
0:14 — Washington Hospital (Level II NICU, Doula-Friendly)
0:39 — El Camino Health Mountain View (Level III NICU)
1:04 — 33 Doulas & Midwives Serving Fremont
1:18 — The True Joy Birthing App
1:48 — Cost Reality ($1,500–$3,000)
2:13 — Insurance & California Medi-Cal
2:37 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#fremontdoula #fremontbirth #californiamedicaid #birthplan #doula #pregnancyfremont""",
        'tags': [
            'Fremont doula', 'Fremont birth doula', 'California Medi-Cal doula',
            'Fremont pregnancy guide', 'birth plan template', 'first time mom Fremont',
            'Fremont hospital maternity', 'Fremont doula cost', 'California birth support',
            'doula near me', 'Fremont midwife', 'pregnancy California',
            'free birth plan', 'doula services Fremont', 'birth preparation',
            'Washington Hospital Fremont', 'El Camino Health Mountain View',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'vancouver-wa': {
        'title': 'Vancouver WA Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Vancouver, Washington — now what? This guide walks you through everything: doulas and midwives serving Vancouver, hospital policies, real costs, and whether Washington Apple Health covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Vancouver doula directory → https://truejoybirthing.com/birth-support/vancouver-wa/

▸ Find Vancouver doulas & midwives
▸ Compare hospital options (PeaceHealth Southwest, Legacy Salmon Creek)
▸ Know what doula care actually costs ($1,200–$2,800)
▸ Understand Washington Apple Health doula coverage (mature program)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Vancouver
0:11 — Where Vancouver Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Vancouver
1:23 — The True Joy Birthing App
1:48 — Cost Reality ($1,200–$2,800)
2:13 — Insurance & Washington Apple Health
2:38 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#vancouverwadoula #vancouverwashingtonbirth #washingtonmedicaid #birthplan #doula #pregnancyvancouverwa""",
        'tags': [
            'Vancouver WA doula', 'Vancouver Washington birth doula', 'Washington Apple Health doula',
            'Vancouver WA pregnancy guide', 'birth plan template', 'first time mom Vancouver WA',
            'PeaceHealth Southwest maternity', 'Legacy Salmon Creek maternity',
            'Vancouver doula cost', 'Washington birth support',
            'doula near me', 'Vancouver WA midwife', 'pregnancy Washington',
            'free birth plan', 'doula services Vancouver WA', 'birth preparation',
            'Clark County doula', 'Vancouver WA birth guide',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'cary-nc': {
        'title': 'Cary Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Cary, North Carolina — now what? This guide walks you through everything: doulas and midwives serving Cary, hospital policies, real costs, and whether NC Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Cary doula directory → https://truejoybirthing.com/birth-support/cary-nc/

▸ Find Cary doulas & midwives
▸ Compare hospital options (WakeMed Cary Level III, UNC REX Level III, Duke Level IV)
▸ Know what doula care actually costs ($1,000–$3,000)
▸ Understand NC Medicaid doula coverage (since Oct 2024)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Cary
0:11 — Where Cary Families Deliver (Hospitals)
0:21 — Doulas & Midwives in Cary
0:29 — The True Joy Birthing App
0:52 — Cost Reality ($1,000–$3,000)
1:14 — Insurance & NC Medicaid
1:33 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#carydoula #caryncbirth #ncmedicaid #birthplan #doula #pregnancync""",
        'tags': [
            'Cary doula', 'Cary NC birth doula', 'North Carolina Medicaid doula',
            'Cary pregnancy guide', 'birth plan template', 'first time mom Cary NC',
            'WakeMed Cary maternity', 'UNC REX maternity', 'Cary doula cost',
            'North Carolina birth support', 'doula near me', 'Cary midwife',
            'pregnancy North Carolina', 'free birth plan', 'doula services Cary',
            'Research Triangle doula', 'Cary NC birth guide',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'unlisted',
        'made_for_kids': False,
    },
    'dallas-tx': {
        'title': 'Dallas Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Dallas — now what? This guide walks you through everything: doulas and midwives serving Dallas, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Dallas doula directory → https://truejoybirthing.com/birth-support/dallas-tx/

▸ Find Dallas doulas & midwives (10+ providers)
▸ Compare hospital options (Texas Health Dallas, Baylor, Parkland, Medical City Dallas, Methodist Dallas)
▸ Know what doula care actually costs ($900-$2,800)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Dallas
0:09 — Where Dallas Families Deliver
0:23 — Texas Health Presbyterian Hospital Dallas (Level III)
0:39 — Baylor University Medical Center (Level III)
0:55 — Parkland Memorial Hospital (Level III)
1:11 — Medical City Dallas (Level III)
1:27 — Methodist Dallas Medical Center (Level III)
1:43 — Doulas & Midwives in Dallas
1:57 — The True Joy Birthing App
2:22 — Cost Reality ($900-$2,800)
2:40 — Insurance & Texas Medicaid (SB 750)
3:05 — Urban Family Co-op Birth Center
3:22 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#dallasdoula #dallastxbirth #texasmedicaid #birthplan #doula #pregnancydallas""",
        'tags': [
            'Dallas doula', 'Dallas birth doula', 'Texas Medicaid doula',
            'Dallas pregnancy guide', 'birth plan template', 'first time mom Dallas',
            'Texas Health Dallas maternity', 'Baylor Dallas maternity', 'Parkland Hospital Dallas',
            'Dallas doula cost', 'Texas birth support',
            'doula near me', 'Dallas midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Dallas', 'birth preparation',
            'Medical City Dallas', 'Methodist Dallas',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'chesapeake-va': {
        'title': 'Chesapeake Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Chesapeake — now what? This guide walks you through everything: doulas and midwives serving Chesapeake, hospital policies, real costs, and whether Virginia Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Chesapeake doula directory → https://truejoybirthing.com/birth-support/chesapeake-va/

▸ Find Chesapeake doulas & midwives (6 providers)
▸ Compare hospital options (The BirthPlace at Chesapeake Regional Medical Center)
▸ Know what doula care actually costs ($1,200–$2,500)
▸ Understand Virginia Medicaid doula coverage (covered since 2024)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Chesapeake
0:10 — Where Chesapeake Families Deliver
0:30 — The BirthPlace at Chesapeake Regional Medical Center
1:00 — Doulas & Midwives in Chesapeake
1:14 — The True Joy Birthing App
1:39 — Cost Reality ($1,200–$2,500)
2:02 — Insurance & Virginia Medicaid
2:32 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#chesapeakedoula #chesapeakevabirth #virginiamedicaid #birthplan #doula #pregnancychesapeake""",
        'tags': [
            'Chesapeake doula', 'Chesapeake birth doula', 'Virginia Medicaid doula',
            'Chesapeake pregnancy guide', 'birth plan template', 'first time mom Chesapeake',
            'Chesapeake Regional Medical Center', 'The BirthPlace Chesapeake',
            'Chesapeake doula cost', 'Virginia birth support',
            'doula near me', 'Chesapeake midwife', 'pregnancy Virginia',
            'free birth plan', 'doula services Chesapeake', 'birth preparation',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'fontana-ca': {
        'title': 'Fontana Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Fontana — now what? This guide walks you through everything: doulas and midwives serving Fontana, hospital policies, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Fontana doula directory → https://truejoybirthing.com/birth-support/fontana-ca/

▸ Find Fontana doulas & midwives (10 providers)
▸ Compare hospital options (Kaiser Fontana, San Antonio Regional, Arrowhead, Pomona Valley, Community SB, Loma Linda, Riverside Community, Montclair)
▸ Know what doula care actually costs ($1,200-$2,500)
▸ Understand California Medi-Cal PAVE doula coverage ($1,587/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Fontana
0:13 — Where Fontana Families Deliver (Hospitals)
0:25 — Kaiser Permanente Fontana Medical Center
0:37 — San Antonio Regional Hospital
0:49 — Arrowhead Regional Medical Center
1:01 — Pomona Valley Hospital
1:13 — Community Hospital of San Bernardino
1:25 — Loma Linda University Medical Center
1:37 — Riverside Community Hospital
1:49 — Montclair Hospital Medical Center
2:01 — Doulas & Midwives in Fontana
2:13 — The True Joy Birthing App
2:35 — Cost Reality ($1,200-$2,500)
2:55 — Insurance & California Medi-Cal
3:15 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#fontanadoula #fontanacabirth #californiamedicaid #birthplan #doula #pregnancyfontana""",
        'tags': [
            'Fontana doula', 'Fontana birth doula', 'California Medi-Cal doula',
            'Fontana pregnancy guide', 'birth plan template', 'first time mom Fontana',
            'Kaiser Fontana maternity', 'San Antonio Regional Hospital', 'Arrowhead Regional Medical Center',
            'Fontana doula cost', 'California birth support',
            'doula near me', 'Fontana midwife', 'pregnancy California',
            'free birth plan', 'doula services Fontana', 'birth preparation',
            'Pomona Valley Hospital', 'Loma Linda Medical Center', 'Riverside Community Hospital',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'moreno-valley-ca': {
        'title': 'Moreno Valley Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Moreno Valley — now what? This guide walks you through everything: doulas and midwives serving Moreno Valley, hospital policies, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Moreno Valley doula directory → https://truejoybirthing.com/birth-support/moreno-valley-ca/

▸ Find Moreno Valley doulas & midwives (5 providers)
▸ Compare hospital options (Kaiser Permanente Moreno Valley Medical Center)
▸ Know what doula care actually costs ($1,200-$2,500)
▸ Understand California Medi-Cal PAVE doula coverage ($1,587/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Moreno Valley
0:12 — Where Moreno Valley Families Deliver (Hospitals)
0:24 — Kaiser Permanente Moreno Valley Medical Center
0:36 — Doulas & Midwives in Moreno Valley
1:08 — The True Joy Birthing App
1:30 — Cost Reality ($1,200-$2,500)
1:55 — Insurance & California Medi-Cal
2:15 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#morenovalleydoula #morenovalleycabirth #californiamedicaid #birthplan #doula #pregnancymorenovalley""",
        'tags': [
            'Moreno Valley doula', 'Moreno Valley birth doula', 'California Medi-Cal doula',
            'Moreno Valley pregnancy guide', 'birth plan template', 'first time mom Moreno Valley',
            'Kaiser Moreno Valley maternity', 'Moreno Valley doula cost', 'California birth support',
            'doula near me', 'Moreno Valley midwife', 'pregnancy California',
            'free birth plan', 'doula services Moreno Valley', 'birth preparation',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'carrollton-tx': {
        'title': 'Carrollton TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Carrollton — now what? This guide walks you through everything: doulas and midwives serving Carrollton, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Carrollton doula directory → https://truejoybirthing.com/birth-support/carrollton-tx/

▸ Find Carrollton doulas & midwives
▸ Compare hospital options (Medical City Lewisville, Texas Health Flower Mound)
▸ Know what doula care actually costs ($800–$2,800)
▸ Understand Texas Medicaid doula coverage (SB 750)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Carrollton
0:11 — Where Carrollton Families Deliver (Hospitals)
0:35 — Doulas & Midwives in Carrollton
1:05 — The True Joy Birthing App
1:25 — Cost Reality ($800–$2,800)
1:45 — Insurance & Texas Medicaid
2:10 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#carrolltondoula #carrolltontxbirth #texasmedicaid #birthplan #doula #pregnancycarrollton""",
        'tags': [
            'Carrollton doula', 'Carrollton birth doula', 'Texas Medicaid doula',
            'Carrollton pregnancy guide', 'birth plan template', 'first time mom Carrollton',
            'Medical City Lewisville maternity', 'Texas Health Flower Mound maternity',
            'Carrollton doula cost', 'Texas birth support',
            'doula near me', 'Carrollton midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Carrollton', 'birth preparation',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'san-bernardino-ca': {
        'title': 'San Bernardino Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in San Bernardino — now what? This guide walks you through everything: doulas and midwives serving San Bernardino, hospital policies, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 San Bernardino doula directory → https://truejoybirthing.com/birth-support/san-bernardino-ca/

▸ Find San Bernardino doulas & midwives
▸ Compare hospital options (St. Bernardine Medical Center, Community Hospital of San Bernardino)
▸ Know what doula care actually costs ($1,200–$2,500)
▸ Understand California Medi-Cal doula coverage (~$1,587/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to San Bernardino
0:12 — Where San Bernardino Families Deliver (Hospitals)
0:34 — Doulas & Midwives in San Bernardino
0:43 — The True Joy Birthing App
1:06 — Cost Reality ($1,200–$2,500)
1:31 — Insurance & California Medi-Cal
1:49 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#sanbernardinodoula #sanbernardinobirth #californiamedicaid #birthplan #doula #pregnancysanbernardino""",
        'tags': [
            'San Bernardino doula', 'San Bernardino birth doula', 'California Medi-Cal doula',
            'San Bernardino pregnancy guide', 'birth plan template', 'first time mom San Bernardino',
            'St. Bernardine Medical Center maternity', 'Community Hospital San Bernardino',
            'San Bernardino doula cost', 'California birth support',
            'doula near me', 'San Bernardino midwife', 'pregnancy California',
            'free birth plan', 'doula services San Bernardino', 'birth preparation',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'beaumont-tx': {
        'title': 'Beaumont TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Beaumont, Texas — now what? This guide walks you through everything: doulas and midwives serving Beaumont, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Beaumont doula directory → https://truejoybirthing.com/birth-support/beaumont-tx/

▸ Find Beaumont doulas & midwives
▸ Compare hospital options (Baptist Hospitals of SE Texas, CHRISTUS St. Elizabeth)
▸ Know what doula care actually costs ($700-$1,600)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Beaumont
0:13 — Where Beaumont Families Deliver (Hospitals)
0:26 — Baptist Hospitals of Southeast Texas (Level III)
0:52 — CHRISTUS Southeast Texas — St. Elizabeth (Level III)
1:22 — Doulas & Midwives in Beaumont
1:30 — The True Joy Birthing App
1:52 — Cost Reality ($700-$1,600)
2:18 — Insurance & Texas Medicaid
2:50 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#beaumonttxdoula #beaumonttexasbirth #texasmedicaid #birthplan #doula #pregnancybeaumont""",
        'tags': [
            'Beaumont TX doula', 'Beaumont Texas birth doula', 'Texas Medicaid doula',
            'Beaumont TX pregnancy guide', 'birth plan template', 'first time mom Beaumont TX',
            'Baptist Hospitals Beaumont maternity', 'CHRISTUS St. Elizabeth Beaumont',
            'Beaumont doula cost', 'Texas birth support',
            'doula near me', 'Beaumont midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Beaumont', 'birth preparation',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'waco-tx': {
        'title': 'Waco TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Waco, Texas — now what? This guide walks you through everything: doulas and midwives serving Waco, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Waco doula directory → https://truejoybirthing.com/birth-support/waco-tx/

▸ Find Waco doulas & midwives
▸ Compare hospital options (BSW Hillcrest Level III, Ascension Providence Level II)
▸ Know what doula care actually costs ($800-$1,500)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Waco
0:13 — Where Waco Families Deliver (Hospitals)
0:28 — BSW Hillcrest (Level III NICU, Women's & Children's Center)
0:55 — Ascension Providence (Level II NICU, Dell Children's)
1:22 — Doulas & Midwives in Waco
1:35 — The True Joy Birthing App
1:58 — Cost Reality ($800-$1,500)
2:22 — Insurance & Texas Medicaid
2:50 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#wacotxdoula #wacotexasbirth #texasmedicaid #birthplan #doula #pregnancywaco""",
        'tags': [
            'Waco TX doula', 'Waco Texas birth doula', 'Texas Medicaid doula',
            'Waco TX pregnancy guide', 'birth plan template', 'first time mom Waco TX',
            'BSW Hillcrest Waco maternity', 'Ascension Providence Waco',
            'Waco doula cost', 'Texas birth support',
            'doula near me', 'Waco midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Waco', 'birth preparation',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'killeen-tx': {
        'title': 'Killeen TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Killeen, Texas — now what? This guide walks you through everything: doulas and midwives serving Killeen, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Killeen doula directory → https://truejoybirthing.com/birth-support/killeen-tx/

▸ Find Killeen doulas & midwives
▸ Compare hospital options (AdventHealth Central Texas, BSW Temple, Darnall Army Medical Center)
▸ Know what doula care actually costs ($700-$1,800)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Killeen
0:11 — Where Killeen Families Deliver (Hospitals)
0:28 — AdventHealth Central Texas
0:55 — Baylor Scott & White Temple
1:22 — Carl R. Darnall Army Medical Center
1:49 — Doulas & Midwives in Killeen
2:02 — The True Joy Birthing App
2:25 — Cost Reality ($700-$1,800)
2:49 — Insurance & Texas Medicaid
3:17 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#killeentxdoula #killeentexasbirth #texasmedicaid #birthplan #doula #pregnancykilleen""",
        'tags': [
            'Killeen TX doula', 'Killeen Texas birth doula', 'Texas Medicaid doula',
            'Killeen TX pregnancy guide', 'birth plan template', 'first time mom Killeen TX',
            'AdventHealth Central Texas maternity', 'BSW Temple maternity',
            'Darnall Army Medical Center', 'Fort Cavazos doula',
            'Killeen doula cost', 'Texas birth support',
            'doula near me', 'Killeen midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Killeen', 'birth preparation',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'tyler-tx': {
        'title': 'Tyler Texas Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Tyler, Texas — now what? This guide walks you through everything: doulas and midwives serving Tyler, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Tyler doula directory → https://truejoybirthing.com/birth-support/tyler-tx/

▸ Find Tyler doulas & midwives
▸ Compare hospital options (CHRISTUS Mother Frances Level III, UT Health Tyler Level III)
▸ Know what doula care actually costs ($800-$2,000)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Tyler
0:11 — Where Tyler Families Deliver (Hospitals)
0:28 — CHRISTUS Mother Frances Hospital (Level III NICU)
0:55 — UT Health Tyler (Level III NICU)
1:22 — Azalea Birth Center
1:49 — Doulas & Midwives in Tyler
2:02 — The True Joy Birthing App
2:25 — Cost Reality ($800-$2,000)
2:49 — Insurance & Texas Medicaid
3:17 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#tylertxdoula #tylertexasbirth #texasmedicaid #birthplan #doula #pregnancytyler""",
        'tags': [
            'Tyler TX doula', 'Tyler Texas birth doula', 'Texas Medicaid doula',
            'Tyler TX pregnancy guide', 'birth plan template', 'first time mom Tyler TX',
            'CHRISTUS Mother Frances Tyler maternity', 'UT Health Tyler maternity',
            'Azalea Birth Center', 'Tyler doula cost', 'Texas birth support',
            'doula near me', 'Tyler midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Tyler', 'birth preparation',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },

    'austin-tx': {
        'title': 'Austin Texas Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Austin, Texas — now what? This guide walks you through everything: doulas and midwives serving Austin, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Austin doula directory → https://truejoybirthing.com/birth-support/austin-tx/

▸ Find Austin doulas & midwives
▸ Compare hospital options (St. David's South Austin, Seton Medical Center, St. David's Women's Center)
▸ Explore Austin Area Birthing Center (midwife-led, waterbirth)
▸ Know what doula care actually costs ($1,000–$3,000)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Austin
0:13 — What This Guide Covers
0:32 — St. David's South Austin Medical Center (Level III NICU)
0:51 — Seton Medical Center Austin (Level III NICU)
1:09 — St. David's Women's Center of Texas (Level III NICU)
1:33 — Austin Area Birthing Center (Midwife-Led)
1:55 — Doulas & Midwives in Austin
2:15 — The True Joy Birthing App
2:38 — Cost Reality ($1,000–$3,000)
3:05 — Insurance & Texas Medicaid (SB 750)
3:34 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#austintxdoula #austintexasbirth #texasmedicaid #birthplan #doula #pregnancyaustin""",
        'tags': [
            'Austin TX doula', 'Austin Texas birth doula', 'Texas Medicaid doula',
            'Austin TX pregnancy guide', 'birth plan template', 'first time mom Austin TX',
            "St. David's South Austin maternity", 'Seton Medical Center Austin maternity',
            "St. David's Women's Center Texas", 'Austin Area Birthing Center',
            'Austin doula cost', 'Texas birth support', 'doula near me',
            'Austin midwife', 'pregnancy Texas', 'free birth plan',
            'doula services Austin', 'birth preparation', 'SB 750 doula coverage',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'conroe-tx': {
        'title': 'Conroe TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Conroe, Texas — now what? This guide walks you through everything: doulas and midwives serving Conroe, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Conroe doula directory → https://truejoybirthing.com/birth-support/conroe-tx/

▸ Find Conroe doulas & midwives (6 providers)
▸ Compare hospital options (HCA Houston Healthcare Conroe)
▸ Know what doula care actually costs ($800–$2,000)
▸ Understand Texas Medicaid doula coverage (SB 750)
▸ Explore birth centers (Journey Birth Center, Bliss Women's Wellness, Nativiti Family)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Conroe
0:13 — Where Conroe Families Deliver (HCA Houston Healthcare Conroe)
0:43 — Doulas & Midwives in Conroe (6 providers)
0:55 — The True Joy Birthing App
1:18 — Cost Reality ($800–$2,000)
1:43 — Insurance & Texas Medicaid (SB 750)
2:10 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#conroedoula #conroetxbirth #texasmedicaid #birthplan #doula #pregnancyconroe #montgomerycountydoula #sb750 #journeybirthcenter #hcahoustonconroe""",
        'tags': [
            'Conroe doula', 'Conroe birth doula', 'Montgomery County doula',
            'Texas doula', 'Conroe birth plan', 'HCA Houston Healthcare Conroe',
            'Journey Birth Center', 'Texas Medicaid doula', 'SB 750',
            'Conroe pregnancy', 'Conroe childbirth', 'Conroe hospital birth',
            'Texas birth doula', 'Conroe TX doula', 'first time mom',
            'birth plan', 'doula support', 'pregnancy guide',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'mckinney-tx': {
        'title': 'McKinney TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in McKinney — now what? This guide walks you through everything: doulas and midwives serving McKinney, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 McKinney doula directory → https://truejoybirthing.com/birth-support/mckinney-tx/

▸ Find McKinney doulas & midwives
▸ Compare hospital options (Baylor Scott & White McKinney, Medical City McKinney)
▸ Know what doula care actually costs ($950–$2,700)
▸ Understand Texas Medicaid doula coverage (SB 750)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to McKinney
0:13 — Baylor Scott & White McKinney (Level III NICU)
0:26 — Medical City McKinney (NICU)
0:39 — Little Lilacs Birth Services
0:53 — Amie Ivy Doula
1:07 — Babymoon Concierge
1:21 — The True Joy Birthing App
1:44 — Cost Reality ($950–$2,700)
2:09 — Insurance & Texas Medicaid
2:30 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#mckinneytxdoula #mckinneytexasbirth #texasmedicaid #birthplan #doula #pregnancymckinney""",
        'tags': [
            'McKinney TX doula', 'McKinney Texas birth doula', 'Texas Medicaid doula',
            'McKinney TX pregnancy guide', 'birth plan template', 'first time mom McKinney TX',
            'Baylor Scott & White McKinney maternity', 'Medical City McKinney maternity',
            'McKinney doula cost', 'Texas birth support',
            'doula near me', 'McKinney midwife', 'pregnancy Texas',
            'free birth plan', 'doula services McKinney', 'birth preparation',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'seattle-wa': {
        'title': 'Seattle Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Seattle — now what? This guide walks you through everything: doulas and midwives serving Seattle, hospital policies, real costs, and whether Washington Apple Health covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Seattle doula directory → https://truejoybirthing.com/birth-support/seattle-wa/

▸ Find Seattle doulas & midwives
▸ Compare hospital options (Swedish First Hill, UW Montlake, Overlake)
▸ Know what doula care actually costs ($1,500–$4,500)
▸ Understand Washington Apple Health doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Seattle
0:11 — Where Seattle Families Deliver (Hospitals)
1:24 — Doulas & Midwives in Seattle
1:56 — The True Joy Birthing App
2:19 — Cost Reality ($1,500–$4,500)
2:36 — Insurance & Washington Apple Health
3:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#seattledoula #seattlebirth #washingtonmedicaid #birthplan #doula #pregnancyseattle""",
        'tags': [
            'Seattle doula', 'Seattle birth doula', 'Washington Apple Health doula',
            'Seattle pregnancy guide', 'birth plan template', 'first time mom Seattle',
            'Seattle hospital maternity', 'Seattle doula cost', 'Washington birth support',
            'doula near me', 'Seattle midwife', 'pregnancy Washington',
            'free birth plan', 'doula services Seattle', 'birth preparation',
            'Swedish Medical Center Seattle', 'UW Medical Center Seattle',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'los-angeles-ca': {
        'title': 'Los Angeles Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Los Angeles — now what? This guide walks you through everything: doulas and midwives serving LA, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 LA doula directory → https://truejoybirthing.com/birth-support/los-angeles-ca/

▸ Find Los Angeles doulas & midwives
▸ Compare hospital options (Cedars-Sinai, UCLA Ronald Reagan, Kaiser West LA)
▸ Know what doula care actually costs ($1,800–$5,500)
▸ Understand California Medi-Cal doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Los Angeles
0:11 — Where LA Families Deliver (Hospitals)
1:24 — Doulas & Midwives in Los Angeles
1:56 — The True Joy Birthing App
2:19 — Cost Reality ($1,800–$5,500)
2:36 — Insurance & California Medi-Cal
3:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#losangelesdoula #labirth #californiamedicaid #birthplan #doula #pregnancyla""",
        'tags': [
            'Los Angeles doula', 'LA birth doula', 'California Medi-Cal doula',
            'Los Angeles pregnancy guide', 'birth plan template', 'first time mom LA',
            'Cedars-Sinai maternity', 'UCLA Ronald Reagan maternity', 'LA doula cost',
            'doula near me', 'Los Angeles midwife', 'pregnancy California',
            'free birth plan', 'doula services Los Angeles', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'san-antonio-tx': {
        'title': 'San Antonio Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in San Antonio — now what? This guide walks you through everything: doulas and midwives serving San Antonio, hospital policies, real costs, and Texas Medicaid options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 San Antonio doula directory → https://truejoybirthing.com/birth-support/san-antonio-tx/

▸ Find San Antonio doulas & midwives
▸ Compare hospital options (Methodist, University Hospital, Baptist Medical Center)
▸ Know what doula care actually costs ($700–$2,200)
▸ Understand Texas Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to San Antonio
0:11 — Where SA Families Deliver (Hospitals)
1:24 — Doulas & Midwives in San Antonio
1:56 — The True Joy Birthing App
2:19 — Cost Reality ($700–$2,200)
2:36 — Insurance & Texas Medicaid
3:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#sanantoniodoula #sabirth #texasmedicaid #birthplan #doula #pregnancysanantonio""",
        'tags': [
            'San Antonio doula', 'SA birth doula', 'Texas Medicaid doula',
            'San Antonio pregnancy guide', 'birth plan template', 'first time mom San Antonio',
            'Methodist Hospital San Antonio', 'University Hospital San Antonio', 'SA doula cost',
            'doula near me', 'San Antonio midwife', 'pregnancy Texas',
            'free birth plan', 'doula services San Antonio', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'philadelphia-pa': {
        'title': 'Philadelphia Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Philadelphia — now what? This guide walks you through everything: doulas and midwives serving Philly, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Philadelphia doula directory → https://truejoybirthing.com/birth-support/philadelphia-pa/

▸ Find Philadelphia doulas & midwives
▸ Compare hospital options (HUP, Jefferson, Temple, Einstein, Pennsylvania Hospital)
▸ Know what doula care actually costs ($800–$2,500)
▸ Understand Pennsylvania Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Philadelphia
0:11 — Where Philly Families Deliver (Hospitals)
1:24 — Doulas & Midwives in Philadelphia
1:56 — The True Joy Birthing App
2:19 — Cost Reality ($800–$2,500)
2:36 — Insurance & Pennsylvania Medicaid
3:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#philadelphiadoula #phillybirth #pennsylvaniadoula #birthplan #doula #pregnancyphilly""",
        'tags': [
            'Philadelphia doula', 'Philly birth doula', 'Pennsylvania doula',
            'Philadelphia pregnancy guide', 'birth plan template', 'first time mom Philadelphia',
            'HUP maternity', 'Jefferson Hospital maternity', 'Philly doula cost',
            'doula near me', 'Philadelphia midwife', 'pregnancy Pennsylvania',
            'free birth plan', 'doula services Philadelphia', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'atlanta-ga': {
        'title': 'Atlanta Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Atlanta — now what? This guide walks you through everything: doulas and midwives serving Atlanta, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Atlanta doula directory → https://truejoybirthing.com/birth-support/atlanta-ga/

▸ Find Atlanta doulas & midwives
▸ Compare hospital options (Northside, Emory Midtown, Piedmont)
▸ Know what doula care actually costs ($1,000–$3,000)
▸ Understand Georgia Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Atlanta
0:11 — Where Atlanta Families Deliver (Hospitals)
1:24 — Doulas & Midwives in Atlanta
1:56 — The True Joy Birthing App
2:19 — Cost Reality ($1,000–$3,000)
2:36 — Insurance & Georgia Medicaid
3:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#atlantadoula #atlantabirth #georgiamedicaid #birthplan #doula #pregnancyatlanta""",
        'tags': [
            'Atlanta doula', 'Atlanta birth doula', 'Georgia Medicaid doula',
            'Atlanta pregnancy guide', 'birth plan template', 'first time mom Atlanta',
            'Northside Hospital Atlanta maternity', 'Emory Midtown maternity', 'Atlanta doula cost',
            'doula near me', 'Atlanta midwife', 'pregnancy Georgia',
            'free birth plan', 'doula services Atlanta', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'baltimore-md': {
        'title': 'Baltimore Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Baltimore — now what? This guide walks you through everything: doulas and midwives serving Baltimore, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Baltimore doula directory → https://truejoybirthing.com/birth-support/baltimore-md/

▸ Find Baltimore doulas & midwives
▸ Compare hospital options (Johns Hopkins, UMMC, Sinai, MedStar Franklin Square)
▸ Know what doula care actually costs ($800–$2,200)
▸ Understand Maryland Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Baltimore
0:11 — Where Baltimore Families Deliver (Hospitals)
1:24 — Doulas & Midwives in Baltimore
1:56 — The True Joy Birthing App
2:19 — Cost Reality ($800–$2,200)
2:36 — Insurance & Maryland Medicaid
3:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#baltimoredoula #baltimorebirth #marylandmedicaid #birthplan #doula #pregnancybaltimore""",
        'tags': [
            'Baltimore doula', 'Baltimore birth doula', 'Maryland Medicaid doula',
            'Baltimore pregnancy guide', 'birth plan template', 'first time mom Baltimore',
            'Johns Hopkins maternity', 'UMMC maternity', 'Baltimore doula cost',
            'doula near me', 'Baltimore midwife', 'pregnancy Maryland',
            'free birth plan', 'doula services Baltimore', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'chicago-il': {
        'title': 'Chicago Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Chicago — now what? This guide walks you through everything: doulas and midwives serving Chicago, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Chicago doula directory → https://truejoybirthing.com/birth-support/chicago-il/

▸ Find Chicago doulas & midwives
▸ Compare hospital options (Northwestern Prentice, Rush, UChicago, Advocate Illinois Masonic)
▸ Know what doula care actually costs ($1,500–$5,000)
▸ Understand Illinois Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Chicago
0:11 — Where Chicago Families Deliver (Hospitals)
1:24 — Doulas & Midwives in Chicago
1:56 — The True Joy Birthing App
2:19 — Cost Reality ($1,500–$5,000)
2:36 — Insurance & Illinois Medicaid
3:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#chicagodoula #chicagobirth #illinoismedicaid #birthplan #doula #pregnancychicago""",
        'tags': [
            'Chicago doula', 'Chicago birth doula', 'Illinois Medicaid doula',
            'Chicago pregnancy guide', 'birth plan template', 'first time mom Chicago',
            'Northwestern Prentice maternity', 'Rush maternity', 'Chicago doula cost',
            'doula near me', 'Chicago midwife', 'pregnancy Illinois',
            'free birth plan', 'doula services Chicago', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'phoenix-az': {
        'title': 'Phoenix Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Phoenix — now what? This guide walks you through everything: doulas and midwives serving Phoenix, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Phoenix doula directory → https://truejoybirthing.com/birth-support/phoenix-az/

▸ Find Phoenix doulas & midwives
▸ Compare hospital options (Banner University, St. Joseph's, HonorHealth)
▸ Know what doula care actually costs ($1,200–$3,500)
▸ Understand Arizona Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Phoenix
0:12 — What We're Covering
0:29 — Banner University Medical Center Phoenix
0:49 — St. Joseph's Hospital (Dignity Health)
1:08 — HonorHealth Scottsdale Shea
1:27 — Natural Birth Center & Women's Wellness
1:50 — Doulas & Midwives Serving Phoenix
2:10 — The True Joy Birthing App
2:34 — Cost Reality ($1,200–$3,500)
2:57 — Insurance & Arizona Medicaid (AHCCCS)
3:21 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#phoenixdoula #phoenixbirth #arizonamedicaid #birthplan #doula #pregnancyphoenix""",
        'tags': [
            'Phoenix doula', 'Phoenix birth doula', 'Arizona Medicaid doula',
            'Phoenix pregnancy guide', 'birth plan template', 'first time mom Phoenix',
            'Banner University maternity', 'St. Joseph Phoenix maternity', 'Phoenix doula cost',
            'doula near me', 'Phoenix midwife', 'pregnancy Arizona',
            'free birth plan', 'doula services Phoenix', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'miami-fl': {
        'title': 'Miami Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Miami — now what? This guide walks you through everything: doulas and midwives serving Miami, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Miami doula directory → https://truejoybirthing.com/birth-support/miami-fl/

▸ Find Miami doulas & midwives
▸ Compare hospital options (Jackson Memorial, Mercy, Mount Sinai, Baptist Health)
▸ Know what doula care actually costs ($1,200–$3,500)
▸ Understand Florida Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Miami
0:11 — Where Miami Families Deliver (Hospitals)
1:24 — Doulas & Midwives in Miami
1:56 — The True Joy Birthing App
2:19 — Cost Reality ($1,200–$3,500)
2:36 — Insurance & Florida Medicaid
3:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#miamidoula #miamibirth #floridamedicaid #birthplan #doula #pregnancymiami""",
        'tags': [
            'Miami doula', 'Miami birth doula', 'Florida Medicaid doula',
            'Miami pregnancy guide', 'birth plan template', 'first time mom Miami',
            'Jackson Memorial maternity', 'Baptist Health Miami maternity', 'Miami doula cost',
            'doula near me', 'Miami midwife', 'pregnancy Florida',
            'free birth plan', 'doula services Miami', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'nashville-tn': {
        'title': 'Nashville Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Nashville — now what? This guide walks you through everything: doulas and midwives serving Nashville, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Nashville doula directory → https://truejoybirthing.com/birth-support/nashville-tn/

▸ Find Nashville doulas & midwives
▸ Compare hospital options (Vanderbilt, Ascension Saint Thomas, TriStar Centennial)
▸ Know what doula care actually costs ($1,200–$3,500)
▸ Understand Tennessee Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Nashville
0:11 — Where Nashville Families Deliver (Hospitals)
1:24 — Doulas & Midwives in Nashville
1:56 — The True Joy Birthing App
2:19 — Cost Reality ($1,200–$3,500)
2:36 — Insurance & Tennessee Medicaid
3:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital preparedness — all for free.

Created by Shelbi Kohler, certified birth doula.

#nashvilledoula #nashvillebirth #tennesseemedicaid #birthplan #doula #pregnancynashville""",
        'tags': [
            'Nashville doula', 'Nashville birth doula', 'Tennessee Medicaid doula',
            'Nashville pregnancy guide', 'birth plan template', 'first time mom Nashville',
            'Vanderbilt maternity', 'Saint Thomas Nashville maternity', 'Nashville doula cost',
            'doula near me', 'Nashville midwife', 'pregnancy Tennessee',
            'free birth plan', 'doula services Nashville', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'san-diego-ca': {
        'title': 'San Diego Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in San Diego — now what? This guide walks you through everything: doulas and midwives serving San Diego, hospital policies, real costs, and California's Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 San Diego doula directory → https://truejoybirthing.com/birth-support/san-diego-ca/

▸ Find San Diego doulas & midwives
▸ Compare hospital options (UCSD Jacobs, Sharp Mary Birch, Scripps Mercy, Palomar)
▸ Know what doula care actually costs ($1,500–$4,500)
▸ Understand California Medi-Cal doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to San Diego
0:11 — Where San Diego Families Deliver (Hospitals)
1:30 — Doulas & Midwives in San Diego
2:00 — The True Joy Birthing App
2:30 — Cost Reality ($1,500–$4,500)
2:50 — Insurance & California Medi-Cal
3:15 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#sandiegodoula #sandiegobirth #californiamedicaid #birthplan #doula #pregnancysandiego""",
        'tags': [
            'San Diego doula', 'San Diego birth doula', 'California Medi-Cal doula',
            'San Diego pregnancy guide', 'birth plan template', 'first time mom San Diego',
            'San Diego hospital maternity', 'San Diego doula cost', 'California birth support',
            'doula near me', 'San Diego midwife', 'pregnancy California',
            'free birth plan', 'doula services San Diego', 'birth preparation',
            'UCSD Jacobs Medical Center', 'Sharp Mary Birch Hospital', 'Scripps Mercy San Diego',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'detroit-mi': {
        'title': 'Detroit Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Detroit — now what? This guide walks you through everything: doulas and midwives serving Detroit, hospital policies, real costs, and Michigan Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Detroit doula directory → https://truejoybirthing.com/birth-support/detroit-mi/

▸ Find Detroit doulas & midwives
▸ Compare hospital options (DMC Hutzel, Henry Ford, Corewell Beaumont, Sinai-Grace)
▸ Know what doula care actually costs ($800–$3,000)
▸ Understand Michigan Medicaid doula coverage ($1,500/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Detroit
0:11 — Where Detroit Families Deliver (Hospitals)
1:30 — Doulas & Midwives in Detroit
2:00 — The True Joy Birthing App
2:30 — Cost Reality ($800–$3,000)
2:50 — Insurance & Michigan Medicaid
3:15 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#detroitdoula #detroitbirth #michiganmedicaid #birthplan #doula #pregnancydetroit""",
        'tags': [
            'Detroit doula', 'Detroit birth doula', 'Michigan Medicaid doula',
            'Detroit pregnancy guide', 'birth plan template', 'first time mom Detroit',
            'Detroit hospital maternity', 'Detroit doula cost', 'Michigan birth support',
            'doula near me', 'Detroit midwife', 'pregnancy Michigan',
            'free birth plan', 'doula services Detroit', 'birth preparation',
            'DMC Hutzel Womens Hospital', 'Henry Ford Hospital Detroit', 'Corewell Beaumont',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'las-vegas-nv': {
        'title': 'Las Vegas Doula & Birth Plan Guide: Costs, Hospitals & Insurance (First-Time Mom)',
        'description': """You just found out you're pregnant in Las Vegas — now what? This guide walks you through everything: doulas and midwives serving Las Vegas, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Las Vegas doula directory → https://truejoybirthing.com/birth-support/las-vegas-nv/

▸ Find Las Vegas doulas & midwives
▸ Compare hospital options (Sunrise, UMC, Summerlin, Centennial Hills)
▸ Know what doula care actually costs ($1,200–$3,500)
▸ Understand Nevada Medicaid and your insurance options
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Las Vegas
0:11 — Where Las Vegas Families Deliver (Hospitals)
1:30 — Doulas & Midwives in Las Vegas
2:00 — The True Joy Birthing App
2:30 — Cost Reality ($1,200–$3,500)
2:50 — Insurance & Nevada Medicaid
3:15 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#lasvegasdoula #lasvegasbirth #nevadamedicaid #birthplan #doula #pregnancylasvegas""",
        'tags': [
            'Las Vegas doula', 'Las Vegas birth doula', 'Nevada Medicaid doula',
            'Las Vegas pregnancy guide', 'birth plan template', 'first time mom Las Vegas',
            'Las Vegas hospital maternity', 'Las Vegas doula cost', 'Nevada birth support',
            'doula near me', 'Las Vegas midwife', 'pregnancy Nevada',
            'free birth plan', 'doula services Las Vegas', 'birth preparation',
            'Sunrise Hospital Las Vegas', 'UMC Las Vegas', 'Summerlin Hospital',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'minneapolis-mn': {
        'title': 'Minneapolis Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Minneapolis — now what? This guide walks you through everything: doulas and midwives serving Minneapolis, hospital policies, real costs, and whether Minnesota Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Minneapolis doula directory → https://truejoybirthing.com/birth-support/minneapolis-mn/

▸ Find Minneapolis doulas & midwives
▸ Compare hospital options (Abbott Northwestern, HCMC, M Health Fairview)
▸ Know what doula care actually costs ($1,500–$4,000)
▸ Understand Minnesota Medical Assistance doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Minneapolis
0:11 — Where Minneapolis Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Minneapolis
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,500–$4,000)
2:37 — Insurance & Minnesota Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#minneapolisdoula #minneapolisbirth #minnesotamedicaid #birthplan #doula #pregnancyminneapolis""",
        'tags': [
            'Minneapolis doula', 'Minneapolis birth doula', 'Minnesota Medicaid doula',
            'Minneapolis pregnancy guide', 'birth plan template', 'first time mom Minneapolis',
            'Abbott Northwestern maternity', 'HCMC maternity', 'Minneapolis doula cost',
            'Minnesota birth support', 'doula near me', 'Minneapolis midwife',
            'pregnancy Minnesota', 'free birth plan', 'doula services Minneapolis',
            'Twin Cities doula', 'Minneapolis birth guide',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'new-york-ny': {
        'title': 'New York City Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in New York City — now what? This guide walks you through everything: doulas and midwives serving NYC, hospital policies, real costs, and whether NY Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 NYC doula directory → https://truejoybirthing.com/birth-support/new-york-ny/

▸ Find NYC doulas & midwives
▸ Compare hospital options (Columbia, NYU Langone, Mount Sinai, Elmhurst)
▸ Know what doula care actually costs ($1,500–$5,000)
▸ Understand NY Medicaid doula coverage ($1,710/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to New York City
0:11 — Where NYC Families Deliver (Hospitals)
1:06 — Doulas & Midwives in NYC
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,500–$5,000)
2:37 — Insurance & New York Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#nycdoula #nycbirth #newyorkmedicaid #birthplan #doula #pregnancynyc""",
        'tags': [
            'NYC doula', 'New York City birth doula', 'New York Medicaid doula',
            'NYC pregnancy guide', 'birth plan template', 'first time mom NYC',
            'Columbia Presbyterian maternity', 'NYU Langone maternity', 'Mount Sinai maternity',
            'NYC doula cost', 'New York birth support',
            'doula near me', 'NYC midwife', 'pregnancy New York',
            'free birth plan', 'doula services NYC', 'birth preparation',
            'Elmhurst Hospital', 'NYC birth guide',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'pittsburgh-pa': {
        'title': 'Pittsburgh Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Pittsburgh — now what? This guide walks you through everything: doulas and midwives serving Pittsburgh, hospital policies, real costs, and whether Pennsylvania Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Pittsburgh doula directory → https://truejoybirthing.com/birth-support/pittsburgh-pa/

▸ Find Pittsburgh doulas & midwives
▸ Compare hospital options (Magee-Womens, UPMC Children's, Allegheny General)
▸ Know what doula care actually costs ($700–$2,000)
▸ Understand PA Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Pittsburgh
0:11 — Where Pittsburgh Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Pittsburgh
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($700–$2,000)
2:37 — Insurance & Pennsylvania Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#pittsburghdoula #pittsburghbirth #pennsylvaniamedicaid #birthplan #doula #pregnancypittsburgh""",
        'tags': [
            'Pittsburgh doula', 'Pittsburgh birth doula', 'Pennsylvania Medicaid doula',
            'Pittsburgh pregnancy guide', 'birth plan template', 'first time mom Pittsburgh',
            'Magee-Womens maternity', 'UPMC maternity', 'Allegheny General maternity',
            'Pittsburgh doula cost', 'Pennsylvania birth support',
            'doula near me', 'Pittsburgh midwife', 'pregnancy Pennsylvania',
            'free birth plan', 'doula services Pittsburgh', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'sacramento-ca': {
        'title': 'Sacramento Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Sacramento — now what? This guide walks you through everything: doulas and midwives serving Sacramento, hospital policies, real costs, and whether California's Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Sacramento doula directory → https://truejoybirthing.com/birth-support/sacramento-ca/

▸ Find Sacramento doulas & midwives
▸ Compare hospital options (UC Davis, Sutter Medical Center, Mercy General)
▸ Know what doula care actually costs ($1,500–$4,000)
▸ Understand California Medi-Cal PAVE doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Sacramento
0:11 — Where Sacramento Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Sacramento
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,500–$4,000)
2:37 — Insurance & California Medi-Cal
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#sacramentodoula #sacramentobirth #californiamedicaid #birthplan #doula #pregnancysacramento""",
        'tags': [
            'Sacramento doula', 'Sacramento birth doula', 'California Medi-Cal doula',
            'Sacramento pregnancy guide', 'birth plan template', 'first time mom Sacramento',
            'UC Davis Medical Center maternity', 'Sutter Medical Center maternity', 'Mercy General maternity',
            'Sacramento doula cost', 'California birth support',
            'doula near me', 'Sacramento midwife', 'pregnancy California',
            'free birth plan', 'doula services Sacramento', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'colorado-springs-co': {
        'title': 'Colorado Springs Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Colorado Springs — now what? This guide walks you through everything: doulas and midwives serving Colorado Springs, hospital policies, real costs, and whether Colorado Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Colorado Springs doula directory → https://truejoybirthing.com/birth-support/colorado-springs-co/

▸ Find Colorado Springs doulas & midwives
▸ Compare hospital options (UCHealth Memorial, Penrose, Evans Army)
▸ Know what doula care actually costs ($800–$2,500)
▸ Understand Colorado Health First doula coverage ($750/birth)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Colorado Springs
0:11 — Where Colorado Springs Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Colorado Springs
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($800–$2,500)
2:37 — Insurance & Colorado Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#coloradospringsdoula #coloradospringsbirth #coloradomedicaid #birthplan #doula #pregnancycos""",
        'tags': [
            'Colorado Springs doula', 'Colorado Springs birth doula', 'Colorado Medicaid doula',
            'Colorado Springs pregnancy guide', 'birth plan template', 'first time mom Colorado Springs',
            'UCHealth Memorial maternity', 'Penrose Hospital maternity', 'Colorado Springs doula cost',
            'Colorado birth support', 'doula near me', 'Colorado Springs midwife',
            'pregnancy Colorado', 'free birth plan', 'doula services Colorado Springs',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'meridian-id': {
        'title': 'Meridian ID Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Meridian, Idaho — now what? This guide walks you through everything: doulas and midwives serving Meridian, hospital policies, real costs, and whether Idaho Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Meridian doula directory → https://truejoybirthing.com/birth-support/meridian-id/

▸ Find Meridian doulas & midwives
▸ Compare hospital options (St. Luke's Meridian, St. Luke's Nampa, St. Luke's Boise)
▸ Know what doula care actually costs ($900–$1,800)
▸ Understand Idaho Medicaid (does not cover doulas)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Meridian
0:11 — Where Meridian Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Meridian
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($900–$1,800)
2:37 — Insurance & Idaho Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#meridianidahodoula #meridianbirth #idahomedicaid #birthplan #doula #pregnancymeridian""",
        'tags': [
            'Meridian ID doula', 'Meridian Idaho birth doula', 'Idaho Medicaid doula',
            'Meridian pregnancy guide', 'birth plan template', 'first time mom Meridian',
            'St. Luke\'s Meridian maternity', 'St. Luke\'s Boise maternity', 'Meridian doula cost',
            'Idaho birth support', 'doula near me', 'Meridian midwife',
            'pregnancy Idaho', 'free birth plan', 'doula services Meridian',
            'Treasure Valley doula', 'Boise area doula',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'portland-or': {
        'title': 'Portland Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Portland — now what? This guide walks you through everything: doulas and midwives serving Portland, hospital policies, real costs, and whether Oregon Health Plan covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Portland doula directory → https://truejoybirthing.com/birth-support/portland-or/

▸ Find Portland doulas & midwives
▸ Compare hospital options (OHSU, Providence St. Vincent, Legacy Emanuel)
▸ Know what doula care actually costs ($1,500–$4,500)
▸ Understand Oregon Health Plan doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Portland
0:11 — Where Portland Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Portland
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,500–$4,500)
2:37 — Insurance & Oregon Health Plan
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#portlanddoula #portlandbirth #oregonhealthplan #birthplan #doula #pregnancyportland""",
        'tags': [
            'Portland doula', 'Portland birth doula', 'Oregon Health Plan doula',
            'Portland pregnancy guide', 'birth plan template', 'first time mom Portland',
            'OHSU maternity', 'Providence St. Vincent maternity', 'Legacy Emanuel maternity',
            'Portland doula cost', 'Oregon birth support',
            'doula near me', 'Portland midwife', 'pregnancy Oregon',
            'free birth plan', 'doula services Portland', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'providence-ri': {
        'title': 'Providence RI Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Providence, Rhode Island — now what? This guide walks you through everything: doulas and midwives serving Providence, hospital policies, real costs, and whether RI Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Providence doula directory → https://truejoybirthing.com/birth-support/providence-ri/

▸ Find Providence doulas & midwives
▸ Compare hospital options (Women & Infants, Roger Williams, Hasbro Children's)
▸ Know what doula care actually costs ($800–$1,800)
▸ Understand RI Medicaid doula coverage (since July 2023)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Providence
0:11 — Where Providence Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Providence
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($800–$1,800)
2:37 — Insurance & Rhode Island Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#provencedoula #providencebirth #rhodeislandmedicaid #birthplan #doula #pregnancyprovidence""",
        'tags': [
            'Providence RI doula', 'Providence Rhode Island birth doula', 'Rhode Island Medicaid doula',
            'Providence pregnancy guide', 'birth plan template', 'first time mom Providence',
            'Women & Infants Hospital maternity', 'Roger Williams maternity', 'Providence doula cost',
            'Rhode Island birth support', 'doula near me', 'Providence midwife',
            'pregnancy Rhode Island', 'free birth plan', 'doula services Providence',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'raleigh-nc': {
        'title': 'Raleigh Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Raleigh — now what? This guide walks you through everything: doulas and midwives serving Raleigh, hospital policies, real costs, and whether NC Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Raleigh doula directory → https://truejoybirthing.com/birth-support/raleigh-nc/

▸ Find Raleigh doulas & midwives
▸ Compare hospital options (WakeMed Raleigh, UNC REX, Duke Regional)
▸ Know what doula care actually costs ($850–$2,300)
▸ Understand NC Medicaid doula coverage (since Oct 2024)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Raleigh
0:11 — Where Raleigh Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Raleigh
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($850–$2,300)
2:37 — Insurance & North Carolina Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#raleighdoula #raleighbirth #ncmedicaid #birthplan #doula #pregnancyraleigh""",
        'tags': [
            'Raleigh doula', 'Raleigh birth doula', 'North Carolina Medicaid doula',
            'Raleigh pregnancy guide', 'birth plan template', 'first time mom Raleigh',
            'WakeMed Raleigh maternity', 'UNC REX maternity', 'Duke Regional maternity',
            'Raleigh doula cost', 'North Carolina birth support',
            'doula near me', 'Raleigh midwife', 'pregnancy North Carolina',
            'free birth plan', 'doula services Raleigh', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'augusta-ga': {
        'title': 'Augusta GA Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Augusta, Georgia — now what? This guide walks you through everything: doulas and midwives serving Augusta, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Augusta doula directory → https://truejoybirthing.com/birth-support/augusta-ga/

▸ Find Augusta doulas & midwives
▸ Compare hospital options (Piedmont Augusta, AU Health, Doctors Hospital)
▸ Know what doula care actually costs ($1,200–$3,500)
▸ Understand Georgia Medicaid and your insurance options
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Augusta
0:11 — Where Augusta Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Augusta
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,200–$3,500)
2:37 — Insurance & Georgia Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#augustadoula #augustagabirth #georgiamedicaid #birthplan #doula #pregnancyaugusta""",
        'tags': [
            'Augusta GA doula', 'Augusta birth doula', 'Georgia Medicaid doula',
            'Augusta pregnancy guide', 'birth plan template', 'first time mom Augusta',
            'Piedmont Augusta maternity', 'AU Health maternity', 'Doctors Hospital Augusta',
            'Augusta doula cost', 'Georgia birth support',
            'doula near me', 'Augusta midwife', 'pregnancy Georgia',
            'free birth plan', 'doula services Augusta', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'el-paso-tx': {
        'title': 'El Paso Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in El Paso — now what? This guide walks you through everything: doulas and midwives serving El Paso, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 El Paso doula directory → https://truejoybirthing.com/birth-support/el-paso-tx/

▸ Find El Paso doulas & midwives (5 doulas)
▸ Compare hospital options (Las Palmas, Del Sol, Providence, UMC El Paso)
▸ Luna Tierra Casa de Partos — bilingual birth center
▸ Know what doula care actually costs ($800–$2,200)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to El Paso
0:14 — Where El Paso Families Deliver (Hospitals)
0:33 — University Medical Center of El Paso
0:42 — Las Palmas Medical Center
0:51 — Del Sol Medical Center
1:01 — Luna Tierra Casa de Partos (Birth Center)
1:13 — 5 Doulas Serving El Paso
1:26 — The True Joy Birthing App
1:50 — Cost Reality ($800–$2,200)
2:12 — Insurance & Texas Medicaid (SB 750)
2:31 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#elpasodoula #elpasotxbirth #texasmedicaid #birthplan #doula #pregnancyelpaso""",
        'tags': [
            'El Paso doula', 'El Paso birth doula', 'Texas Medicaid doula',
            'El Paso pregnancy guide', 'birth plan template', 'first time mom El Paso',
            'Las Palmas El Paso maternity', 'Del Sol Medical Center maternity',
            'El Paso doula cost', 'Texas birth support',
            'doula near me', 'El Paso midwife', 'pregnancy Texas',
            'free birth plan', 'doula services El Paso', 'birth preparation',
            'UMC El Paso', 'Providence El Paso',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'fort-worth-tx': {
        'title': 'Fort Worth Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Fort Worth — now what? This guide walks you through everything: doulas and midwives serving Fort Worth, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Fort Worth doula directory → https://truejoybirthing.com/birth-support/fort-worth-tx/

▸ Find Fort Worth doulas & midwives
▸ Compare hospital options (Texas Health Harris, Cook Children's, Baylor Scott & White)
▸ Know what doula care actually costs ($850–$2,600)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Fort Worth
0:11 — Where Fort Worth Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Fort Worth
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($850–$2,600)
2:37 — Insurance & Texas Medicaid (SB 750)
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#fortworthdoula #fortworthbirth #texasmedicaid #birthplan #doula #pregnancyfortworth""",
        'tags': [
            'Fort Worth doula', 'Fort Worth birth doula', 'Texas Medicaid doula',
            'Fort Worth pregnancy guide', 'birth plan template', 'first time mom Fort Worth',
            'Texas Health Harris maternity', 'Cook Childrens maternity', 'Baylor Fort Worth maternity',
            'Fort Worth doula cost', 'Texas birth support',
            'doula near me', 'Fort Worth midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Fort Worth', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'fresno-ca': {
        'title': 'Fresno Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Fresno — now what? This guide walks you through everything: doulas and midwives serving Fresno, hospital policies, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Fresno doula directory → https://truejoybirthing.com/birth-support/fresno-ca/

▸ Find Fresno doulas & midwives
▸ Compare hospital options (Community Regional, Saint Agnes, Kaiser Fresno)
▸ Know what doula care actually costs ($1,000–$3,000)
▸ Understand California Medi-Cal PAVE doula coverage ($1,587/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Fresno
0:11 — Where Fresno Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Fresno
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,000–$3,000)
2:37 — Insurance & California Medi-Cal
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#fresnodoula #fresnobirth #californiamedicaid #birthplan #doula #pregnancyfresno""",
        'tags': [
            'Fresno doula', 'Fresno birth doula', 'California Medi-Cal doula',
            'Fresno pregnancy guide', 'birth plan template', 'first time mom Fresno',
            'Community Regional Fresno maternity', 'Saint Agnes Fresno maternity',
            'Fresno doula cost', 'California birth support',
            'doula near me', 'Fresno midwife', 'pregnancy California',
            'free birth plan', 'doula services Fresno', 'birth preparation',
            'Kaiser Fresno maternity',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'plano-tx': {
        'title': 'Plano Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Plano — now what? This guide walks you through everything: doulas and midwives serving Plano, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Plano doula directory → https://truejoybirthing.com/birth-support/plano-tx/

▸ Find Plano doulas & midwives
▸ Compare hospital options (Texas Health Plano, Medical City Plano, Baylor Scott & White)
▸ Know what doula care actually costs ($1,000–$2,800)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Plano
0:11 — Where Plano Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Plano
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,000–$2,800)
2:37 — Insurance & Texas Medicaid (SB 750)
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#planodoula #planotxbirth #texasmedicaid #birthplan #doula #pregnancyplano""",
        'tags': [
            'Plano doula', 'Plano birth doula', 'Texas Medicaid doula',
            'Plano pregnancy guide', 'birth plan template', 'first time mom Plano',
            'Texas Health Plano maternity', 'Medical City Plano maternity', 'Baylor Plano maternity',
            'Plano doula cost', 'Texas birth support',
            'doula near me', 'Plano midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Plano', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'san-francisco-ca': {
        'title': 'San Francisco Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in San Francisco — now what? This guide walks you through everything: doulas and midwives serving San Francisco, hospital policies, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 San Francisco doula directory → https://truejoybirthing.com/birth-support/san-francisco-ca/

▸ Find San Francisco doulas & midwives
▸ Compare hospital options (UCSF Mission Bay, CPMC, Zuckerberg SF General)
▸ Know what doula care actually costs ($1,800–$3,500)
▸ Understand California Medi-Cal PAVE doula coverage ($1,587/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to San Francisco
0:11 — Where San Francisco Families Deliver (Hospitals)
1:06 — Doulas & Midwives in San Francisco
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,800–$3,500)
2:37 — Insurance & California Medi-Cal
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#sanfranciscodoula #sanfranciscobirth #californiamedicaid #birthplan #doula #pregnancysf""",
        'tags': [
            'San Francisco doula', 'San Francisco birth doula', 'California Medi-Cal doula',
            'San Francisco pregnancy guide', 'birth plan template', 'first time mom San Francisco',
            'UCSF Mission Bay maternity', 'CPMC maternity', 'Zuckerberg SF General maternity',
            'San Francisco doula cost', 'California birth support',
            'doula near me', 'San Francisco midwife', 'pregnancy California',
            'free birth plan', 'doula services San Francisco', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'san-jose-ca': {
        'title': 'San Jose Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in San Jose — now what? This guide walks you through everything: doulas and midwives serving San Jose, hospital policies, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 San Jose doula directory → https://truejoybirthing.com/birth-support/san-jose-ca/

▸ Find San Jose doulas & midwives
▸ Compare hospital options (Regional Medical Center, Good Samaritan, Kaiser Santa Clara)
▸ Know what doula care actually costs ($1,500–$3,000)
▸ Understand California Medi-Cal PAVE doula coverage ($1,587/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to San Jose
0:11 — Where San Jose Families Deliver (Hospitals)
1:06 — Doulas & Midwives in San Jose
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,500–$3,000)
2:37 — Insurance & California Medi-Cal
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#sanjosedoula #sanjosecabirth #californiamedicaid #birthplan #doula #pregnancysanjose""",
        'tags': [
            'San Jose doula', 'San Jose birth doula', 'California Medi-Cal doula',
            'San Jose pregnancy guide', 'birth plan template', 'first time mom San Jose',
            'Regional Medical Center San Jose maternity', 'Good Samaritan San Jose maternity',
            'San Jose doula cost', 'California birth support',
            'doula near me', 'San Jose midwife', 'pregnancy California',
            'free birth plan', 'doula services San Jose', 'birth preparation',
            'Kaiser Santa Clara maternity',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'spokane-wa': {
        'title': 'Spokane Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Spokane — now what? This guide walks you through everything: doulas and midwives serving Spokane, hospital policies, real costs, and whether Washington Apple Health covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Spokane doula directory → https://truejoybirthing.com/birth-support/spokane-wa/

▸ Find Spokane doulas & midwives
▸ Compare hospital options (Providence Sacred Heart, MultiCare Deaconess, Valley Hospital)
▸ Know what doula care actually costs ($1,300–$3,800)
▸ Understand Washington Apple Health doula coverage ($1,500/birth)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Spokane
0:11 — Where Spokane Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Spokane
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,300–$3,800)
2:37 — Insurance & Washington Apple Health
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#spokanedoula #spokanebirth #washingtonmedicaid #birthplan #doula #pregnancyspokane""",
        'tags': [
            'Spokane doula', 'Spokane birth doula', 'Washington Apple Health doula',
            'Spokane pregnancy guide', 'birth plan template', 'first time mom Spokane',
            'Providence Sacred Heart maternity', 'MultiCare Deaconess maternity',
            'Spokane doula cost', 'Washington birth support',
            'doula near me', 'Spokane midwife', 'pregnancy Washington',
            'free birth plan', 'doula services Spokane', 'birth preparation',
            'Valley Hospital Spokane',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'spring-tx': {
        'title': 'Spring TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Spring, Texas — now what? This guide walks you through everything: doulas and midwives serving Spring, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Spring doula directory → https://truejoybirthing.com/birth-support/spring-tx/

▸ Find Spring doulas & midwives
▸ Compare hospital options (HCA Houston North, Memorial Hermann The Woodlands)
▸ Know what doula care actually costs ($1,000–$2,800)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Spring
0:11 — Where Spring Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Spring
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,000–$2,800)
2:37 — Insurance & Texas Medicaid (SB 750)
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#springtxdoula #springtexasbirth #texasmedicaid #birthplan #doula #pregnancyspringtx""",
        'tags': [
            'Spring TX doula', 'Spring Texas birth doula', 'Texas Medicaid doula',
            'Spring TX pregnancy guide', 'birth plan template', 'first time mom Spring TX',
            'HCA Houston North maternity', 'Memorial Hermann The Woodlands maternity',
            'Spring doula cost', 'Texas birth support',
            'doula near me', 'Spring TX midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Spring TX', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'st-paul-mn': {
        'title': 'St. Paul Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in St. Paul — now what? This guide walks you through everything: doulas and midwives serving St. Paul, hospital policies, real costs, and whether Minnesota Medical Assistance covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 St. Paul doula directory → https://truejoybirthing.com/birth-support/st-paul-mn/

▸ Find St. Paul doulas & midwives
▸ Compare hospital options (Regions Hospital, United Hospital, Children's Minnesota)
▸ Know what doula care actually costs ($1,200–$3,500)
▸ Understand Minnesota Medical Assistance doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to St. Paul
0:11 — Where St. Paul Families Deliver (Hospitals)
1:06 — Doulas & Midwives in St. Paul
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($1,200–$3,500)
2:37 — Insurance & Minnesota Medical Assistance
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#stpauldoula #stpaulmnbirth #minnesotamedicaid #birthplan #doula #pregnancystpaul""",
        'tags': [
            'St. Paul doula', 'St. Paul birth doula', 'Minnesota Medicaid doula',
            'St. Paul pregnancy guide', 'birth plan template', 'first time mom St. Paul',
            'Regions Hospital maternity', 'United Hospital maternity', 'Childrens Minnesota',
            'St. Paul doula cost', 'Minnesota birth support',
            'doula near me', 'St. Paul midwife', 'pregnancy Minnesota',
            'free birth plan', 'doula services St. Paul', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'arlington-tx': {
        'title': 'Arlington Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Arlington — now what? This guide walks you through everything: doulas and midwives serving Arlington, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Arlington doula directory → https://truejoybirthing.com/birth-support/arlington-tx/

▸ Find Arlington doulas & midwives (7 providers)
▸ Compare hospital options (Medical City Arlington, Texas Health Arlington Memorial)
▸ Know what doula care actually costs ($850–$2,500)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Birth & Wellness Center of Arlington — birth center across from the hospital
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Arlington
0:11 — Where Arlington Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Arlington
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($850–$2,500)
2:37 — Insurance & Texas Medicaid (SB 750)
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#arlingtontxdoula #arlingtonbirth #texasmedicaid #birthplan #doula #pregnancyarlington #dfwdoula #tarrantcounty""",
        'tags': [
            'Arlington doula', 'Arlington birth doula', 'Texas Medicaid doula',
            'Arlington pregnancy guide', 'birth plan template', 'first time mom Arlington',
            'Medical City Arlington maternity', 'Texas Health Arlington Memorial maternity',
            'Arlington doula cost', 'Texas birth support',
            'doula near me', 'Arlington midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Arlington', 'birth preparation',
            'DFW doula', 'Tarrant County doula', 'birth center Arlington',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'charlotte-nc': {
        'title': 'Charlotte NC Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Charlotte, North Carolina — now what? This guide walks you through everything: doulas and midwives serving Charlotte, hospital policies, real costs, and whether North Carolina Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Charlotte doula directory → https://truejoybirthing.com/birth-support/charlotte-nc/

▸ Find Charlotte doulas & midwives
▸ Compare hospital options (Atrium Health, Novant Health Presbyterian)
▸ Know what doula care actually costs ($900–$2,500)
▸ Understand North Carolina Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Charlotte
0:11 — Where Charlotte Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Charlotte
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($900–$2,500)
2:37 — Insurance & North Carolina Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#charlottedoula #charlottencbirth #northcarolinamedicaid #birthplan #doula #pregnancycharlotte""",
        'tags': [
            'Charlotte NC doula', 'Charlotte birth doula', 'North Carolina Medicaid doula',
            'Charlotte pregnancy guide', 'birth plan template', 'first time mom Charlotte',
            'Atrium Health maternity', 'Novant Health Presbyterian maternity',
            'Charlotte doula cost', 'North Carolina birth support',
            'doula near me', 'Charlotte midwife', 'pregnancy North Carolina',
            'free birth plan', 'doula services Charlotte', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'orlando-fl': {
        'title': 'Orlando Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Orlando - now what? This guide walks you through everything: doulas and midwives serving Orlando, hospital policies, real costs, and whether Florida Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Orlando doula directory → https://truejoybirthing.com/birth-support/orlando-fl/

▸ Find Orlando doulas & midwives
▸ Compare hospital options (Winnie Palmer, AdventHealth, Osceola Regional)
▸ Know what doula care actually costs ($850-$2,500)
▸ Understand Florida Medicaid doula coverage (not currently covered)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 - Welcome to Orlando
0:12 - What This Guide Covers
0:28 - Winnie Palmer Hospital
0:44 - AdventHealth Orlando
1:02 - Osceola Regional Medical Center
1:16 - In Joy Birth
1:38 - Childbirth Concierge
1:59 - Zory Soto
2:21 - The Mothered Momma Doula
2:41 - The True Joy Birthing App
3:04 - Cost Reality ($850-$2,500)
3:23 - Insurance & Florida Medicaid
3:51 - Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared - all for free.

Created by Shelbi Kohler, certified birth doula.

#orlandodoula #orlandobirth #floridamedicaid #birthplan #doula #pregnancyorlando""",
        'tags': [
            'Orlando doula', 'Orlando birth doula', 'Florida Medicaid doula',
            'Orlando pregnancy guide', 'birth plan template', 'first time mom Orlando',
            'Winnie Palmer maternity', 'AdventHealth Orlando maternity',
            'Orlando doula cost', 'Florida birth support',
            'doula near me', 'Orlando midwife', 'pregnancy Florida',
            'free birth plan', 'doula services Orlando', 'birth preparation',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'tampa-fl': {
        'title': 'Tampa Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Tampa - now what? This guide walks you through everything: doulas and midwives serving Tampa, hospital policies, real costs, and whether Florida Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Tampa doula directory → https://truejoybirthing.com/birth-support/tampa-fl/

▸ Find Tampa doulas & midwives
▸ Compare hospital options (Tampa General, St. Joseph's Women's, AdventHealth)
▸ Know what doula care actually costs ($900-$2,800)
▸ Understand Florida Medicaid doula coverage (not currently covered)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 - Welcome to Tampa
0:12 - What This Guide Covers
0:30 - Tampa General Hospital
0:55 - BayCare St. Joseph's Women's Hospital
1:12 - AdventHealth Tampa
1:32 - One Love Doula
2:01 - Buddha Belly Doulas
2:27 - Tanya Grazione (Roar Like A Mama)
2:55 - Dee Larkin (Firm Foundation Doula Co.)
3:22 - Barefoot Birth
3:46 - The True Joy Birthing App
4:10 - Cost Reality ($900-$2,800)
4:33 - Insurance & Florida Medicaid
5:08 - Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared - all for free.

Created by Shelbi Kohler, certified birth doula.

#tampadoula #tampabirth #floridamedicaid #birthplan #doula #pregnancytampa""",
        'tags': [
            'Tampa doula', 'Tampa birth doula', 'Florida Medicaid doula',
            'Tampa pregnancy guide', 'birth plan template', 'first time mom Tampa',
            'Tampa General Hospital maternity', 'St. Josephs Womens Hospital Tampa',
            'AdventHealth Tampa maternity', 'Tampa doula cost',
            'doula near me', 'Tampa midwife', 'pregnancy Florida',
            'free birth plan', 'doula services Tampa', 'birth preparation',
        ],
        'category_id': '27',
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


def run_content_gate(slug):
    """Run the content accuracy audit as a pre-upload gate.
    Blocks upload if high-severity issues are found."""
    import subprocess
    audit_script = os.path.join(PROJECT_DIR, 'scripts', 'audit-video-quality.py')
    if not os.path.exists(audit_script):
        print("  ⚠️  audit-video-quality.py not found — skipping content gate")
        return True

    result = subprocess.run(
        ['python3', audit_script, '--slug', slug, '--json'],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        # Script errored — don't block upload, just warn
        print("  ⚠️  Content audit script errored — skipping gate")
        return True

    try:
        data = json.loads(result.stdout)
        city_data = data.get(slug, {})
        issues = city_data.get('issues', [])
    except (json.JSONDecodeError, KeyError):
        print("  ⚠️  Content audit output parse error — skipping gate")
        return True

    high_issues = [i for i in issues if i.get('severity') == 'high']
    med_issues = [i for i in issues if i.get('severity') == 'medium']

    if not high_issues and not med_issues:
        print("  ✅ Content accuracy gate: PASS (0 issues)")
        return True

    if high_issues:
        print(f"  ❌ Content accuracy gate: FAIL ({len(high_issues)} high, {len(med_issues)} medium)")
        print("  HIGH SEVERITY ISSUES — must fix before upload:")
        for issue in high_issues:
            print(f"    [{issue['check']}] {issue['scene']}: {issue['message']}")
        print("\n  Run: python3 scripts/audit-video-quality.py --slug", slug)
        print("  Fix the high-severity issues, then re-run the upload.\n")
        return False

    # Only medium issues — warn but allow
    print(f"  ⚠️  Content accuracy gate: {len(med_issues)} medium issue(s) — review recommended")
    for issue in med_issues:
        print(f"    [{issue['check']}] {issue['scene']}: {issue['message']}")
    return True


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

    # ─── Pre-upload content accuracy gate ───
    print("\n  Running content accuracy gate...")
    if not run_content_gate(slug):
        print(f"\n❌ Upload BLOCKED — fix high-severity content issues first.")
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