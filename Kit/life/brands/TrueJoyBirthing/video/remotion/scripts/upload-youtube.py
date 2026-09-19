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
import os, sys, json, re, time, subprocess

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
    """Extract state abbreviation from slug (e.g. 'denver-co' â 'CO')."""
    parts = slug.rsplit('-', 1)
    if len(parts) == 2 and parts[1].upper() in STATE_NAMES:
        return parts[1].upper()
    return None


def get_state_name(slug):
    """Get full state name from slug."""
    abbr = parse_state(slug)
    if abbr is None:
        return ''
    return STATE_NAMES.get(abbr, '')


# ─── City metadata ───
CITY_META = {
    'milwaukee-wi': {
        'title': 'Milwaukee Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Milwaukee — now what? This guide walks you through everything: doulas and midwives serving Milwaukee, hospital policies, real costs, and how to get free doula support through the city's BOMB program.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Milwaukee doula directory → https://truejoybirthing.com/birth-support/milwaukee-wi/

▸ Find Milwaukee doulas & midwives (5 providers)
▸ Compare hospital options (Froedtert, Aurora Sinai, Columbia St. Mary's)
▸ Know what doula care actually costs ($800–$1,600)
▸ Understand Wisconsin Medicaid doula coverage + the free BOMB Doula Program
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Milwaukee
0:17 — Where Milwaukee Families Deliver (Hospitals)
0:35 — Froedtert Hospital (Level IV NICU)
0:59 — Aurora Sinai Medical Center (Level III NICU)
1:22 — Ascension Columbia St. Mary's (Level III NICU)
1:44 — Authentic Birth Center (Wauwatosa)
2:13 — Doulas & Midwives in Milwaukee
3:52 — The True Joy Birthing App
4:16 — Cost Reality ($800–$1,600)
4:37 — Insurance & Wisconsin Medicaid
5:04 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#milwaukeedoula #milwaukeebirth #wisconsinmedicaid #birthplan #doula #pregnancymilwaukee""",
        'tags': [
            'Milwaukee doula', 'Milwaukee birth doula', 'Wisconsin Medicaid doula',
            'Milwaukee pregnancy guide', 'birth plan template', 'first time mom Milwaukee',
            'Milwaukee hospital maternity', 'Milwaukee doula cost', 'Wisconsin birth support',
            'doula near me', 'Milwaukee midwife', 'pregnancy Wisconsin',
            'free birth plan', 'doula services Milwaukee', 'birth preparation',
            'Froedtert Hospital', 'Aurora Sinai Medical Center', 'Ascension Columbia St. Marys',
            'Authentic Birth Center', 'BOMB Doula Program',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'houston-tx': {
        'title': 'Houston Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Houston — now what? This guide walks you through everything: doulas and midwives serving Houston, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Houston doula directory → https://truejoybirthing.com/birth-support/houston-tx/

▸ Find Houston doulas & midwives (9 providers)
▸ Compare hospital options (Woman's Hospital, Texas Children's Pavilion, Memorial Hermann)
▸ Know what doula care actually costs ($600–$5,000)
▸ Understand Texas Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Houston
0:11 — Where Houston Families Deliver (Hospitals)
0:29 — The Woman's Hospital of Texas (Level IV NICU)
1:01 — Texas Children's Pavilion for Women (Level IV NICU)
1:30 — Memorial Hermann Memorial City (Level III NICU)
1:55 — Doulas & Midwives in Houston
2:12 — The True Joy Birthing App
2:34 — Cost Reality ($600–$5,000)
2:58 — Insurance & Texas Medicaid
3:18 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#houstondoula #houstonbirth #texasmedicaid #birthplan #doula #pregnancyhouston""",
        'tags': [
            'Houston doula', 'Houston birth doula', 'Texas Medicaid doula',
            'Houston pregnancy guide', 'birth plan template', 'first time mom Houston',
            'Houston hospital maternity', 'Houston doula cost', 'Texas birth support',
            'doula near me', 'Houston midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Houston', 'birth preparation',
            "Woman's Hospital of Texas", "Texas Children's Pavilion for Women",
            'Memorial Hermann Memorial City', 'HCA Houston Healthcare',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'cedar-park-tx': {
        'title': 'Cedar Park Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Cedar Park â now what? This guide walks you through everything: doulas and midwives serving Cedar Park, hospital policies, real costs, and whether Texas Medicaid covers a doula.

ð± Get the free app â https://truejoybirthing.com
ð Free birth plan â https://truejoybirthing.com/birth-plan-template/
ð Cedar Park doula directory â https://truejoybirthing.com/birth-support/cedar-park-tx/

â¸ Find Cedar Park doulas & midwives (4 providers: Alicia Power of Birth Power Doula Services, Tara Garner, Alivia Lehmann, Motherwell Doula Services)
â¸ Compare hospital options (Ascension Seton Cedar Park Hospital, Cedar Park Regional Medical Center, St. David's Round Rock Medical Center)
â¸ Know what doula care actually costs ($800â$2,500)
â¸ Explore the Austin Area Birthing Center's Williamson County birth center
â¸ Understand Texas Medicaid doula coverage
â¸ Build your free birth plan step by step

CHAPTERS:
0:00 â Welcome to Cedar Park
0:12 â Where Cedar Park Families Deliver (Hospitals)
0:30 â Ascension Seton Cedar Park Hospital
0:44 â Cedar Park Regional Medical Center
0:57 â St. David's Round Rock Medical Center
1:10 â Doulas & Midwives in Cedar Park
1:23 â The Free Birth Plan App
1:45 â Cost Reality ($800â$2,500)
2:06 â Insurance & Texas Medicaid
2:23 â Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared â all for free.

Created by Shelbi Kohler, certified birth doula.

#cedarparkdoula #txdoula #txmedicaid #birthplan #doula #pregnancycedarpark""",
        'tags': [
            'Cedar Park doula', 'Cedar Park birth doula', 'Texas Medicaid doula',
            'Cedar Park pregnancy guide', 'birth plan template', 'first time mom Cedar Park',
            'Cedar Park hospital maternity', 'Cedar Park doula cost', 'Texas birth support',
            'doula near me', 'Cedar Park midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Cedar Park', 'birth preparation',
            'Ascension Seton Cedar Park Hospital', 'Cedar Park Regional Medical Center',
            "St. David's Round Rock Medical Center", 'Austin Area Birthing Center',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
    },
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
    'virginia-beach-va': {
        'title': 'Virginia Beach Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Virginia Beach — now what? This guide walks you through everything: doulas and midwives serving Virginia Beach, hospital policies, real costs, and whether Virginia Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Virginia Beach doula directory → https://truejoybirthing.com/birth-support/virginia-beach-va/

▸ Find Virginia Beach doulas & midwives
▸ Compare hospital options (Sentara Princess Anne, Sentara VB General, Naval Medical Center Portsmouth)
▸ Know what doula care actually costs ($1,000–$3,000)
▸ Understand Virginia Medicaid doula coverage (~$1,500/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Virginia Beach
0:15 — Where Virginia Beach Families Deliver
0:34 — Sentara Virginia Beach General Hospital
1:11 — Sentara Princess Anne Hospital
1:58 — Naval Medical Center Portsmouth
2:41 — Doulas & Midwives in Virginia Beach
3:00 — The True Joy Birthing App
3:24 — Cost Reality ($1,000–$3,000)
3:54 — Insurance & Virginia Medicaid
4:24 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#virginiabeachdoula #virginiabeachbirth #virginiamedicaid #birthplan #doula #pregnancyvirginiabeach""",
        'tags': [
            'Virginia Beach doula', 'Virginia Beach birth doula', 'Virginia Medicaid doula',
            'Virginia Beach pregnancy guide', 'birth plan template', 'first time mom Virginia Beach',
            'Virginia Beach hospital maternity', 'Virginia Beach doula cost', 'Virginia birth support',
            'doula near me', 'Virginia Beach midwife', 'pregnancy Virginia',
            'free birth plan', 'doula services Virginia Beach', 'birth preparation',
            'Sentara Princess Anne', 'Sentara Virginia Beach', 'Naval Medical Center Portsmouth',
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

▸ Find Fremont doulas & midwives (18 providers)
▸ Compare hospital options (Washington Hospital, El Camino Health, Lucile Packard Stanford)
▸ Explore birth center options (Pacifica Family Maternity Center)
▸ Understand real costs ($1,500–$3,000 for doulas, $5,000–$8,000 for midwifery)
▸ Learn how Medi-Cal's PAVE program covers doula care (~$1,587 per pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Fremont
0:13 — What This Video Covers
0:31 — Washington Hospital (Level II NICU, Doula-Friendly)
1:03 — El Camino Health Mountain View (Level III NICU)
1:31 — Lucile Packard Children's Hospital Stanford (Level IV NICU)
2:08 — Pacifica Family Maternity Center (Freestanding Birth Center)
2:39 — 18 Doulas & Midwives Serving Fremont
3:06 — The True Joy Birthing App
3:30 — Cost Reality ($1,500–$3,000)
4:01 — Medi-Cal Covers Doula Care (PAVE Program)
4:31 — Build Your Free Birth Plan

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
            'Lucile Packard Stanford', 'Pacifica Family Maternity Center',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'newport-beach-ca': {
        'title': 'Newport Beach Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': "Newport Beach, California doula and birth plan guide by True Joy Birthing. Find local doulas, hospital info, costs, and Medi-Cal coverage. https://truejoybirthing.com/birth-support/newport-beach-ca/",
        'tags': [
            'Newport Beach doula', 'Newport Beach birth doula', 'California Medi-Cal doula',
            'Newport Beach pregnancy guide', 'birth plan template', 'first time mom Newport Beach',
            'Newport Beach hospital maternity', 'Newport Beach doula cost', 'California birth support',
            'doula near me', 'Newport Beach midwife', 'pregnancy California',
            'free birth plan', 'doula services Newport Beach', 'birth preparation',
            'Hoag Newport Beach', 'Providence St Joseph Orange', 'UCI Medical Center',
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
        'title': 'Cary, NC Doula & Birth Plan Guide: Costs, Hospitals & Birth Centers (First-Time Mom)',
        'description': """You just found out you're pregnant in Cary, North Carolina â now what? This guide walks you through everything: doulas and midwives serving Cary, hospital policies, real costs, and whether NC Medicaid covers a doula.

ð± Get the free app â https://truejoybirthing.com
ð Free birth plan â https://truejoybirthing.com/birth-plan-template/
ð Cary doula directory â https://truejoybirthing.com/birth-support/cary-nc/

â¸ Find Cary doulas & midwives (Triangle Doula by Nature, Mariam Lam, Amanda Petry, Sacred Haven Midwifery)
â¸ Compare hospital options (WakeMed Cary Level III NICU, UNC Health Rex Level IV NICU)
â¸ Tour the CNM-led Haven Women's Health and Birth Center in Cary
â¸ Know what doula care actually costs ($800â$2,500)
â¸ Understand NC Medicaid doula coverage (not yet statewide as of 2026)
â¸ Build your free birth plan step by step

CHAPTERS:
0:00 â Welcome to Cary, North Carolina
0:13 â Why Cary Families Choose Local Birth Support
0:29 â WakeMed Cary Hospital (Level III NICU)
0:53 â UNC Health Rex (Level IV NICU)
1:11 â Local Doulas & Midwives
1:53 â The True Joy Birthing App
2:02 â Doula Costs in Cary ($800â$2,500)
2:18 â Medicaid & Insurance in North Carolina
2:37 â Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared â all for free.

Created by Shelbi Kohler, certified birth doula.

#carydoula #caryncbirth #ncbirth #birthplan #doula #pregnancync""",
        'tags': [
            'Cary doula', 'Cary NC birth doula', 'North Carolina birth doula',
            'Cary pregnancy guide', 'birth plan template', 'first time mom Cary NC',
            'WakeMed Cary maternity', 'UNC Rex maternity', 'Cary doula cost',
            'North Carolina birth support', 'doula near me', 'Cary midwife',
            'pregnancy North Carolina', 'free birth plan', 'doula services Cary',
            'Research Triangle doula', 'Cary NC birth guide', 'Haven birth center Cary',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
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

    #dallasdoula #dallascabirth #texastabill #birthplan #doula #pregnancydallas""",
            'tags': [
                'Dallas doula', 'Dallas birth doula', 'Texas Medicaid doula',
                'Dallas pregnancy guide', 'birth plan template', 'first time mom Dallas',
                'Dallas hospital maternity', 'Dallas doula cost', 'Texas birth support',
                'doula near me', 'Dallas midwife', 'pregnancy Texas',
                'free birth plan', 'doula services Dallas', 'birth preparation',
                'Texas Health Presbyterian Hospital Dallas', 'Baylor University Medical Center',
                'Parkland Memorial Hospital', 'Medical City Dallas', 'Methodist Dallas Medical Center',
            ],
            'category_id': '27',  # Education
            'privacy_status': 'public',
            'made_for_kids': False,
        },
        'buffalo-ny': {
            'title': 'Buffalo, NY Birth Doula Guide | Best Doulas, Hospitals & Birth Centers',
            'description': """You just found out you're pregnant in Buffalo — now what? This guide walks you through everything: doulas and midwives serving Buffalo, hospital policies, real costs, and whether New York Medicaid covers a doula.

    📱 Get the free app → https://truejoybirthing.com
    📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
    📍 Buffalo doula directory → https://truejoybirthing.com/birth-support/buffalo-ny/

    ▸ Find Buffalo doulas & midwives (Tara Withey, Malissa Larson, Meghan Warner, Njeri Motley, Caitlan Wilber)
    ▸ Compare hospital options (John R. Oishei Children's, Mercy Hospital, Sisters of Charity)
    ▸ Know what doula care actually costs ($1,000–$2,500)
    ▸ Understand New York Medicaid doula coverage (up to $1,710)
    ▸ Build your free birth plan step by step

    CHAPTERS:
    0:00 — Welcome to Buffalo
    0:09 — Where Buffalo Families Deliver (Hospitals)
    0:38 — John R. Oishei Children's Hospital (Level IV NICU)
    1:34 — Mercy Hospital of Buffalo (Level III NICU)
    2:19 — Doulas & Midwives in Buffalo
    2:36 — The True Joy Birthing App
    2:58 — Cost Reality ($1,000–$2,500)
    3:25 — Insurance & New York Medicaid
    3:42 — Your Next Step

    True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

    Created by Shelbi Kohler, certified birth doula.

    #buffalodoula #buffalonyc #newyorkmedicaid #birthplan #doula #pregnancybuffalo""",
            'tags': [
                'Buffalo doula', 'Buffalo birth doula', 'New York Medicaid doula',
                'Buffalo pregnancy guide', 'birth plan template', 'first time mom Buffalo NY',
                'Buffalo hospital maternity', 'Buffalo doula cost', 'New York birth support',
                'doula near me', 'Buffalo midwife', 'pregnancy New York',
                'free birth plan', 'doula services Buffalo', 'birth preparation',
                "John R. Oishei Children's Hospital", 'Mercy Hospital Buffalo',
                'Sisters of Charity Hospital Buffalo', 'birth center', 'midwife',
            ],
            'category_id': '27',  # Education
            'privacy_status': 'public',
            'made_for_kids': False,
        },
        'worcester-ma': {
            'title': 'Worcester Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
            'description': """You just found out you're pregnant in Worcester — now what? This guide walks you through everything: doulas and midwives serving Worcester, hospital policies, real costs, and whether Massachusetts MassHealth covers a doula.

    📱 Get the free app → https://truejoybirthing.com
    📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
    📍 Worcester doula directory → https://truejoybirthing.com/birth-support/worcester-ma/

    ▸ Find Worcester doulas & midwives (5 providers)
    ▸ Compare hospital options (UMass Memorial Medical Center, Saint Vincent Hospital)
    ▸ Know what doula care actually costs ($1,200–$3,000)
    ▸ Understand Massachusetts MassHealth doula coverage (covered since Jan 2024)
    ▸ Build your free birth plan step by step

    CHAPTERS:
    0:00 — Welcome to Worcester
    0:11 — What We Cover
    0:29 — UMass Memorial Medical Center (Level III NICU)
    1:03 — Saint Vincent Hospital (Level II Special Care)
    1:35 — Embrace Midwifery (Home Birth)
    1:58 — Venette Maurice
    2:32 — Candace Laura
    3:01 — Myriam Lukoff
    3:35 — Shantel Collins
    4:04 — Loreal Drayton
    4:34 — The True Joy Birthing App
    4:57 — Cost Reality ($1,200–$3,000)
    5:24 — Insurance & Massachusetts Medicaid
    5:53 — Your Next Step

    True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

    Created by Shelbi Kohler, certified birth doula.

    #worcesterdoula #worcestermabirth #massachusettsmedicaid #birthplan #doula #pregnancyworcester""",
            'tags': [
                'Worcester doula', 'Worcester birth doula', 'Massachusetts Medicaid doula',
                'Worcester pregnancy guide', 'birth plan template', 'first time mom Worcester MA',
                'Worcester hospital maternity', 'Worcester doula cost', 'Massachusetts birth support',
                'doula near me', 'Worcester midwife', 'pregnancy Massachusetts',
                'free birth plan', 'doula services Worcester', 'birth preparation',
                'UMass Memorial Medical Center', 'Saint Vincent Hospital Worcester',
                'MassHealth doula coverage', 'home birth Worcester', 'midwife',
            ],
            'category_id': '27',  # Education
            'privacy_status': 'public',
            'made_for_kids': False,
        },
    'fontana-ca': {
        'title': 'Fontana Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Fontana — now what? This guide walks you through everything: doulas and midwives serving Fontana, hospital policies, real costs, and how California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Fontana doula directory → https://truejoybirthing.com/birth-support/fontana-ca/

▸ Find Fontana doulas & midwives (5 providers)
▸ Compare hospital options (Kaiser Permanente Fontana Medical Center, San Antonio Regional Hospital)
▸ Birth center option: The Natural Birth Place in Rancho Cucamonga
▸ Know what doula care actually costs ($1,200-$2,500)
▸ Understand California Medi-Cal PAVE doula coverage ($1,587/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Fontana
0:12 — Where Fontana Hospitals & Birth Centers
0:33 — Kaiser Permanente Fontana Medical Center
0:56 — San Antonio Regional Hospital
1:13 — The Natural Birth Place (Birth Center)
1:31 — Doula127
1:48 — Holistic Doula LLC
2:10 — 4 The Moms Southern California
2:31 — Two Moons Doula Services
2:51 — Raising Birth Doula Care
3:13 — The True Joy Birthing App
3:36 — Cost Reality ($1,200-$2,500)
4:02 — Insurance & California Medi-Cal PAVE
4:36 — Your Next Step

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
    'agoura-hills-ca': {
        'title': 'Agoura Hills Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Agoura Hills — now what? This guide walks you through everything: doulas and midwives serving Agoura Hills, hospital policies, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Agoura Hills doula directory → https://truejoybirthing.com/birth-support/agoura-hills-ca/

▸ Find Agoura Hills doulas & midwives (5 providers)
▸ Compare hospital options (Los Robles, Providence Cedars-Sinai Tarzana, Northridge)
▸ Birth center option (SCV Birth Center)
▸ Know what doula care actually costs ($1,800-$5,000)
▸ Understand California Medi-Cal doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Agoura Hills
0:12 — What This Guide Covers
0:30 — Los Robles Regional Medical Center
0:50 — Providence Cedars-Sinai Tarzana
1:05 — Dignity Health Northridge
1:26 — SCV Birth Center
1:45 — Mary Skinner - Lotus Doula Tribe
2:01 — Sharon Jensen-Cody
2:19 — Christine Cannon - The Midwife
2:37 — Cris Levin - Postpartum
2:52 — Monica Mayer - Breath 2 Birth
3:08 — The True Joy Birthing App
3:28 — Cost Reality
3:49 — Insurance & Medi-Cal
4:09 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#agourahillsdoula #agourahillsbirth #californiamedicaid #birthplan #doula #pregnancyagourahills""",
        'tags': [
            'Agoura Hills doula', 'Agoura Hills birth doula', 'California Medi-Cal doula',
            'Agoura Hills pregnancy guide', 'birth plan template', 'first time mom Agoura Hills',
            'Los Robles maternity', 'Thousand Oaks doula', 'Westlake Village doula',
            'Agoura Hills doula cost', 'California birth support',
            'doula near me', 'Conejo Valley doula', 'pregnancy California',
            'free birth plan', 'doula services Agoura Hills', 'birth preparation',
            'SCV Birth Center', 'Los Robles Regional Medical Center',
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
â¸ Compare hospital options (Kaiser Permanente Moreno Valley Medical Center, Riverside University Health System Medical Center)
â¸ Know what doula care actually costs ($1,200-$2,500)
â¸ Understand California Medi-Cal PAVE doula coverage ($1,587/pregnancy)
â¸ Build your free birth plan step by step

CHAPTERS:
0:00 â Welcome to Moreno Valley
0:12 â Where Moreno Valley Families Deliver
0:33 â Kaiser Permanente Moreno Valley Medical Center
0:55 â Riverside University Health System Medical Center
1:18 â Doulas & Midwives in Moreno Valley
2:17 â The True Joy Birthing App
2:42 â Cost Reality ($1,200-$2,500)
3:05 â Insurance & California Medi-Cal
3:30 â Your Next Step

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
        'title': 'Carrollton Texas Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Carrollton — now what? This guide walks you through everything: doulas and midwives serving Carrollton, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Carrollton doula directory → https://truejoybirthing.com/birth-support/carrollton-tx/

▸ Find Carrollton doulas & midwives (9 providers)
▸ Compare hospital options (Medical City Lewisville, Texas Health Flower Mound, Texas Health Presbyterian Hospital Plano)
▸ Know what doula care actually costs ($900–$2,500)
▸ Understand Texas Medicaid doula coverage (SB 750)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Carrollton
0:13 — What This Guide Covers
0:31 — Medical City Lewisville (Level III NICU)
0:49 — Texas Health Flower Mound (Level III NICU)
1:09 — Texas Health Presbyterian Hospital Plano (Level III NICU)
1:28 — Doulas & Midwives in Carrollton
1:37 — The True Joy Birthing App
2:00 — Cost Reality ($900–$2,500)
2:25 — Insurance & Texas Medicaid
2:45 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#carrolltondoula #carrolltontxbirth #texasmedicaid #birthplan #doula #pregnancycarrollton""",
        'tags': [
            'Carrollton doula', 'Carrollton birth doula', 'Texas Medicaid doula',
            'Carrollton pregnancy guide', 'birth plan template', 'first time mom Carrollton',
            'Medical City Lewisville maternity', 'Texas Health Flower Mound maternity',
            'Texas Health Presbyterian Plano maternity',
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
▸ Compare hospital options (Johns Hopkins, UMMC, Sinai)
▸ Know what doula care actually costs ($800–$2,200)
▸ Understand Maryland Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Baltimore
0:12 — Baltimore Hospitals (Johns Hopkins, UMMC, Sinai)
1:18 — Birth Center Option
1:38 — Doulas & Midwives in Baltimore
2:39 — Build Your Birth Plan
3:00 — Cost Reality
3:22 — Maryland Medicaid Coverage
3:40 — Your Next Step

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
        'springfield-il': {
        'title': 'Springfield IL Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Springfield — now what? This guide walks you through everything: doulas and midwives serving Springfield, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Springfield doula directory → https://truejoybirthing.com/birth-support/springfield-il/

▸ Find Springfield doulas & midwives (Grayce Eubanks, Jennifer Griffin, Kyra Patton)
▸ Compare hospital options (Springfield Memorial, HSHS St. John's)
▸ Know what doula care actually costs ($800–$2,000)
▸ Understand Illinois Medicaid doula coverage (HB 4430, up to $1,500/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Springfield
0:29 — Where Springfield Families Deliver (Hospitals)
1:37 — Doulas & Midwives in Springfield
2:58 — The True Joy Birthing App
3:22 — Cost Reality ($800–$2,000)
3:47 — Insurance & Illinois Medicaid
4:18 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#springfieldildoula #springfieldilbirth #illinoismedicaid #birthplan #doula #pregnancyspringfield""",
        'tags': [
            'Springfield IL doula', 'Springfield IL birth doula', 'Illinois Medicaid doula',
            'Springfield IL pregnancy guide', 'birth plan template', 'first time mom Springfield',
            'Springfield Memorial Hospital maternity', 'HSHS St Johns maternity', 'Springfield doula cost',
            'doula near me', 'Springfield midwife', 'pregnancy Illinois',
            'free birth plan', 'doula services Springfield', 'birth preparation',
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
    'gainesville-fl': {
        'title': 'Gainesville Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Gainesville — now what? This guide walks you through everything: doulas and midwives serving Gainesville, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Gainesville doula directory → https://truejoybirthing.com/birth-support/gainesville-fl/

â¸ Find Gainesville doulas & midwives (10 providers)
â¸ Compare hospital options (UF Health Shands, North Florida Regional)
â¸ Tour the area's freestanding birth center (Vision Birth Center of Gainesville)
â¸ Know what doula care actually costs ($700â$1,800)
â¸ Understand Florida Medicaid doula coverage
â¸ Build your free birth plan step by step

CHAPTERS:
0:00 â Welcome to Gainesville
0:13 â What This Guide Covers
0:35 â UF Health Shands Hospital
1:11 â North Florida Regional Medical Center
1:40 â Vision Birth Center of Gainesville
2:10 â Doulas & Midwives (10 Providers)
2:29 â The Free Birth Plan App
2:55 â What Doula Care Costs
3:19 â Florida Medicaid & Insurance
3:42 â Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#gainesvilledoula #gainesvillebirth #floridamedicaid #birthplan #doula #pregnancygainesville""",
        'tags': [
            'Gainesville doula', 'Gainesville birth doula', 'Florida Medicaid doula',
            'Gainesville pregnancy guide', 'birth plan template', 'first time mom Gainesville',
            'UF Health Shands maternity', 'North Florida Regional maternity', 'Gainesville doula cost',
            'doula near me', 'Gainesville midwife', 'pregnancy Florida',
            'Vision Birth Center Gainesville', 'Gainesville birth center',
            'free birth plan', 'doula services Gainesville', 'birth preparation',
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
        'title': 'Las Vegas NV Doula & Birth Guide: Hospitals, Costs & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Las Vegas, Nevada - now what? This guide walks you through everything: the hospitals where doulas are welcome, Nevada's first licensed freestanding birth center, the doulas serving your neighborhood, real costs, and how Nevada Medicaid covers doula care.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Las Vegas doula directory → https://truejoybirthing.com/birth-support/las-vegas-nv/

▸ Tour Sunrise, Spring Valley, and Southern Hills hospitals
▸ Visit Serenity Birth Center - Nevada's first state-licensed birth center
▸ Meet Las Vegas doulas: Carla Parker, Alyson Mancini, Chandra Larocque, Aisha Fanning
▸ Know what doula care actually costs ($1,200-$3,500)
▸ Nevada Medicaid covers doula services - $1,300 in Clark County
▸ Build your free birth plan step by step

CHAPTERS:
0:00 - Welcome to Las Vegas
0:36 - Hospitals: Sunrise, Spring Valley, Southern Hills
1:52 - Serenity Birth Center
2:17 - Las Vegas Doulas (Carla, Alyson, Chandra, Aisha)
4:00 - The Free True Joy Birthing App
4:28 - What Doula Care Costs in Las Vegas
4:53 - Nevada Medicaid Covers Doulas
5:20 - Build Your Free Birth Plan

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared - all for free.

Created by Shelbi Kohler, certified birth doula.

#lasvegasdoula #lasvegasbirth #nevadadoula #nevadamedicaid #birthplan #pregnancylasvegas #doula""",
        'tags': [
            'Las Vegas NV doula',
            'Las Vegas doula',
            'Las Vegas birth doula',
            'Nevada Medicaid doula',
            'Las Vegas pregnancy guide',
            'Las Vegas doula cost',
            'doula services Las Vegas',
            'Las Vegas midwife',
            'Nevada birth support',
            'pregnancy Nevada',
            'first time mom Las Vegas',
            'Las Vegas hospital maternity',
            'Sunrise Hospital Las Vegas',
            'Spring Valley Hospital Las Vegas',
            'Southern Hills Hospital',
            'Serenity Birth Center',
            'birth plan template',
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

▸ Find Minneapolis doulas & midwives (9 providers)
▸ Compare hospital options (Abbott Northwestern, HCMC, M Health Fairview, North Memorial)
▸ Minnesota Birth Center (CABC-accredited freestanding birth center)
▸ Know what doula care actually costs ($1,000–$3,200)
▸ Understand Minnesota Medicaid doula coverage ($1,700/pregnancy since Jan 2024)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Minneapolis
0:14 — Where Minneapolis Families Deliver
0:31 — Abbott Northwestern Hospital (Level III NICU)
0:51 — HCMC Hennepin Healthcare (Level III NICU)
1:12 — M Health Fairview University of Minnesota (Level IV NICU)
1:31 — North Memorial Health Hospital (Level III NICU)
1:48 — Minnesota Birth Center (Freestanding)
2:06 — Doulas & Midwives in Minneapolis
2:27 — The True Joy Birthing App
2:50 — Cost Reality ($1,000–$3,200)
3:13 — Insurance & Minnesota Medicaid
3:39 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#minneapolisdoula #minneapolisbirth #minnesotamedicaid #birthplan #doula #pregnancyminneapolis""",
        'tags': [
            'Minneapolis doula', 'Minneapolis birth doula', 'Minnesota Medicaid doula',
            'Minneapolis pregnancy guide', 'birth plan template', 'first time mom Minneapolis',
            'Abbott Northwestern maternity', 'HCMC maternity', 'M Health Fairview maternity',
            'North Memorial Health maternity', 'Minnesota Birth Center',
            'Minneapolis doula cost', 'Minnesota birth support', 'doula near me', 'Minneapolis midwife',
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
0:11 — Where Pittsburgh Families Deliver
0:28 — Magee-Womens Hospital
0:51 — UPMC Children's Hospital
1:15 — Allegheny General Hospital
1:40 — The Midwife Center
2:12 — Doulas & Midwives in Pittsburgh
2:30 — The True Joy Birthing App
2:53 — Cost Reality ($700–$2,000)
3:13 — Insurance & Pennsylvania Medicaid
3:42 — Your Next Step

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
        'category_id': '27',  # Education
        'privacy_status': 'unlisted',
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
    'fort-collins-co': {
        'title': 'Fort Collins Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Fort Collins — now what? This guide walks you through everything: 7 doulas serving Fort Collins, hospital policies, real costs, and whether Colorado Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Fort Collins doula directory → https://truejoybirthing.com/birth-support/fort-collins-co/

▸ Find Fort Collins doulas & midwives (7 providers)
▸ Compare hospital options (UCHealth Poudre Valley, Banner North Colorado)
▸ Explore Avalon Birth & Wellness Center
▸ Know what doula care actually costs ($500-$4,000)
▸ Understand Colorado Medicaid doula coverage (HB 23-1027, up to $750/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Fort Collins
0:12 — What This Video Covers
0:34 — UCHealth Poudre Valley Hospital
1:19 — Banner North Colorado Medical Center
1:53 — Avalon Birth & Wellness Center
2:20 — Doulas Serving Fort Collins (7 providers)
3:16 — The True Joy Birthing App
3:37 — Cost Reality ($500-$4,000)
4:02 — Insurance & Colorado Medicaid
4:36 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#fortcollinsdoula #fortcollinsbirth #coloradomedicaid #birthplan #doula #pregnancyfortcollins""",
        'tags': [
            'fort collins doula', 'fort collins midwife', 'colorado birth',
            'poudre valley hospital', 'banner north colorado', 'avalon birth center',
            'noco doula collective', 'doula cost', 'birth plan',
            'colorado medicaid doula', 'northern colorado doula',
            'fort collins pregnancy', 'fort collins birth support',
            'doula services fort collins', 'birth doula colorado',
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
    'boise-id': {
        'title': 'Boise ID Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Boise, Idaho — now what? This guide walks you through everything: doulas and midwives serving Boise, hospital policies, real costs, and whether Idaho Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Boise doula directory → https://truejoybirthing.com/birth-support/boise-id/

▸ Find Boise doulas & midwives
▸ Compare hospital options (St. Luke's Boise, Saint Alphonsus)
▸ Know what doula care actually costs ($900–$1,800)
▸ Understand Idaho Medicaid (does not cover doulas)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Boise
0:11 — Where Boise Families Deliver (Hospitals)
1:06 — Doulas & Midwives in Boise
1:55 — The True Joy Birthing App
2:19 — Cost Reality ($900–$1,800)
2:37 — Insurance & Idaho Medicaid
3:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#boiseidahodoula #boisebirth #idahomedicaid #birthplan #doula #pregnancyboise""",
        'tags': [
            'Boise ID doula', 'Boise Idaho birth doula', 'Idaho Medicaid doula',
            'Boise pregnancy guide', 'birth plan template', 'first time mom Boise',
            "St. Luke's Boise maternity", 'Saint Alphonsus maternity', 'Boise doula cost',
            'Idaho birth support', 'doula near me', 'Boise midwife',
            'pregnancy Idaho', 'free birth plan', 'doula services Boise',
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
▸ Compare hospital options (UMC El Paso, Las Palmas, Del Sol, Providence)
▸ Luna Tierra Casa de Partos — bilingual birth center
▸ Know what doula care actually costs ($550–$2,200)
▸ Understand Texas Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to El Paso
0:13 — Where El Paso Families Deliver (Hospitals)
0:32 — University Medical Center of El Paso
0:45 — Las Palmas Medical Center
0:59 — Del Sol Medical Center
1:09 — Hospitals of Providence Memorial Campus
1:20 — Luna Tierra Casa de Partos (Birth Center)
1:34 — 5 Doulas Serving El Paso
2:03 — The True Joy Birthing App
2:28 — Cost Reality ($550–$2,200)
2:49 — Insurance & Texas Medicaid
3:09 — Your Next Step

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
        'description': """You just found out you're pregnant in Fort Worth — now what? This guide walks you through everything: 9 doulas and midwives serving Fort Worth, 3 hospital options, the only freestanding birth center, real costs, and how Texas Medicaid covers a doula under SB 750.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Fort Worth doula directory → https://truejoybirthing.com/birth-support/fort-worth-tx/

▸ Meet 9 Fort Worth doulas & midwives
▸ Compare hospital options (Texas Health Harris, Andrews Women's at Baylor, Medical City Alliance)
▸ Fort Worth Birthing & Wellness Center (CABC accredited birth center)
▸ Know what doula care actually costs ($800–$3,000)
▸ Understand Texas Medicaid doula coverage under SB 750 (since Sep 2024)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Fort Worth
0:12 — What This Guide Covers
0:33 — Texas Health Harris Methodist Fort Worth
0:48 — Andrews Women's Hospital at Baylor Scott & White
1:03 — Medical City Alliance
1:16 — Fort Worth Birthing & Wellness Center
1:36 — Fort Worth's 9 Doulas & Midwives
2:00 — The True Joy Birthing App
2:23 — Cost Reality ($800–$3,000)
2:53 — Insurance & Texas Medicaid (SB 750)
3:20 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#fortworthdoula #fortworthbirth #texasmedicaid #birthplan #doula #pregnancyfortworth""",
        'tags': [
            'Fort Worth doula', 'Fort Worth birth doula', 'Texas Medicaid doula',
            'Fort Worth pregnancy guide', 'birth plan template', 'first time mom Fort Worth',
            'Texas Health Harris maternity', 'Medical City Alliance maternity',
            'Fort Worth Birthing Wellness Center', 'Fort Worth doula cost', 'Texas birth support',
            'doula near me', 'Fort Worth midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Fort Worth', 'birth preparation',
            'SB 750 doula coverage', 'CABC birth center Fort Worth',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'fresno-ca': {
        'title': 'Fresno Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Fresno — now what? This guide walks you through everything: 7 doulas serving Fresno, 3 hospital options, real costs, and how California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Fresno doula directory → https://truejoybirthing.com/birth-support/fresno-ca/

▸ Meet 7 Fresno doulas & midwives
▸ Compare hospital options (Community Regional, Clovis Community, Saint Agnes)
▸ Know what doula care actually costs ($1,000-$3,000)
▸ Understand California Medi-Cal PAVE doula coverage ($1,587/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Fresno
0:10 — What This Guide Covers
0:27 — Community Regional Medical Center
0:48 — Clovis Community Medical Center
1:01 — Saint Agnes Medical Center
1:18 — Fresno's 7 Doulas & Midwives
2:06 — The True Joy Birthing App
2:30 — Cost Reality ($1,000-$3,000)
2:54 — Insurance & California Medi-Cal
3:21 — Your Next Step

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
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
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
▸ Compare hospital options (Regions, M Health Fairview St. John's, United Hospital, Minnesota Birth Center)
▸ Know what doula care actually costs ($1,200–$3,500)
▸ Understand Minnesota Medical Assistance doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to St. Paul
0:10 — What This Video Covers
0:29 — Regions Hospital
0:53 — M Health Fairview St. John's Hospital
1:20 — United Hospital (Allina Health)
1:46 — Minnesota Birth Center - St. Paul
2:11 — Midwest Doulas
2:38 — Blooma Birth Support
3:02 — Twin Cities Doulas (Everyday Miracles)
3:26 — Doula Minnesota
3:51 — The True Joy Birthing App
4:15 — Cost Reality ($1,200–$3,500)
4:37 — Minnesota Medicaid & Insurance
5:15 — Your Next Step

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
    'new-braunfels-tx': {
        'title': 'New Braunfels Birth Guide: Doulas, Hospitals & Birth Centers (First-Time Mom)',
        'description': """Just found out you're pregnant in New Braunfels, Texas? This guide walks you through everything: doulas and midwives serving New Braunfels, where you can deliver, real costs, and whether Texas Medicaid covers a doula.

ð± Get the free app â https://truejoybirthing.com
ð Free birth plan â https://truejoybirthing.com/birth-plan-template/
ð New Braunfels doula directory â https://truejoybirthing.com/birth-support/new-braunfels-tx/

â¸ Find New Braunfels doulas & midwives
â¸ Compare delivery options (CHRISTUS Santa Rosa Hospital, Joyful Beginnings & Family Birth Centers)
â¸ Know what doula care actually costs ($800â$2,500)
â¸ Understand Texas Medicaid doula coverage (not yet covered statewide)
â¸ Build your free birth plan step by step

CHAPTERS:
0:00 â Welcome to New Braunfels
0:15 â What This Guide Covers
0:34 â CHRISTUS Santa Rosa Hospital
0:55 â Joyful Beginnings Birth Center
1:15 â Family Birth Center
1:35 â Doulas & Midwives Serving New Braunfels
2:31 â The True Joy Birthing App
2:54 â Cost Reality ($800â$2,500)
3:21 â Insurance & Texas Medicaid
4:03 â Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into birth prepared â all for free.

Created by Shelbi Kohler, certified birth doula.

#newbraunfelsdoula #newbraunfelstxbirth #texasmedicaid #birthplan #doula #pregnancynewbraunfels""",
        'tags': [
            'New Braunfels TX doula', 'New Braunfels birth doula', 'Texas Hill Country doula',
            'New Braunfels pregnancy guide', 'birth plan template', 'first time mom New Braunfels',
            'CHRISTUS Santa Rosa New Braunfels', 'Joyful Beginnings Birth Center', 'Family Birth Center',
            'New Braunfels doula cost', 'Texas birth support',
            'doula near me', 'New Braunfels midwife', 'pregnancy Texas',
            'free birth plan', 'doula services New Braunfels', 'birth preparation',
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
        'description': """Just found out you're pregnant in Tampa, Florida? This guide walks you through everything: five Tampa hospitals where doulas and midwives are welcome, two birth centers offering midwife-led care, ten doulas and midwives you can work with, what everything costs, how Florida Medicaid can help, and a free app that builds your birth plan step by step.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Tampa doula directory → https://truejoybirthing.com/birth-support/tampa-fl/

▸ Find Tampa doulas & midwives
▸ Compare hospital options (Tampa General, St. Joseph's Women's, AdventHealth Tampa, HCA Florida Brandon, South Florida Baptist)
▸ Know what doula care actually costs ($800–$5,000)
▸ Understand Florida Medicaid doula coverage (covers since 2024)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Tampa
0:11 — What This Guide Covers
0:30 — Tampa General Hospital
0:58 — St. Joseph's Women's Hospital
1:26 — AdventHealth Tampa
1:52 — Barefoot Birth
2:23 — Sweet Child of Mine Birth Center
2:45 — Doulas & Midwives in Tampa
3:14 — The True Joy Birthing App
3:36 — Cost Reality ($800–$5,000)
3:58 — Insurance & Florida Medicaid
4:24 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#tampadoula #tampabirth #floridamedicaid #birthplan #doula #pregnancytampa""",
        'tags': [
            'Tampa doula', 'Tampa birth doula', 'Florida Medicaid doula',
            'Tampa pregnancy guide', 'birth plan template', 'first time mom Tampa',
            'Tampa General Hospital maternity', 'St Josephs Womens Hospital Tampa',
            'AdventHealth Tampa maternity', 'Tampa doula cost',
            'doula near me', 'Tampa midwife', 'pregnancy Florida',
            'free birth plan', 'doula services Tampa', 'birth preparation',
            'HCA Florida Brandon Hospital', 'South Florida Baptist Hospital',
            'Barefoot Birth Tampa', 'Sweet Child of Mine Birth Center',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'jacksonville-fl': {
        'title': 'Jacksonville Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Jacksonville, Florida? This guide walks you through everything: five Jacksonville hospitals where doulas and midwives are welcome, two freestanding birth centers, twelve doulas and midwives you can work with, what everything costs, how Florida Medicaid covers doula care through SB 264, and a free app that builds your birth plan step by step.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Jacksonville doula directory → https://truejoybirthing.com/birth-support/jacksonville-fl/

▸ Find Jacksonville doulas & midwives (12 providers)
▸ Compare hospital options (Baptist Medical Center, UF Health, St. Vincent's, Memorial, Baptist Beaches)
▸ Tour two birth centers (Transitions, Fruitful Vine)
▸ Know what doula care actually costs ($500–$6,000)
▸ Understand Florida Medicaid doula coverage (SB 264)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Jacksonville
0:12 — What This Guide Covers
0:31 — Baptist Medical Center Jacksonville (Level IV NICU)
1:21 — UF Health Jacksonville (Level III NICU)
2:07 — Ascension St. Vincent's Southside
2:49 — HCA Florida Memorial Hospital
3:25 — Baptist Medical Center Beaches
3:54 — Transitions Birth Center
4:17 — Fruitful Vine Birth Center
4:40 — Doulas & Midwives in Jacksonville
5:47 — The True Joy Birthing App
6:13 — Cost Reality ($500–$6,000)
6:50 — Insurance & Florida Medicaid SB 264
7:42 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#jacksonvilledoula #jacksonvillebirth #floridamedicaid #birthplan #doula #pregnancyjacksonville""",
        'tags': [
            'Jacksonville doula', 'Florida Medicaid doula',
            'Jacksonville pregnancy guide', 'birth plan template', 'first time mom Jacksonville',
            'Jacksonville hospital maternity', 'Jacksonville doula cost',
            'doula near me', 'Jacksonville midwife', 'pregnancy Florida',
            'free birth plan', 'doula services Jacksonville',
            'Baptist Medical Center Jacksonville', 'UF Health Jacksonville',
            'SB 264',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'oakland-ca': {
        'title': 'Oakland CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)',
        'description': """Planning a birth in Oakland, California? This complete guide covers everything first-time moms need to know about doulas, hospitals, birth centers, costs, and Medi-Cal coverage in the East Bay.

CHAPTERS:
0:00 Welcome to Oakland
0:14 What This Guide Covers
0:35 Highland Hospital
1:08 Kaiser Permanente Oakland
1:39 Alta Bates Summit Medical Center
2:11 Bay Area Birth Center
2:32 Doulas & Midwives Serving Oakland
2:50 Free Birth Plan App
3:14 Doula Costs in Oakland
3:42 Medi-Cal Insurance Coverage
4:15 Make Your Birth Plan

Oakland hospitals covered: Highland Hospital (Level III NICU, Medi-Cal), Kaiser Permanente Oakland (Level III NICU, midwifery program), Alta Bates Summit Medical Center (Level III NICU at Berkeley campus).

California Medi-Cal covers doula services up to $1,587 per pregnancy since January 2023.

Download the free True Joy Birthing app: https://truejoybirthing.com/app
Find a doula near you: https://truejoybirthing.com/birth-support/oakland-ca/

#oaklanddoula #oaklandmidwife #californiabirth #eastbaydoula #highlandhospital #kaiserpermanente #altabates #medicaid #birthplan #trimester #pregnancyguide""",
        'tags': [
            'oakland doula', 'oakland midwife', 'california birth', 'east bay doula',
            'highland hospital oakland', 'kaiser oakland', 'alta bates summit',
            'medi-cal doula', 'birth plan template', 'first time mom oakland',
            'alameda county birth', 'bay area birth center',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    "richmond-va": {
        "title": "Richmond VA Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """Planning a birth in Richmond, Virginia? This is your complete guide.

We cover everything first-time parents need to know:

HOSPITALS (2):
VCU Medical Center — Level IV NICU, Level I trauma center, academic powerhouse, accepts Virginia Medicaid, doulas welcome
Bon Secours St. Mary's Hospital — Level III NICU, community maternity hospital, private labor suites, midwifery options, accepts Virginia Medicaid, doulas welcome

DOULAS (4):
Richmond Birth and Baby — $1,200-$2,200 (birth doula, postpartum, newborn care)
Richmond Birth Doula Services — $1,200-$1,800 (birth and postpartum support)
Doula Training Center of Virginia — $1,000-$2,000 (birth and postpartum doula)
Emily Bruno / MyBirth — $1,800-$2,000 (birth doula since 2007)

COSTS:
Birth doulas: $1,000-$2,200
Postpartum doulas: $25-$45/hour

MEDICAID:
Virginia Medicaid does NOT currently cover doula services as of 2026. Families must pay out of pocket, though some doulas offer sliding scale rates.

Download the free True Joy Birthing app: https://truejoybirthing.com/app
Find a doula near you: https://truejoybirthing.com/birth-support/richmond-va/

#richmonddoula #richmondmidwife #virginiabirth #richmondva #vcumedicalcenter #bonsecours #birthplan #firsttimemom #doulatraining #mybirth #richmondbirthandbaby""",
        "tags": [
            'richmond doula', 'richmond midwife', 'virginia birth', 'richmond va birth',
            'vcu medical center', 'bon secours st marys', 'richmond birth and baby',
            'doula training center virginia', 'emily bruno mybirth', 'birth plan template',
            'first time mom richmond', 'virginia medicaid doula',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    "reno-nv": {
        "title": "Reno NV Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """Planning a birth in Reno, Nevada? This complete guide covers everything first-time moms need to know about doulas, hospitals, costs, and Medicaid coverage in Reno.

CHAPTERS:
0:00 Welcome to Reno
0:11 What This Guide Covers
0:30 Renown Regional Medical Center
0:53 Sierra Medical Center
1:13 Carson Tahoe Regional Medical Center
1:40 Jessica Hebert - DOULA CO-OP of Nevada
2:08 Samantha Cole - DCNV
2:32 Ashley Maas - Ashley Maas Birth Services
2:56 Carly Parks - Sweet Pea Doula Co.
3:16 Morgan Powell - Nurtured Birth
3:35 Free Birth Plan App
3:59 Doula Costs in Reno
4:30 Nevada Medicaid & Insurance
5:04 Make Your Birth Plan

Reno hospitals covered: Renown Regional Medical Center (Level III NICU, largest hospital in northern Nevada, DOULA CO-OP credentialed volunteer doulas, Medicaid), Sierra Medical Center (Level III NICU, dedicated Family Birth Center with LDRP suites, Medicaid), Carson Tahoe Regional Medical Center (Baby-Friendly designated, Special Care Nursery, soaking tubs, Medicaid).

Doulas serving Reno:
Jessica Hebert - DOULA CO-OP of Nevada ($800-$2,000, free services via Molina Healthcare for Medicaid enrollees)
Samantha Cole - DCNV ($800-$1,500 via co-op referral)
Ashley Maas - Ashley Maas Birth Services ($2,500, Best Doula in Reno News and Review)
Carly Parks - Sweet Pea Doula Co. ($1,200-$2,000)
Morgan Powell - Nurtured Birth ($800-$1,500, certified Medicaid doula provider)

Nevada Medicaid does NOT currently cover doula services as of 2026. But the DOULA CO-OP of Nevada partners with Molina Healthcare to provide free birth doula services to Medicaid enrollees. HSA and FSA funds can cover doula fees.

Download the free True Joy Birthing app: https://truejoybirthing.com/app
Find a doula near you: https://truejoybirthing.com/birth-support/reno-nv/

#renodoula #renomidwife #nevadabirth #renonv #renownregional #sierramedical #carsontahoe #doulacoop #molinahealthcare #birthplan #firsttimemom #doula #nevadamedicaid #truckeemeadows #sparksnv""",
        "tags": [
            'reno doula', 'reno midwife', 'nevada birth', 'reno nv birth',
            'renown regional medical center', 'sierra medical center',
            'carson tahoe regional medical center', 'doula co-op of nevada',
            'jessica hebert doula', 'ashley maas birth services',
            'sweet pea doula co', 'morgan powell nurtured birth',
            'nevada medicaid doula', 'birth plan template',
            'first time mom reno', 'truckee meadows birth',
            'sparks nv doula', 'doula near me', 'reno pregnancy', 'free birth plan',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'tucson-az': {
        'title': 'Tucson AZ Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """Planning a birth in Tucson, Arizona? This complete guide covers everything first-time moms need to know about doulas, hospitals, costs, and Medicaid coverage in Tucson.

CHAPTERS:
0:00 Welcome to Tucson
0:11 What This Guide Covers
0:29 Tucson Medical Center
1:03 Banner University Medical Center Tucson
1:36 Northwest Medical Center
2:04 Doulas & Midwives Serving Tucson
2:27 Free Birth Plan App
2:49 Doula Costs in Tucson
3:16 Insurance & Arizona Medicaid
3:48 Make Your Birth Plan

Tucson hospitals covered: Tucson Medical Center (Mayo Clinic Care Network, Special Care Nursery, Medicaid), Banner University Medical Center Tucson (Level III NICU at Diamond Children's, academic medical center, Medicaid), Northwest Medical Center (NICU, Women's Center, Medicaid).

Arizona Medicaid (AHCCCS) does NOT currently cover doula services. Most doulas offer sliding-scale fees and payment plans. HSA and FSA funds can cover doula fees.

Download the free True Joy Birthing app: https://truejoybirthing.com/app
Find a doula near you: https://truejoybirthing.com/birth-support/tucson-az/

#tucsondoula #tucsonmidwife #arizonabirth #tucsonaz #tmc #bannerumc #northwestmedical #ahcccs #birthplan #firsttimemom #doula #pregnancyguide""",
        'tags': [
            'tucson doula', 'tucson midwife', 'arizona birth', 'tucson az birth',
            'tucson medical center', 'banner university medical center tucson',
            'northwest medical center tucson', 'ahcccs doula', 'birth plan template',
            'first time mom tucson', 'pima county birth', 'arizona medicaid doula',
            'doula near me', 'tucson pregnancy', 'free birth plan',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    "rochester-ny": {
        "title": "Rochester NY Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """Planning a birth in Rochester, NY? This guide walks you through everything: doula costs, hospital NICU levels, Medicaid coverage, and how to build your birth plan.

Doulas serving Rochester:
- Phyllis Sharp (Royalty Birth Services) - $1,750-$2,000
- Morgan Moy & Rebecca Dilley (The Doula Duo) - $2,000
- Rebecah Hatchel (Labor With Love) - $1,000-$1,500
- Amanda Souza-Hinkley (Alma Sprout) - $500-$1,200

Hospitals covered:
- Strong Memorial Hospital (Level IV NICU)
- Rochester General Hospital (Level III NICU)
- Highland Hospital (Level II Special Care Nursery)
- Unity Hospital / August Family Birth Place (Level II)

NY Medicaid covers doula services up to ~$1,710 as of January 2024.

Chapters:
00:00 ('00:00', 'Hook')
00:10 ('', 'Rochester Birth Overview')
00:27 ('', 'Strong Memorial Hospital')
00:52 ('', 'Rochester General Hospital')
01:12 ('', 'Phyllis Sharp - Royalty Birth Services')
01:35 ('', 'Morgan Moy & Rebecca Dilley - The Doula Duo')
01:54 ('', 'Rebecah Hatchel - Labor With Love')
02:13 ('', 'Amanda Souza-Hinkley - Alma Sprout')
02:36 ('', 'Free Birth Plan App')
03:02 ('', 'Doula Costs in Rochester')
03:27 ('', 'NY Medicaid Doula Coverage')
03:52 ('', 'Next Steps')

Free birth plan app: https://truejoybirthing.com
Download on the App Store: https://apps.apple.com/us/app/true-joy-birthing/id6742589808

#rochesterdoula #rochesterNY #rochesterbirth #fingerlakesdoula #nydoula #rochestermidwife #birthplan #doula #firsttimemom #medicaiddoula #ny medicaid #strongmemorial #rochestergeneral #highlandhospital #unityhospital""",
        "tags": [
            "rochester doula", "rochester ny doula", "rochester midwife",
            "new york birth", "finger lakes doula", "rochester birth plan",
            "strong memorial hospital", "rochester general hospital",
            "highland hospital rochester", "unity hospital rochester",
            "ny medicaid doula", "birth plan template",
            "doula near me", "rochester pregnancy", "free birth plan",
        ],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },
    'abilene-tx': {
        'title': 'Abilene TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Abilene — now what? This guide walks you through everything: doulas and midwives serving Abilene, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Abilene doula directory → https://truejoybirthing.com/birth-support/abilene-tx/

▸ Find Abilene doulas & midwives
▸ Compare hospital options (Hendrick Medical Center, Shannon Women's & Children's)
▸ Know what doula care actually costs ($650–$1,600)
▸ Understand Texas Medicaid doula coverage (SB 750)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Abilene
0:10 — Where Abilene Families Deliver (Hospitals)
0:27 — Hendrick Medical Center
0:58 — Shannon Women's & Children's
1:24 — Crowned Birth Place
1:46 — Doulas & Midwives in Abilene
3:08 — The True Joy Birthing App
3:34 — Cost Reality ($650–$1,600)
3:57 — Insurance & Texas Medicaid
4:27 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#abilenedoula #abilenebirth #texasmedicaid #birthplan #doula #pregnancyabilene""",
        'tags': [
            'Abilene doula', 'Abilene birth doula', 'Texas Medicaid doula',
            'Abilene pregnancy guide', 'birth plan template', 'first time mom Abilene',
            'Abilene hospital maternity', 'Abilene doula cost', 'Texas birth support',
            'doula near me', 'Abilene midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Abilene', 'birth preparation',
            'Hendrick Medical Center', 'Shannon Womens Childrens Hospital',
            'Crowned Birth Place', 'SB 750 doula', 'Taylor County doula',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'apple-valley-ca': {
        'title': 'Apple Valley CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)',
        'description': """You just found out you're pregnant in Apple Valley — now what? This guide walks you through everything: doulas and midwives serving Apple Valley, hospital policies, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Apple Valley doula directory → https://truejoybirthing.com/birth-support/apple-valley-ca/

▸ Find Apple Valley doulas & midwives (LaReina Garza, High Desert Birth Services)
▸ Compare hospital options (Providence St. Mary Medical Center Level IIIB NICU)
▸ Know what doula care actually costs ($800–$2,500)
▸ Understand California Medi-Cal doula coverage ($1,500/birth package)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Apple Valley
0:13 — What this guide covers
0:31 — Providence St. Mary Medical Center
0:52 — Doulas & Midwives in Apple Valley
1:03 — The True Joy Birthing App
1:27 — Cost Reality ($800–$2,500)
1:51 — Insurance & California Medi-Cal
2:11 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#applevalleydoula #applevalleybirth #californiamedical #birthplan #doula #pregnancyapplevalley #highdesertbirth""",
        'tags': [
            'Apple Valley doula', 'birth doula', 'Medi-Cal doula',
            'pregnancy guide', 'birth plan', 'first time mom',
            'hospital maternity', 'doula cost', 'California birth',
            'doula near me', 'midwife', 'pregnancy California',
            'free birth plan', 'doula services', 'birth prep',
            'High Desert birth', 'San Bernardino doula',
            'Licensed Midwife', 'Medi-Cal coverage',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'albany-ny': {
        'title': 'Albany NY Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Albany — now what? This guide walks you through everything: doulas and midwives serving Albany, hospital policies, real costs, and whether New York Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Albany doula directory → https://truejoybirthing.com/birth-support/albany-ny/

▸ Find Albany doulas & midwives
▸ Compare hospital options (Albany Medical Center Level IV NICU, St. Peter's Hospital Level III NICU)
▸ Know what doula care actually costs ($1,000–$2,300)
▸ Understand New York Medicaid doula coverage (up to $1,710 since Jan 2024)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Albany
0:10 — Where Albany Families Deliver (Hospitals)
0:26 — Albany Medical Center (Level IV NICU)
0:40 — St. Peter's Hospital (Level III NICU)
0:54 — Doulas & Midwives in Albany
1:08 — The True Joy Birthing App
1:30 — Cost Reality ($1,000–$2,300)
1:52 — Insurance & New York Medicaid
2:11 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#albanydoula #albanybirth #newyorkmedicaid #birthplan #doula #pregnancyalbany""",
        'tags': [
            'Albany doula', 'Albany birth doula', 'New York Medicaid doula',
            'Albany pregnancy guide', 'birth plan template', 'first time mom Albany',
            'Albany hospital maternity', 'Albany doula cost', 'New York birth support',
            'doula near me', 'Albany midwife', 'pregnancy New York',
            'free birth plan', 'doula services Albany', 'birth preparation',
            'Albany Medical Center', 'St Peters Hospital Albany',
            'Capital Region doula', 'NY Medicaid doula', 'upstate New York birth',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'allen-tx': {
        'title': 'Allen TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Allen — now what? This guide walks you through everything: doulas and midwives serving Allen, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Allen doula directory → https://truejoybirthing.com/birth-support/allen-tx/

▸ Find Allen doulas & midwives
▸ Compare hospital options (Texas Health Allen Level II NICU, Medical City McKinney Level III NICU)
▸ Know what doula care actually costs ($900–$2,500)
▸ Understand Texas Medicaid doula coverage (SB 750)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Allen
0:11 — Where Allen Families Deliver (Hospitals)
0:29 — Texas Health Presbyterian Hospital Allen
1:02 — Medical City Women's Hospital McKinney
1:35 — Allen Birthing Center
1:59 — Doulas & Midwives in Allen
3:18 — The True Joy Birthing App
3:40 — Cost Reality ($900–$2,500)
4:07 — Insurance & Texas Medicaid
4:32 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#allendoula #allenbirth #texasmedicaid #birthplan #doula #pregnancyallen""",
        'tags': [
            'Allen doula', 'Allen birth doula', 'Texas Medicaid doula',
            'Allen pregnancy guide', 'birth plan template', 'first time mom Allen',
            'Allen hospital maternity', 'Allen doula cost', 'Texas birth support',
            'doula near me', 'Allen midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Allen', 'birth preparation',
            'Texas Health Presbyterian Allen', 'Medical City McKinney',
            'Allen Birthing Center', 'SB 750 doula', 'Collin County doula',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'amarillo-tx': {
        'title': 'Amarillo TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Amarillo — now what? This guide walks you through everything: doulas and midwives serving Amarillo, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Amarillo doula directory → https://truejoybirthing.com/birth-support/amarillo-tx/

▸ Find Amarillo doulas & midwives
▸ Compare hospital options (BSA Hospital Level III NICU, Northwest Texas Healthcare Level III NICU)
▸ Know what doula care actually costs ($650–$1,800)
▸ Understand Texas Medicaid doula coverage (SB 750)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Amarillo
0:12 — Where Amarillo Families Deliver (Hospitals)
0:31 — Baptist St. Anthony's Hospital
1:01 — Northwest Texas Healthcare System
1:29 — Birth Haven
2:01 — Doulas & Midwives in Amarillo
2:27 — The True Joy Birthing App
2:52 — Cost Reality ($650–$1,800)
3:17 — Insurance & Texas Medicaid
3:39 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#amarillodoula #amarillobirth #texasmedicaid #birthplan #doula #pregnancyamarillo""",
        'tags': [
            'Amarillo doula', 'Amarillo birth doula', 'Texas Medicaid doula',
            'Amarillo pregnancy guide', 'birth plan template', 'first time mom Amarillo',
            'Amarillo hospital maternity', 'Amarillo doula cost', 'Texas birth support',
            'doula near me', 'Amarillo midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Amarillo', 'birth preparation',
            'BSA Hospital Amarillo', 'Northwest Texas Healthcare',
            'Birth Haven Amarillo', 'SB 750 doula', 'Texas Panhandle doula',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'aurora-co': {
        'title': 'Aurora Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Aurora — now what? This guide walks you through everything: doulas and midwives serving Aurora, hospital policies, real costs, and whether Colorado Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Aurora doula directory → https://truejoybirthing.com/birth-support/aurora-co/

▸ Find Aurora doulas & midwives
▸ Compare hospital options (UCHealth University Level IV NICU, Sky Ridge Level III)
▸ Know what doula care actually costs ($900–$2,000)
▸ Understand Colorado Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Aurora
0:14 — Where Aurora Families Deliver (Hospitals)
0:32 — Doulas & Midwives in Aurora
0:50 — The True Joy Birthing App
1:14 — Cost Reality ($900–$2,000)
1:37 — Insurance & Colorado Medicaid
2:00 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#auroradoula #aurorabirth #coloradomedicaid #birthplan #doula #pregnancyaurora""",
        'tags': [
            'Aurora doula', 'Aurora birth doula', 'Colorado Medicaid doula',
            'Aurora pregnancy guide', 'birth plan template', 'first time mom Aurora',
            'Aurora hospital maternity', 'Aurora doula cost', 'Colorado birth support',
            'doula near me', 'Aurora midwife', 'pregnancy Colorado',
            'free birth plan', 'doula services Aurora', 'birth preparation',
            'UCHealth University Colorado', 'Sky Ridge Medical Center',
            'Anschutz Medical Campus', 'Health First Colorado',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'naperville-il': {
        'title': 'Naperville IL Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Naperville â now what? This guide walks you through everything: doulas and midwives serving Naperville, hospital policies, real costs, and how Illinois Medicaid covers doula care.

ð± Get the free app â https://truejoybirthing.com
ð Free birth plan â https://truejoybirthing.com/birth-plan-template/
ð Naperville doula directory â https://truejoybirthing.com/birth-support/naperville-il/

â¸ Find Naperville doulas & midwives (4 providers: Stefanie McMillin, Jessica Dzierzanowski, Cecily Ivey, Millie Piper)
â¸ Compare hospital options (Edward Hospital, Advocate Good Samaritan, Rush Copley)
â¸ Know what doula care actually costs ($400â$3,500)
â¸ Understand Illinois Medicaid doula coverage (up to ~$1,500 per pregnancy)
â¸ Build your free birth plan step by step

CHAPTERS:
0:00 â Welcome to Naperville
0:14 â What This Guide Covers
0:35 â Edward Hospital
0:51 â Advocate Good Samaritan
1:07 â Rush Copley Medical Center
1:22 â Doulas & Midwives in Naperville
1:37 â The True Joy Birthing App
2:02 â Cost Reality ($400â$3,500)
2:28 â Insurance & Illinois Medicaid
2:48 â Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared â all for free.

Created by Shelbi Kohler, certified birth doula.

#napervilledoula #illdoula #illinoismedicaid #birthplan #doula #pregnancynaperville""",
        'tags': [
            'Naperville doula', 'Naperville birth doula', 'Illinois Medicaid doula',
            'Naperville pregnancy guide', 'birth plan template', 'first time mom Naperville',
            'Naperville hospital maternity', 'Naperville doula cost', 'Illinois birth support',
            'doula near me', 'Naperville midwife', 'pregnancy Illinois',
            'free birth plan', 'doula services Naperville', 'birth preparation',
            'Edward Hospital', 'Advocate Good Samaritan', 'Rush Copley Medical Center',
            'Illinois Medicaid doula coverage', 'Fox Valley birth support',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
    },
    'aurora-il': {
        'title': 'Aurora IL Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Aurora — now what? This guide walks you through everything: doulas and midwives serving Aurora, hospital policies, real costs, and how Illinois Medicaid covers doula care.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Aurora doula directory → https://truejoybirthing.com/birth-support/aurora-il/

▸ Find Aurora doulas & midwives (8 listed providers)
▸ Compare hospital options (Rush-Copley Level III NICU, Northwestern Delnor, Edward Hospital)
▸ Know what doula care actually costs ($800–$2,500)
▸ Understand Illinois Medicaid doula coverage (up to $3,500 per pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Aurora
0:13 — Where Aurora Families Deliver (Hospitals)
0:31 — Rush-Copley Medical Center
0:56 — Northwestern Medicine Delnor Hospital
1:22 — Edward Hospital
1:48 — Doulas & Midwives in Aurora
2:08 — The True Joy Birthing App
2:31 — Cost Reality ($800–$2,500)
2:53 — Insurance & Illinois Medicaid
3:17 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#auroradoula #aurorabirth #illinoishmedicaid #birthplan #doula #pregnancyaurora""",
        'tags': [
            'Aurora doula', 'Aurora birth doula', 'Illinois Medicaid doula',
            'Aurora pregnancy guide', 'birth plan template', 'first time mom Aurora',
            'Aurora hospital maternity', 'Aurora doula cost', 'Illinois birth support',
            'doula near me', 'Aurora midwife', 'pregnancy Illinois',
            'free birth plan', 'doula services Aurora', 'birth preparation',
            'Rush-Copley Medical Center', 'Northwestern Medicine Delnor', 'Edward Hospital',
            'Illinois Medicaid doula coverage', 'Fox Valley birth support',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'bakersfield-ca': {
        'title': 'Bakersfield Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)',
        'description': """You just found out you're pregnant in Bakersfield — now what? This guide walks you through everything: doulas and midwives serving Bakersfield, hospital policies, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Bakersfield doula directory → https://truejoybirthing.com/birth-support/bakersfield-ca/

▸ Find Bakersfield doulas & midwives
▸ Compare hospital options (Kern Medical, Bakersfield Memorial)
▸ Know what doula care actually costs ($900–$2,200)
▸ Understand California Medi-Cal doula coverage (~$1,587)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Bakersfield
0:12 — Where Bakersfield Families Deliver (Hospitals)
0:31 — Kern Medical
0:48 — Bakersfield Memorial Hospital
1:04 — Doulas & Midwives in Bakersfield
1:20 — The True Joy Birthing App
1:45 — Cost Reality ($900–$2,200)
2:06 — Insurance & California Medi-Cal
2:30 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#bakersfielddoula #bakersfieldbirth #californiamedicaid #birthplan #doula #pregnancybakersfield""",
        'tags': [
            'Bakersfield doula', 'Bakersfield birth doula', 'California Medi-Cal doula',
            'Bakersfield pregnancy guide', 'birth plan template', 'first time mom Bakersfield',
            'Bakersfield hospital maternity', 'Bakersfield doula cost', 'California birth support',
            'doula near me', 'Bakersfield midwife', 'pregnancy California',
            'free birth plan', 'doula services Bakersfield', 'birth preparation',
            'Kern Medical', 'Bakersfield Memorial Hospital', 'Kern County birth',
            'Medi-Cal doula coverage', 'Central Valley doula',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    "boston-ma": {
        "title": "Boston MA Doula & Birth Plan Guide: Costs, Hospitals & MassHealth (First-Time Mom)",
        "description": """Planning a birth in Boston? This guide covers everything you need: doula costs, hospital options, MassHealth doula coverage, and a free birth plan app.

CHAPTERS:
0:00 — Welcome to Your Boston Birth Guide
0:12 — What We Cover
0:32 — Hospitals That Welcome Doulas
1:12 — Birth Sanctuary Cambridge
1:21 — Doulas & Midwives in Boston
1:31 — Free Birth Plan App
1:53 — Cost Reality ($1,000-$3,000)
2:11 — Insurance & MassHealth Doula Coverage
2:29 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#bostondoula #bostonbirth #massachusettsmedicaid #birthplan #doula #pregnancyboston""",
        "tags": [
            'Boston doula', 'Boston birth doula', 'Massachusetts MassHealth doula',
            'Boston pregnancy guide', 'birth plan template', 'first time mom Boston',
            'Boston hospital maternity', 'Boston doula cost', 'Massachusetts birth support',
            'doula near me', 'Boston midwife', 'pregnancy Massachusetts',
            'free birth plan', 'doula services Boston', 'birth preparation',
            'Brigham and Womens Hospital', 'Boston Medical Center', 'Massachusetts General Hospital',
            'Beth Israel Deaconess', 'Birth Sanctuary Cambridge', 'MassHealth doula coverage',
            'Boston Childrens Hospital NICU',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    "henderson-nv": {
        "title": "Henderson NV Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """You just found out you're pregnant in Henderson — now what? This guide walks you through everything: doulas and midwives serving Henderson, hospital policies, real costs, and whether Nevada Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Henderson doula directory → https://truejoybirthing.com/birth-support/henderson-nv/

▸ Find Henderson doulas & midwives
▸ Compare hospital options (Henderson Hospital, St. Rose Dominican Siena, St. Rose Dominican San Martin)
▸ Know what doula care actually costs ($1,000–$3,000)
▸ Understand Nevada Medicaid doula coverage (NV SB 392, $600–$900)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Henderson
0:16 — What We Cover
0:32 — Henderson Hospital
1:00 — St. Rose Dominican Siena
1:26 — St. Rose Dominican San Martin
1:58 — Doulas in Henderson
2:19 — More Doulas
2:36 — The True Joy Birthing App
3:00 — Cost Reality ($1,000–$3,000)
3:24 — Insurance & Nevada Medicaid
3:56 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#hendersondoula #hendersonbirth #nevadamedicaid #birthplan #doula #pregnancyhenderson""",
        "tags": [
            'Henderson doula', 'Henderson birth doula', 'Nevada Medicaid doula',
            'Henderson pregnancy guide', 'birth plan template', 'first time mom Henderson',
            'Henderson hospital maternity', 'Henderson doula cost', 'Nevada birth support',
            'doula near me', 'Henderson midwife', 'pregnancy Nevada',
            'free birth plan', 'doula services Henderson', 'birth preparation',
            'Henderson Hospital', 'St. Rose Dominican Siena', 'St. Rose Dominican San Martin',
            'NV SB 392 doula coverage', 'Las Vegas area doula',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    "columbia-md": {
        "title": "Columbia MD Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """You just found out you're pregnant in Columbia, Maryland — now what? This guide walks you through everything: doulas and midwives serving Columbia, hospital policies, real costs, and whether Maryland Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Columbia doula directory → https://truejoybirthing.com/birth-support/columbia-md/

▸ Find Columbia doulas & midwives
▸ Compare hospital options (Howard County General Hospital, Holy Cross Hospital Silver Spring)
▸ Know what doula care actually costs ($900-$2,500)
▸ Understand Maryland Medicaid doula coverage ($900/pregnancy since 2024)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Columbia
0:13 — What We Cover
0:32 — Howard County General Hospital
0:53 — Holy Cross Hospital
1:14 — DMV Birth Doulas
1:33 — Darshal Smith (Dee The Doula)
1:53 — DMV Birth Doulas C-Section Support
2:12 — The True Joy Birthing App
2:36 — Cost Reality ($900-$2,500)
2:58 — Insurance & Maryland Medicaid
3:25 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#columbiadoula #columbiabirth #marylandmedicaid #birthplan #doula #pregnancycolumbia""",
        "tags": [
            'Columbia doula', 'Columbia MD birth doula', 'Maryland Medicaid doula',
            'Columbia pregnancy guide', 'birth plan template', 'first time mom Columbia MD',
            'Howard County General Hospital', 'Holy Cross Hospital Silver Spring',
            'Columbia doula cost', 'Maryland birth support',
            'doula near me', 'Columbia midwife', 'pregnancy Maryland',
            'free birth plan', 'doula services Columbia MD', 'birth preparation',
            'DMV Birth Doulas', 'Johns Hopkins affiliate Columbia',
        ],
        "category_id": "27",  # Education
        "privacy_status": "public",
        "made_for_kids": False,
    },
    'gaithersburg-md': {
        'title': 'Gaithersburg MD Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Gaithersburg, Maryland — now what? This guide walks you through everything: doulas and midwives serving Gaithersburg, hospital policies, real costs, and whether Maryland Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Gaithersburg doula directory → https://truejoybirthing.com/birth-support/gaithersburg-md/

▸ Find Gaithersburg doulas & midwives (5 providers)
▸ Compare hospital options (Adventist HealthCare Shady Grove Level III NICU, Holy Cross Germantown Level II Nursery)
▸ Know what doula care actually costs ($600–$5,000)
▸ Understand Maryland Medicaid doula coverage (up to $900/pregnancy since 2024)
▸ Rock Creek Midwifery — home birth option for Montgomery County
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Gaithersburg
0:14 — What This Guide Covers
0:36 — Adventist HealthCare Shady Grove Medical Center (Level III NICU)
1:08 — Holy Cross Germantown Hospital (Level II Nursery)
1:37 — Rock Creek Midwifery (Home Birth Option)
2:16 — Nashare Butts — That Community Helper
2:43 — Doula Nathalie & Associates
3:14 — Womb Room Maryland Doulas
3:39 — Joni Wallace — Sun Moon & Herbs Wellness
4:08 — Jennifer Whelan — Postpartum Doula LLC
4:42 — The True Joy Birthing App
5:05 — Cost Reality ($600–$5,000)
5:38 — Insurance & Maryland Medicaid
6:14 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#gaithersburgdoula #gaithersburgmdbirth #marylandmedicaid #birthplan #doula #pregnancygaithersburg #montgomerycountydoula""",
        'tags': [
            'Gaithersburg doula', 'Gaithersburg MD birth doula', 'Maryland Medicaid doula',
            'Gaithersburg pregnancy guide', 'birth plan template', 'first time mom Gaithersburg',
            'Adventist HealthCare Shady Grove maternity', 'Holy Cross Germantown Hospital',
            'Gaithersburg doula cost', 'Maryland birth support',
            'doula near me', 'Gaithersburg midwife', 'pregnancy Maryland',
            'free birth plan', 'doula services Gaithersburg MD', 'birth preparation',
            'Montgomery County doula', 'Rock Creek Midwifery',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'unlisted',
        'made_for_kids': False,
    },
    'rockville-md': {
        'title': 'Rockville MD Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Rockville, Maryland — now what? This guide walks you through everything: doulas and midwives serving Rockville, hospital policies, real costs, and whether Maryland Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Rockville doula directory → https://truejoybirthing.com/birth-support/rockville-md/

▸ Find Rockville doulas & midwives (4 providers)
▸ Compare hospital options (Adventist HealthCare Shady Grove Level III NICU, Holy Cross Germantown Level II Nursery)
▸ Know what doula care actually costs ($900–$3,000)
▸ Understand Maryland Medicaid doula coverage (up to $900/pregnancy since 2024)
▸ Rock Creek Midwifery — home birth option for Montgomery County
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Rockville
0:15 — What This Guide Covers
0:35 — Adventist HealthCare Shady Grove Medical Center (Level III NICU)
1:10 — Holy Cross Germantown Hospital (Level II Nursery)
1:39 — Rock Creek Midwifery (Home Birth Option)
2:23 — Doula Nathalie & Associates
2:58 — Dina Piccioni — Nurturing Hands Doula Support
3:36 — Rose Quintilian — Silver Spring Doula
4:09 — Katie Baxter Doula Services
4:43 — The True Joy Birthing App
5:06 — Cost Reality ($900–$3,000)
5:33 — Insurance & Maryland Medicaid
6:12 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#rockvilledoula #rockvillemdbirth #marylandmedicaid #birthplan #doula #pregnancyrockville #montgomerycountydoula""",
        'tags': [
            'Rockville doula', 'Rockville MD birth doula', 'Maryland Medicaid doula',
            'Rockville pregnancy guide', 'birth plan template', 'first time mom Rockville',
            'Adventist HealthCare Shady Grove maternity', 'Holy Cross Germantown Hospital',
            'Rockville doula cost', 'Maryland birth support',
            'doula near me', 'Rockville midwife', 'pregnancy Maryland',
            'free birth plan', 'doula services Rockville MD', 'birth preparation',
            'Montgomery County doula', 'Rock Creek Midwifery',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    "laurel-md": {
        "title": "Laurel MD Birth Guide: Hospitals, Doulas, Costs & Medicaid",
        "description": """Planning a birth in Laurel, Maryland? This complete guide covers everything you need:

🏥 HOSPITALS
• UM Capital Region Medical Center (Level III NICU, Best Hospital 2026)
• Holy Cross Hospital Silver Spring (largest NICU in the region)

👶 DOULAS & MIDWIFES
• Local doulas serving Prince George's County
• My Way Birth (home birth midwifery in Laurel)

💰 COSTS & INSURANCE
• Doula costs in the Laurel area
• Maryland Medicaid coverage for birth services

📱 FREE BIRTH PLAN APP
Build your birth plan step by step with the True Joy Birthing app.
Download free: https://truejoybirthing.com/app

Created by Shelbi Kohler, certified birth doula.

#laureldoula #laurelmdbirth #marylandmedicaid #birthplan #doula #pregnancylaurel #princegeorgescountydoula""",
        "tags": [
            'Laurel doula', 'Laurel MD birth doula', 'Maryland Medicaid doula',
            'Laurel pregnancy guide', 'birth plan template', 'first time mom Laurel',
            'UM Capital Region maternity', 'Holy Cross Silver Spring maternity',
            'Laurel doula cost', 'Maryland birth support',
            'doula near me', 'Laurel midwife', 'pregnancy Maryland',
            'free birth plan', 'doula services Laurel MD', 'birth preparation',
            'Prince George\'s County doula', 'My Way Birth',
        ],
        "category_id": "27",  # Education
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "greenbelt-md": {
        "title": "Greenbelt MD Birth Guide: Hospitals, Doulas, Costs & Medicaid",
        "description": """Planning a birth in Greenbelt, Maryland? This complete guide covers everything you need:

🏥 HOSPITALS
• UM Capital Region Medical Center (Level III NICU, Best Hospital 2026)
• MedStar Southern Maryland Hospital Center (Level II Special Care Nursery)

👶 DOULAS & MIDWIVES
• Nathalie Grolleman (DONA-certified, birth & postpartum)
• Celina Sargusingh (birth and postpartum doula)
• Fatima Abdallah (birth doula, Arabic-speaking)
• Cean (postpartum and lactation support)
• Cheryl Washington (birth doula, community-focused)

🏠 BIRTH CENTERS
• Chesapeake Midwifery (home birth, CNM-led)
• College Park Homebirth (home birth services)

💰 COSTS & INSURANCE
• Doula costs in the Greenbelt area ($1,200-$3,000)
• Maryland Medicaid covers doula care (8:1 model, $800 for labor + 8 visits)

📱 FREE BIRTH PLAN APP
Build your birth plan step by step with the True Joy Birthing app.
Download free: https://truejoybirthing.com/app

Created by Shelbi Kohler, certified birth doula.

#greenbeltdoula #greenbeltmdbirth #marylandmedicaid #birthplan #doula #pregnancygreenbelt #princegeorgescountydoula""",
        "tags": [
            'Greenbelt doula', 'Greenbelt MD birth doula', 'Maryland Medicaid doula',
            'Greenbelt pregnancy guide', 'birth plan template', 'first time mom Greenbelt',
            'UM Capital Region maternity', 'MedStar Southern Maryland maternity',
            'Greenbelt doula cost', 'Maryland birth support',
            'doula near me', 'Greenbelt midwife', 'pregnancy Maryland',
            'free birth plan', 'doula services Greenbelt MD', 'birth preparation',
            "Prince George's County doula", 'Chesapeake Midwifery',
        ],
        "category_id": "27",  # Education
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "hartford-ct": {
        "title": "Hartford CT Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """Planning a birth in Hartford, CT? This guide covers everything you need:

CHAPTERS:
0:00 Welcome to Hartford
0:14 What this video covers
0:31 Connecticut Children's Medical Center (Level IV NICU)
0:50 Hartford Hospital (Level III NICU)
1:09 Saint Francis Hospital (Level III NICU)
1:26 NuBeing Doula Services
1:47 Mischa Hadaway - Me and My Doula LLC
2:10 Bri Rice Birth Support
2:31 MothersCare Doula Services
2:51 Free Birth Plan App
3:13 Doula Costs in Hartford ($800-$3,500)
3:29 Connecticut Medicaid (HUSKY Health) Covers Doulas
3:51 Get Started

Hartford has 3 hospitals with NICU care, 4 doula practices serving the area, and Connecticut Medicaid (HUSKY Health) covers doula services as of January 2024.

Build your free birth plan: https://truejoybirthing.com/birth-support/hartford-ct/
Download the app: https://apps.apple.com/us/app/true-joy-birthing/id6760793180

#hartforddoula #hartfordmidwife #connecticutbirth #birthplan #huskyhealth""",
        "tags": [
            'hartford doula', 'hartford midwife', 'connecticut birth',
            'Hartford Hospital', 'Saint Francis Hospital', 'Connecticut Children\'s',
            'HUSKY Health', 'doula cost Hartford', 'birth plan Hartford',
            'doula near me', 'hartford midwife', 'pregnancy Connecticut',
            'free birth plan', 'doula services Hartford CT', 'birth preparation',
            'Hartford County doula', 'NICU Level IV',
        ],
        "category_id": "27",  # Education
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "stamford-ct": {
        "title": "Stamford CT Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": "Planning a birth in Stamford, CT? This guide covers everything you need: 3 Stamford-area hospitals (Stamford Hospital, Norwalk Hospital, Greenwich Hospital), Connecticut's only freestanding birth center in Danbury, 5 local doulas with pricing from $758 to $3,500, and how CT HUSKY Health Medicaid covers doula services at ~$1,300 per pregnancy.\n\nChapters:\n0:00 Introduction\n0:11 What we cover\n0:32 Stamford Hospital\n1:04 Norwalk Hospital\n1:33 Greenwich Hospital\n1:57 Connecticut Childbirth & Women's Center\n2:28 Theresa Davis\n2:52 Allison Petrides\n3:19 Birth Partners Doulas\n3:51 MothersCare Doula Services\n4:15 Bethany Colley\n4:43 True Joy Birthing app\n5:03 Cost ranges\n5:23 CT HUSKY Health Medicaid coverage\n5:50 Free birth plan resources\n\nFree birth plan template: https://truejoybirthing.com/birth-plan-template/\nStamford doula directory: https://truejoybirthing.com/birth-support/stamford-ct/\nDownload the app: https://apps.apple.com/us/app/true-joy-birthing/id6760793180\n\n#stamfordct #stamforddoula #ctdoula #fairfieldcounty #birthdoula #postpartumdoula #midwife #birthplan #huskyhealth #connecticutbirth",
        "tags": ["stamford doula", "stamford midwife", "connecticut birth", "fairfield county doula", "stamford hospital", "norwalk hospital", "greenwich hospital", "ct husky health", "medicaid doula", "birth plan", "postpartum doula", "childbirth education"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "norwalk-ct": {
        "title": "Norwalk CT Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": "Planning a birth in Norwalk, Connecticut? This guide covers everything you need: 3 Norwalk-area hospitals (Norwalk Hospital, Stamford Hospital, Greenwich Hospital), Connecticut's only freestanding birth center in Danbury, 6 local doulas with pricing from $1,200 to $3,000, and how Connecticut HUSKY Health Medicaid covers doula services at approximately $1,300 per pregnancy.\n\nChapters:\n0:00 Introduction\n0:12 What we cover\n0:33 Norwalk Hospital\n1:06 Stamford Hospital\n1:34 Greenwich Hospital\n2:02 Connecticut Childbirth & Women's Center\n2:33 Local doulas (6 providers)\n2:58 True Joy Birthing app\n3:20 Cost ranges\n3:40 Connecticut HUSKY Health Medicaid coverage\n4:11 Free birth plan resources\n\nFree birth plan template: https://truejoybirthing.com/birth-plan-template/\nNorwalk doula directory: https://truejoybirthing.com/birth-support/norwalk-ct/\nDownload the app: https://apps.apple.com/us/app/true-joy-birthing/id6760793180\n\n#norwalkct #norwalkdoula #ctdoula #fairfieldcounty #birthdoula #postpartumdoula #midwife #birthplan #huskyhealth #connecticutbirth",
        "tags": ["norwalk doula", "norwalk midwife", "connecticut birth", "fairfield county doula", "norwalk hospital", "stamford hospital", "greenwich hospital", "ct husky health", "medicaid doula", "birth plan", "postpartum doula", "childbirth education"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "long-beach-ca": {
        "title": "Long Beach CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)",
        "description": "Planning a birth in Long Beach, CA? This guide covers everything you need: 2 Long Beach hospitals (MemorialCare Long Beach Medical Center, Dignity Health St. Mary Medical Center), 4 local doulas with pricing from $1,200 to $2,800, and how California Medi-Cal covers doula services up to $1,587 per pregnancy.\n\nChapters:\n0:00 Introduction\n0:11 What we cover\n0:32 MemorialCare Long Beach\n0:51 Dignity Health St. Mary\n1:08 Doulas of Long Beach\n1:28 Together in Birth\n1:44 Birthworkers of Color Collective\n2:02 Bianca Turner\n2:16 True Joy Birthing app\n2:36 Cost ranges\n2:56 Medi-Cal coverage\n3:20 Free birth plan resources\n\nFree birth plan template: https://truejoybirthing.com/birth-plan-template/\nLong Beach doula directory: https://truejoybirthing.com/birth-support/long-beach-ca/\nDownload the app: https://apps.apple.com/us/app/true-joy-birthing/id6760793180\n\n#longbeach #longbeachdoula #cadoula #medicaid #birthdoula #postpartumdoula #midwife #birthplan #medical #californiabirth",
        "tags": ["long beach doula", "long beach midwife", "california birth", "los angeles county doula", "memorialcare long beach", "st mary medical center", "medi-cal doula", "medicaid doula", "birth plan", "postpartum doula", "childbirth education"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "stockton-ca": {
        "title": "Stockton CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)",
        "description": "Planning a birth in Stockton, CA? This guide covers everything you need: 2 Stockton hospitals (St. Joseph's Medical Center, Dameron Hospital), 4 local doulas with pricing from $900 to $4,000, and how California Medi-Cal covers doula services up to $1,587 per pregnancy.\n\nChapters:\n0:00 Introduction\n0:13 What we cover\n0:31 St. Joseph's Medical Center\n0:49 Dameron Hospital\n1:06 Doulas serving Stockton\n1:25 True Joy Birthing app\n1:45 Cost ranges\n2:07 Medi-Cal coverage\n2:32 Free birth plan resources\n\nFree birth plan template: https://truejoybirthing.com/birth-plan-template/\nStockton doula directory: https://truejoybirthing.com/birth-support/stockton-ca/\nDownload the app: https://apps.apple.com/us/app/true-joy-birthing/id6760793180\n\n#stockton #stocktondoula #cadoula #medicaid #birthdoula #postpartumdoula #midwife #birthplan #medical #californiabirth",
        "tags": ["stockton doula", "stockton midwife", "california birth", "san joaquin county doula", "st josephs medical center", "dameron hospital", "medi-cal doula", "medicaid doula", "birth plan", "postpartum doula", "childbirth education"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "new-haven-ct": {
        "title": "New Haven CT Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """Planning a birth in New Haven, CT? This guide covers everything you need: 2 New Haven hospitals (Yale New Haven Hospital with Level IV NICU, Yale New Haven Children's Hospital), 6 local doulas with pricing from $800 to $3,479, and how CT HUSKY Health Medicaid currently does not cover doula services.

Chapters:
0:00 Introduction
0:12 What we cover
0:28 Yale New Haven Hospital
1:03 Yale New Haven Children's Hospital
1:25 Local doulas (6 providers)
2:17 True Joy Birthing app
2:42 Cost ranges
3:03 CT Medicaid coverage
3:35 Free birth plan resources

Free birth plan template: https://truejoybirthing.com/birth-plan-template/
New Haven doula directory: https://truejoybirthing.com/birth-support/new-haven-ct/
Download the app: https://apps.apple.com/us/app/true-joy-birthing/id6760793180

#newhavenct #newhavendoula #ctdoula #yale #birthdoula #postpartumdoula #midwife #birthplan #huskyhealth #connecticutbirth""",
        "tags": [
            'new haven doula', 'new haven midwife', 'connecticut birth',
            'Yale New Haven Hospital', "Yale New Haven Children's Hospital",
            'HUSKY Health', 'doula cost New Haven', 'birth plan New Haven',
            'doula near me', 'new haven midwife', 'pregnancy Connecticut',
            'free birth plan', 'doula services New Haven CT', 'birth preparation',
            'New Haven County doula', 'NICU Level IV',
        ],
        "category_id": "27",  # Education
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "charleston-sc": {
        "title": "Charleston SC Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """Planning a birth in Charleston, South Carolina? This complete guide walks you through everything you need to know.

🏥 HOSPITALS COVERED:
• MUSC Health University Medical Center — Level IV NICU, academic medical center
• Roper St. Francis Healthcare — largest private system in the Lowcountry
• Trident Medical Center — 2,800+ births/year, holistic birthing suites

🏡 BIRTH CENTER:
• Charleston Birth Place — the Lowcountry's only freestanding birth center, midwife-led since 2008

🤱 DOULAS FEATURED:
• Sabine Baker (Doulacare Charleston) — $1,000-$2,000
• Christina Deleon (Latch onto Health) — IBCLC, $35-$85/hr
• Professional Doulas of Charleston — $900-$2,200
• Laurie Vaughn (Lowcountry Childbirth) — $1,500
• Norma Simpson (Beyond Earthside) — $1,200-$1,800, sliding scale

💰 COSTS:
• Doula: $900-$2,200
• SC Medicaid covers doula services (since 2024)

📱 FREE APP:
Build your birth plan with the True Joy Birthing app — 9 guided sections, find doulas near you, export PDF. No account needed.
👉 https://truejoybirthing.com/birth-support/charleston-sc/

⏱️ CHAPTERS:
0:00 Intro — Charleston Birth Guide
0:12 What This Video Covers
0:29 MUSC Health University Medical Center
0:55 Roper St. Francis Healthcare
1:22 Trident Medical Center
1:51 Charleston Birth Place (Freestanding Birth Center)
2:19 Doulas & Midwives in Charleston
4:58 Free Birth Plan App
5:18 Doula Costs in Charleston
5:43 South Carolina Medicaid Coverage
6:10 Build Your Birth Plan

#charlestonsc #charlestondoula #scdoula #birthdoula #postpartumdoula #midwife #birthplan #scmedicaid #southcarolinabirth #muschealth #roperstfrancis #tridentmedical #charlestonbirthplace #freebirthplan #doulaservices""",
        "tags": [
            'charleston doula', 'charleston midwife', 'south carolina birth',
            'MUSC Health', 'Roper St. Francis', 'Trident Medical Center',
            'Charleston Birth Place', 'SC Medicaid doula', 'doula cost Charleston',
            'birth plan Charleston', 'doula near me', 'charleston sc birth',
            'free birth plan', 'doula services Charleston SC', 'birth preparation',
            'Lowcountry doula', 'NICU Level IV',
        ],
        "category_id": "27",  # Education
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "bozeman-mt": {
        "title": "Bozeman MT Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """Planning a birth in Bozeman, Montana? This complete guide covers everything you need: hospitals, birth centers, doulas, midwives, costs, and Medicaid coverage.

What's inside:
- Bozeman Health Deaconess Regional Medical Center (Level II NICU, midwifery, water labor)
- Bozeman Birth Center (freestanding, Medicaid-accepting, water birth, home birth options)
- 8 local doulas and midwives with cost ranges from $800 to $3,495
- Doula costs ($800-$3,000) and midwifery costs ($6,500-$8,000)
- Montana Medicaid status: SB 319 passed but implementation paused
- Free birth plan app walkthrough

Chapters:
0:00 Intro
0:12 What We Cover
0:29 Bozeman Health Deaconess Regional Medical Center
1:17 Bozeman Birth Center (Freestanding Birth Center)
2:13 Bozeman Doulas & Midwives
2:57 Free Birth Plan App
3:27 Doula Costs in Bozeman
3:58 Montana Medicaid Coverage
4:32 Build Your Birth Plan

#bozemanmt #bozemandoula #mtdoula #birthdoula #postpartumdoula #midwife #birthplan #montanamedicaid #montanabirth #bozemanhealth #deaconess #bozemanbirthcenter #freebirthplan #doulaservices #gallatinvalley""",
        "tags": [
            'bozeman doula', 'bozeman midwife', 'montana birth',
            'Bozeman Health Deaconess', 'Bozeman Birth Center',
            'MT Medicaid doula', 'doula cost Bozeman', 'birth plan Bozeman',
            'doula near me', 'bozeman mt birth', 'free birth plan',
            'doula services Bozeman MT', 'birth preparation', 'gallatin valley doula',
            'NICU Level II', 'water birth Montana',
        ],
        "category_id": "27",  # Education
        "privacy_status": "public",
        "made_for_kids": False,
    },
    'port-st-lucie-fl': {
        'title': 'Port St. Lucie Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Port St. Lucie — now what? This guide walks you through everything: doulas and midwives serving Port St. Lucie, hospital policies, real costs, and whether Florida Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Port St. Lucie doula directory → https://truejoybirthing.com/birth-support/port-st-lucie-fl/

▸ Find Port St. Lucie doulas & midwives (3+ providers)
▸ Compare hospital options (Cleveland Clinic Martin Health – Tradition, Cleveland Clinic Martin Health – Martin North, St. Lucie Medical Center)
▸ Know what doula care actually costs ($1,200–$2,500)
▸ Understand Florida Medicaid doula coverage (not covered as of 2026)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Port St. Lucie
0:14 — Where Port St. Lucie Families Deliver
0:30 — Cleveland Clinic Martin Health – Tradition Hospital (Level II)
0:50 — Cleveland Clinic Martin Health – Martin North Hospital (Level III)
1:10 — St. Lucie Medical Center (Level II)
1:30 — Doulas & Midwives in Port St. Lucie
2:30 — The True Joy Birthing App
2:47 — Cost Reality ($1,200–$2,500)
3:13 — Insurance & Florida Medicaid
3:45 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#portstluciedoula #pslbirth #floridabirth #birthplan #doula #pregnancyportstlucie""",
        'tags': [
            'Port St. Lucie doula', 'Port St. Lucie birth doula', 'Florida Medicaid doula',
            'Port St. Lucie pregnancy guide', 'birth plan template', 'first time mom Port St. Lucie',
            'Cleveland Clinic Martin Health', 'St. Lucie Medical Center', 'Tradition Hospital',
            'Port St. Lucie doula cost', 'Florida birth support',
            'doula near me', 'Port St. Lucie midwife', 'pregnancy Florida',
            'free birth plan', 'doula services Port St. Lucie', 'birth preparation',
            'Treasure Coast doula', 'St. Lucie County birth',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'columbus-oh': {
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
        'title': 'Columbus Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Columbus — now what? This guide walks you through everything: doulas and midwives serving Columbus, hospital policies, real costs, and whether Ohio Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Columbus doula directory → https://truejoybirthing.com/birth-support/columbus-oh/

▸ Find Columbus doulas & midwives
▸ Compare hospital options (OhioHealth Riverside Methodist, OSU Wexner, Mount Carmel East)
▸ Know what doula care actually costs ($700–$2,500)
▸ Understand Ohio Medicaid doula coverage (since 2024)
▸ Build your free birth plan step by step

#ColumbusOH #ColumbusOhio #Doula #Midwife #BirthPlan #Pregnancy #FirstTimeMom #TrueJoyBirthing""",
        'tags': ['Columbus OH doula', 'Columbus Ohio midwife', 'Columbus birth plan', 'Ohio Medicaid doula', 'first time mom Columbus', 'Columbus hospitals birth', 'True Joy Birthing'],
    },
    'oklahoma-city-ok': {
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
        'title': 'Oklahoma City Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Oklahoma City — now what? This guide walks you through everything: doulas and midwives serving OKC, hospital policies, real costs, and whether SoonerCare covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 OKC doula directory → https://truejoybirthing.com/birth-support/oklahoma-city-ok/

▸ Find OKC doulas & midwives (7 providers)
▸ Compare hospital options (OU Health — Level IV NICU, Mercy Hospital — Level III, Integris Baptist — Level III)
▸ Visit the Oklahoma City Birth Center (Midtown, midwife-run)
▸ Know what doula care actually costs ($1,200–$2,500)
▸ Understand SoonerCare doula coverage (covers since 2024)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Oklahoma City
0:13 — What We Cover
0:30 — OU Health University of Oklahoma Medical Center (Level IV NICU)
1:25 — Mercy Hospital Oklahoma City (Level III NICU)
2:15 — Integris Baptist Medical Center (Level III NICU)
2:58 — Oklahoma City Birth Center
3:47 — Doulas & Midwives in OKC
4:33 — The True Joy Birthing App
5:00 — Cost Reality ($1,200–$2,500)
5:27 — Insurance & SoonerCare
6:06 — Your Next Step: Build Your Birth Plan

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#oklahomacitydoula #okcdoula #oklahomabirth #doulaokc #birthplan #pregnancyokc #soonerccare #ouhealth #mercyhospitalokc #integrisbaptist #oklahomacitybirthcenter #firsttimemom #freebirthplan #birthpreparation #trujoybirthing""",
        'tags': ['Oklahoma City doula', 'OKC doula', 'Oklahoma birth', 'SoonerCare doula', 'OU Health', 'Mercy Hospital Oklahoma City', 'Integris Baptist', 'OKC Birth Center', 'birth plan Oklahoma City', 'first time mom OKC', 'pregnancy Oklahoma City', 'free birth plan', 'True Joy Birthing'],
    },
    'eugene-or': {
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
        'title': 'Eugene Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Eugene — now what? This guide walks you through everything: doulas and midwives serving Eugene, hospital policies, real costs, and whether Oregon Health Plan covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Eugene doula directory → https://truejoybirthing.com/birth-support/eugene-or/

▸ Find Eugene doulas & midwives (5 providers)
▸ Compare 2 hospitals:
    • PeaceHealth Sacred Heart RiverBend (Level III NICU, Baby-Friendly)
    • McKenzie-Willamette Medical Center (Level II NICU)
▸ Visit Oregon Birth and Wellness Center (freestanding birth center, Springfield)
▸ Know what doula care actually costs ($1,000–$3,000)
▸ Understand Oregon Health Plan doula coverage (OHP covers statewide)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Eugene
0:12 — What This Guide Covers
0:32 — PeaceHealth Sacred Heart RiverBend (Level III NICU)
1:09 — McKenzie-Willamette Medical Center (Level II NICU)
1:41 — Oregon Birth and Wellness Center
2:13 — Doulas & Midwives in Eugene
4:19 — The True Joy Birthing App
4:40 — Cost Reality ($1,000–$3,000)
5:04 — Insurance & Oregon Health Plan
5:28 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#eugeneoregondoula #eugenedoula #oregonbirth #doulaeugene #birthplan #pregnancyeugene #oregonhealthplan #peacehealth #mckenziewillamette #oregonbirthandwellness #willamettevalley #firsttimemom #freebirthplan #birthpreparation #truejoybirthing""",
        'tags': ['Eugene doula', 'Eugene Oregon doula', 'Oregon birth', 'OHP doula', 'PeaceHealth Sacred Heart', 'McKenzie-Willamette', 'Oregon Birth and Wellness Center', 'birth plan Eugene', 'first time mom Eugene', 'pregnancy Eugene', 'free birth plan', 'True Joy Birthing', 'Willamette Valley doula'],
    },
    'tulsa-ok': {
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
        'title': 'Tulsa Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Tulsa — now what? This guide walks you through everything: doulas and midwives serving Tulsa, hospital policies, real costs, and whether Oklahoma Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Tulsa doula directory → https://truejoybirthing.com/birth-support/tulsa-ok/

▸ Find Tulsa doulas & midwives (4 providers)
▸ Compare 3 hospitals:
    • Hillcrest Medical Center (Level III NICU, Baby-Friendly, TeamBirth)
    • Saint Francis Hospital (Level IV NICU, U.S. News High Performing)
    • OU Health Tulsa (Level III NICU, CNM midwifery, CenteringPregnancy)
▸ Visit 3 freestanding birth centers:
    • Special Delivery Midwifery Care (open since 2012)
    • Tulsa Birth Center (midwifery-model care)
    • Given Women's Health Oasis (community-based, north Tulsa)
▸ Know what doula care actually costs ($800–$2,400)
▸ Understand Oklahoma Medicaid doula coverage (SB 753)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Tulsa
0:12 — What This Guide Covers
0:29 — Hillcrest Medical Center (Level III NICU)
0:42 — Saint Francis Hospital (Level IV NICU)
0:54 — OU Health Tulsa (Level III NICU)
1:12 — Special Delivery Midwifery Care
1:26 — Tulsa Birth Center
1:40 — Given Women's Health Oasis
1:53 — Doulas & Midwives in Tulsa
2:09 — The True Joy Birthing App
2:37 — Cost Reality ($800–$2,400)
3:02 — Insurance & Oklahoma Medicaid
3:23 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#tulsadoula #tulsaokdoula #oklahomabirth #doulatulsa #birthplan #pregnancytulsa #oklahomamedicaid #sooner #hillcrest #saintfrancistulsa #ouhealth #specialdeliverymidwifery #tulsaoklahoma #firsttimemom #freebirthplan #birthpreparation #truejoybirthing""",
        'tags': ['Tulsa doula', 'Tulsa Oklahoma doula', 'Oklahoma birth', 'SoonerCare doula', 'Hillcrest Medical Center', 'Saint Francis Hospital', 'OU Health Tulsa', 'Special Delivery Midwifery', 'Tulsa Birth Center', 'birth plan Tulsa', 'first time mom Tulsa', 'pregnancy Tulsa', 'free birth plan', 'True Joy Birthing', 'Oklahoma Medicaid doula'],
    },
    'indianapolis-in': {
        'title': 'Indianapolis Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Indianapolis — now what? This guide walks you through everything: doulas and midwives serving Indianapolis, hospital policies, real costs, and whether Indiana Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Indianapolis doula directory → https://truejoybirthing.com/birth-support/indianapolis-in/

▸ Find Indianapolis doulas & midwives
▸ Compare hospital options (IU Health Methodist, Ascension St. Vincent, Community East)
▸ Know what doula care actually costs ($800–$1,800)
▸ Understand Indiana Medicaid doula coverage (HB 1008, Jan 2025)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Indianapolis
0:32 — What This Guide Covers
0:52 — IU Health Methodist (Level IV NICU)
1:15 — Ascension St. Vincent (Level III NICU)
1:39 — Community Hospital East (Level II NICU)
2:07 — Doulas & Midwives in Indianapolis
4:06 — The True Joy Birthing App
4:37 — Cost Reality ($800–$1,800)
5:02 — Insurance & Indiana Medicaid
5:18 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#indianapolisdoula #indianapolisbirth #indianamedicaid #birthplan #doula #pregnancyindianapolis #IUHealthMethodist #ascensionstvincent #communityhospitaleast #indianabirth #firsttimemom #freebirthplan #birthpreparation #truejoybirthing""",
        'tags': ['Indianapolis doula', 'Indianapolis birth doula', 'Indiana Medicaid doula', 'Indianapolis pregnancy guide', 'birth plan template', 'first time mom Indianapolis', 'IU Health Methodist maternity', 'Ascension St. Vincent Indianapolis', 'Community Hospital East', 'Indianapolis doula cost', 'Indiana birth support', 'doula near me', 'Indianapolis midwife', 'pregnancy Indiana', 'free birth plan', 'doula services Indianapolis', 'birth preparation', 'HB 1008 doula'],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'hendersonville-tn': {
        'title': 'Hendersonville TN Doula & Birth Plan Guide: Costs, Hospitals & Insurance (First-Time Mom)',
        'description': """Planning a birth in Hendersonville, Tennessee? This video walks you through everything you need to know.

HOSPITALS COVERED:
- TriStar Hendersonville Medical Center (Level II NICU, doulas welcome, TennCare accepted)
- Sumner Regional Medical Center (Level II NICU, doulas welcome, TennCare accepted)

DOULAS & MIDWIVES:
- East Nashville Doula (Birth & Postpartum Doula, $1,200-$2,500)
- Hallee Watson (Birth & Postpartum Doula, $1,200-$2,500)
- By Your Side Family Doula (CLC, Postpartum Doula, $1,200-$2,500)
- Ema Balos, ICCE (Empowered Birthing Doula Services, $1,200-$2,200)
- Gaylea McDougal, CPM (Sumner County Childbirth & Beyond, $3,000-$5,000 home birth)

COSTS:
- Doulas: $800-$2,500
- Home Birth Midwife: $3,000-$5,000
- Most doulas offer payment plans and sliding-scale spots

INSURANCE:
- Tennessee TennCare does NOT cover doula services as of 2026
- Check with private insurance for out-of-network reimbursement
- HSA/FSA funds may help cover costs

FREE TOOLS:
- True Joy Birthing App (iOS): Build your birth plan step by step
- Free PDF Birth Plan Template: https://truejoybirthing.com/birth-plan-template/
- Full Hendersonville Guide: https://truejoybirthing.com/birth-support/hendersonville-tn/

#hendersonvilledoula #tennesseebirth #sumnercounty #birthplan #doula #midwife #tristarhendersonville""",
        'tags': ['hendersonville doula', 'hendersonville midwife', 'tennessee birth', 'sumner county doula', 'nashville doula', 'birth plan', 'tristar hendersonville', 'sumner regional medical center', 'doula cost tennessee', 'tenncare doula', 'home birth tennessee', 'certified professional midwife', 'birth support hendersonville', 'free birth plan', 'doula services hendersonville', 'pregnancy hendersonville tn', 'first time mom tennessee', 'birth guide hendersonville'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'memphis-tn': {
        'title': 'Memphis Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Memphis — now what? This guide walks you through everything: doulas and midwives serving Memphis, hospital policies, real costs, and your insurance options.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Memphis doula directory → https://truejoybirthing.com/birth-support/memphis-tn/

▸ Find Memphis doulas & midwives (Memphis Doulas, Black Doula in Memphis, River City Doulas, Memphis Birth Collective)
▸ Compare hospital options (Methodist Le Bonheur, Baptist Memorial, Regional One Health)
▸ Know what doula care actually costs ($700–$1,700)
▸ Understand Tennessee Medicaid (TennCare) doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Memphis
0:12 — What This Video Covers
0:31 — Methodist University Hospital (Level IV NICU)
1:07 — Baptist Memorial Hospital-Memphis (Level III NICU)
1:38 — Regional One Health (CNM Midwifery)
2:07 — Memphis Doulas (Naturally Nurtured Birth Services)
2:29 — Black Doula in Memphis (WhatTheDoula)
2:52 — River City Doulas
3:13 — Memphis Birth Collective
3:39 — The True Joy Birthing App
4:05 — Cost Reality ($700–$1,700)
4:37 — Insurance & Tennessee Medicaid (TennCare)
5:10 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#memphisdoula #memphisbirth #tennesseemedicaid #birthplan #doula #pregnancymemphis""",
        'tags': [
            'Memphis doula', 'Memphis birth doula', 'Tennessee Medicaid doula',
            'Memphis pregnancy guide', 'birth plan template', 'first time mom Memphis',
            'Methodist Le Bonheur maternity', 'Baptist Memorial Memphis maternity',
            'Regional One Health Memphis', 'Memphis doula cost',
            'doula near me', 'Memphis midwife', 'pregnancy Tennessee',
            'free birth plan', 'doula services Memphis', 'birth preparation',
            'TennCare doula', 'Shelby County doula', 'Memphis birth collective',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'lehi-ut': {
        'title': 'Lehi UT Doula & Birth Plan Guide: Costs, Hospitals & Insurance (First-Time Mom)',
        'description': """Planning a birth in Lehi, Utah? This video walks you through everything you need to know.

HOSPITALS COVERED:
- American Fork Hospital (Level II NICU, doulas welcome, Medicaid accepted)
- Utah Valley Hospital (Level III NICU, doulas welcome, Medicaid accepted)
- Timpanogos Regional Hospital (Level II NICU, doulas welcome, Medicaid accepted)

DOULAS & MIDWIVES:
- Aleece Weaver (DONA, ProDoula, EggBaby Doula Services, $1,200-$2,500)
- Madison Gordon (Catching Bubbles, $2,000 birth, $45/hr postpartum)
- Krystalyn Leffler-Macon (CD(DTI), The Space Doula Care, $1,200 birth)
- Shay Crowther (CD(DONA), RootedBirth Doulas, $1,200 birth package)

COSTS:
- Doulas: $800-$1,800 (below national average)
- Utah's large LDS doula community keeps prices accessible
- HSA/FSA funds can cover doula fees
- Some Silicon Slopes tech employers offer doula benefits

INSURANCE:
- Utah Medicaid does NOT cover doula services
- HB 222 (2024) proposed coverage but did not pass
- Check with private insurance for out-of-network reimbursement
- HSA/FSA funds may help cover costs

FREE TOOLS:
- True Joy Birthing App (iOS): Build your birth plan step by step
- Free PDF Birth Plan Template: https://truejoybirthing.com/birth-plan-template/
- Full Lehi Guide: https://truejoybirthing.com/birth-support/lehi-ut/

#lehidoula #utahbirth #utahcounty #birthplan #doula #midwife #americanforkhospital #utahvalleyhospital #timpanogosregional #doula cost utah #silicon slopes #birth support lehi #free birth plan #doula services lehi #pregnancy lehi ut #first time mom utah #birth guide lehi""",
        'tags': ['lehi doula', 'lehi midwife', 'utah birth', 'utah county doula', 'american fork hospital', 'utah valley hospital', 'timpanogos regional hospital', 'birth plan', 'doula cost utah', 'medicaid doula utah', 'home birth utah', 'certified professional midwife', 'birth support lehi', 'free birth plan', 'doula services lehi', 'pregnancy lehi ut', 'first time mom utah', 'birth guide lehi', 'silicon slopes doula', 'intermountain health'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    "newark-nj": {
        'title': "Newark NJ Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        'description': """Planning a birth in Newark, NJ? This complete city guide covers everything you need:

🏥 Hospitals in Newark:
• Newark Beth Israel Medical Center — Level IV NICU, RWJBarnabas Health, Best Maternity Care Hospital (Newsweek)
• University Hospital (Rutgers NJMS) — Level III NICU, Baby-Friendly USA designated, lowest C-section rates in NJ
• Saint Michael's Medical Center — Level II NICU, Top 100 Hospital, Leapfrog A grade

🤱 Doulas & Midwives Serving Newark:
• RWJBarnabas Health Doula Program
• The Nesting Place — CD(DONA), 5.0 rating from 233 Google reviews
• Tyreema Muhannad — Certified Labor & Postpartum Doula (Madriella)
• Wislene Saint-Vil — Glorious Push Birth Services, multilingual support
• Erica Castillo — Full-spectrum doula, Ancient Song trained
• Keshia Jackman — Community doula, BSN, Melodious Roots Doula
• Monique Higgins — Lovely Empowerment Networking System

💳 Costs & Insurance:
• Doula costs: $1,200–$4,000 (payment plans available)
• New Jersey Medicaid covers doula services: $1,540 per pregnancy (as of 2024)
• Many doulas accept NJ Medicaid (Horizon NJ Health, Aetna Better Health, United Healthcare Community Plan)

📱 Free Birth Plan App:
• Build your birth plan step by step — 9 guided sections
• Find and message doulas and midwives near you
• Export a PDF to share with your provider
• Free. No account needed. Works on iPhone.

⏱️ Chapters:
0:00 Congratulations — Newark Birth Guide
0:11 What This Video Covers
0:30 Newark Beth Israel Medical Center (Level IV NICU)
1:10 University Hospital (Rutgers NJMS) — Baby-Friendly
1:42 Saint Michael's Medical Center (Level II NICU)
2:09 Doulas & Midwives Serving Newark
2:30 Free Birth Plan App
2:52 Doula Costs in Newark
3:15 New Jersey Medicaid Covers Doulas
3:41 Build Your Birth Plan

Download the free app: https://truejoybirthing.com
Browse Newark doulas: https://truejoybirthing.com/birth-support/newark-nj/

#newarkdoula #newarknj #newjerseybirthplan #njmedicaid #newarkbirthguide #doulanewarknj #birthplan #firsttimemom #rwjbarnabas #universityhospitalnewark""",
        'tags': ['newark doula', 'newark nj doula', 'new jersey birth plan', 'newark midwife', 'nj medicaid doula', 'newark birth guide', 'first time mom newark', 'newark beth israel', 'university hospital newark', 'saint michaels medical center', 'rwjbarnabas health', 'ancient song doula', 'new jersey medicaid doula', 'essex county doula', 'birth plan app', 'true joy birthing'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    "rancho-cucamonga-ca": {
        "title": "Rancho Cucamonga CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)",
        "description": """Planning a birth in Rancho Cucamonga, CA? This guide covers everything you need: hospital options (San Antonio Regional Hospital, Arrowhead Regional Medical Center), The Natural Birth Place birth center, local doulas (Selina Pasillas, Annie Griffith, Nicole Jones, Lauren Pancucci), doula costs ($1,000-$2,500), California Medi-Cal doula coverage through the PAVE program (up to $1,587 per pregnancy), and a free birth plan app.

CHAPTERS:
0:00 Intro
0:13 What This Guide Covers
0:31 San Antonio Regional Hospital
1:01 Arrowhead Regional Medical Center
1:32 The Natural Birth Place
2:07 Local Doulas & Midwives
4:18 Free Birth Plan App
4:43 Doula Costs in Rancho Cucamonga
5:13 Medi-Cal & Insurance Coverage
5:44 Get Your Free Birth Plan

Download the free birth plan app: https://truejoybirthing.com/birth-plan
Find doulas and midwives in Rancho Cucamonga: https://truejoybirthing.com/birth-support/rancho-cucamonga-ca/

#ranchoCucamongaDoula #ranchoCucamongaMidwife #californiaBirth #inlandempiredoula #sanantonioRegionalHospital #arrowheadregional #naturalbirthplace #mediCaldoula #birthplan #doulaCosts""",
        "tags": ["rancho cucamonga doula", "rancho cucamonga midwife", "california birth", "inland empire doula", "san antonio regional hospital", "arrowhead regional medical center", "natural birth place", "medi-cal doula", "birth plan", "doula costs"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "grand-rapids-mi": {
        'title': "Grand Rapids MI Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        'description': """Planning a birth in Grand Rapids, MI? This complete city guide covers everything you need:

🏥 Hospitals in Grand Rapids:
• Corewell Health Butterworth Hospital — Level IV NICU, flagship academic medical center on the Medical Mile
• Trinity Health Grand Rapids Hospital — Level II NICU, community-oriented labor unit

🤱 Doulas & Midwives Serving Grand Rapids:
• Blessed Birth Doulas — Birth Doula, Spinning Babies-trained, $1,400 standard ($500 WIC families)
• Bump to Birth (Kiara Baskin) — CD, CLC, $1,200-$2,500 market range
• Great Lakes Doulas — sliding-scale fees, $1,200-$2,000

💳 Costs & Insurance:
• Doula costs: $1,200–$2,500 (payment plans and sliding scale available)
• Michigan Medicaid covers doula services: 12 visits per pregnancy, $1,500 reimbursement rate
• Many doulas accept HSA/FSA payments

📱 Free Birth Plan App:
• Build your birth plan step by step — 9 guided sections
• Find and message doulas and midwives near you
• Export a PDF to share with your provider
• Free. No account needed. Works on iPhone.

⏱️ Chapters:
0:00 Congratulations — Grand Rapids Birth Guide
0:12 What This Video Covers
0:29 Corewell Health Butterworth Hospital (Level IV NICU)
0:44 Trinity Health Grand Rapids (Level II NICU)
1:01 West Michigan Midwifery Birth Center
1:21 Doulas & Midwives Serving Grand Rapids
1:38 Free Birth Plan App
2:17 Doula Costs in Grand Rapids
2:41 Michigan Medicaid Covers Doulas
3:03 Build Your Birth Plan

Download the free app: https://truejoybirthing.com
Browse Grand Rapids doulas: https://truejoybirthing.com/birth-support/grand-rapids-mi/

#grandrapidsdoula #grandrapidsmi #michiganbirthplan #mimedicaid #grandrapidsbirthguide #doulagrandrapids #birthplan #firsttimemom #corewellhealth #trinityhealthgrandrapids #westmichiganmidwifery #michiganmedicaiddoula #kentcountydoula #birthplanapp #truejoybirthing""",
        'tags': ['grand rapids doula', 'grand rapids mi doula', 'michigan birth plan', 'grand rapids midwife', 'mi medicaid doula', 'grand rapids birth guide', 'first time mom grand rapids', 'corewell health butterworth', 'trinity health grand rapids', 'west michigan midwifery', 'michigan medicaid doula', 'kent county doula', 'birth plan app', 'true joy birthing'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },

    'albuquerque-nm': {
        'title': 'Albuquerque Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you\u2019re pregnant in Albuquerque \u2014 now what? This guide walks you through everything: doulas and midwives serving Albuquerque, hospital policies, real costs ($725-$1,650), and whether New Mexico Medicaid covers a doula (yes \u2014 Centennial Care does!).

Albuquerque doula directory \u2192 https://truejoybirthing.com/birth-support/albuquerque-nm/

Chapters:
0:00 Congratulations!
0:13 What this guide covers
0:36 UNM Hospital (Level IV NICU)
1:00 Presbyterian Hospital (Level III NICU)
1:22 Lovelace Women's Hospital (Level III NICU)
1:46 Dar a Luz Birth Center (water birth)
2:16 Doulas serving Albuquerque
3:24 Free birth plan app
3:46 How much does a doula cost?
4:07 Does Medicaid cover doulas?
4:33 Get your free birth plan

#abqdoula #albuquerquebirth #newmexicomedicaid #birthplan #doula #pregnancyabq""",
        'tags': ['albuquerque doula', 'albuquerque birth', 'new mexico doula', 'doula cost', 'birth plan', 'medicaid doula', 'pregnancy albuquerque', 'doula albuquerque nm', 'midwife albuquerque', 'birth center albuquerque', 'dar a luz', 'unm hospital', 'presbyterian hospital', 'lovelace womens hospital'],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'garden-grove-ca': {
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
        'title': 'Garden Grove Doula \u0026 Birth Plan Guide: Costs, Hospitals \u0026 Medi-Cal (First-Time Mom)',
        'description': """You just found out you're pregnant in Garden Grove — now what? This guide walks you through everything: doulas and midwives serving Garden Grove, hospital policies at MemorialCare Orange Coast Medical Center, UCI Medical Center, and Hoag Hospital Newport Beach, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Garden Grove doula directory → https://truejoybirthing.com/birth-support/garden-grove-ca/

▸ Find Garden Grove doulas \u0026 midwives (6 providers)
▸ Compare hospital options (MemorialCare Orange Coast, UCI Medical Center, Hoag Newport Beach)
▸ Explore birth center options (South Coast Midwifery in Irvine)
▸ Know what doula care actually costs ($600–$2,800)
▸ Understand California Medi-Cal doula coverage (SB-509, ~$1,587/birth)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Garden Grove
0:13 — What This Video Covers
0:31 — MemorialCare Orange Coast Medical Center (Fountain Valley)
0:52 — UCI Medical Center (Orange)
1:18 — Hoag Hospital Newport Beach
1:45 — South Coast Midwifery (Irvine)
2:13 — Doulas \u0026 Midwives in Garden Grove
2:36 — The True Joy Birthing App
3:00 — Cost Reality ($600–$2,800)
3:22 — Medi-Cal \u0026 Insurance
3:54 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#gardengrovedoula #gardengrovebirth #californiamedicaid #birthplan #doula #pregnancygardengrove #southerncaliforniabirth #orangecountydoula""",
        'tags': [
            'Garden Grove doula', 'Garden Grove birth doula', 'California Medi-Cal doula',
            'Garden Grove pregnancy guide', 'birth plan template', 'first time mom Garden Grove',
            'Garden Grove hospital maternity', 'Garden Grove doula cost', 'California birth support',
            'doula near me', 'Garden Grove midwife', 'pregnancy California',
            'free birth plan', 'doula services Garden Grove', 'birth preparation',
            'MemorialCare Orange Coast', 'UCI Medical Center', 'Hoag Hospital Newport Beach',
            'South Coast Midwifery', 'Orange County doula',
        ],
    },
    'glendale-ca': {
        'title': "Glendale CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)",
        'description': "You just found out you're pregnant in Glendale, now what? This guide walks you through everything: 4 doulas serving Glendale, hospital policies at Adventist Health Glendale and Glendale Memorial Hospital, the nearest birth center at Moxie Birth in South Pasadena, cost ranges from $1,200 to $3,500, and how California Medi-Cal covers doula care through the PAVE program.\n\nChapters:\n0:00 Intro\n0:14 What we cover\n0:32 Adventist Health Glendale\n0:58 Glendale Memorial Hospital\n1:25 Moxie Birth Center (South Pasadena)\n1:53 Jill Magoffin, DONA Doula\n2:22 Kiley Tkaczyk, Doula and Birth Photographer\n2:44 Iliana Ipes, Birth and Postpartum Doula\n3:04 Veronica Hinojosa-Stang, NICU Doula\n3:27 Free Birth Plan App\n3:49 Doula Costs in Glendale\n4:18 Medi-Cal Doula Coverage (PAVE Program)\n4:45 Get Your Free Birth Plan\n\nDownload the free birth plan: https://truejoybirthing.com/birth-plan-template/\nFind doulas in Glendale: https://truejoybirthing.com/birth-support/glendale-ca/\n\n#glendaledoula #glendalemidwife #californiabirth #doula #birthplan #adventisthealthglendale #glendalememorialhospital #medicaid-doula #doula #birthsupport",
        'tags': ['glendale doula', 'glendale midwife', 'california birth', 'doula glendale ca', 'adventist health glendale', 'glendale memorial hospital', 'moxie birth', 'medi-cal doula', 'birth plan', 'postpartum doula', 'birth center', 'los angeles doula'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },

    "huntington-beach-ca": {
        "title": "Huntington Beach CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)",
        "description": "Planning a birth in Huntington Beach, CA? This guide covers everything you need: 2 hospitals (Hoag Hospital Newport Beach, MemorialCare Saddleback Medical Center), South Coast Midwifery birth center in nearby Irvine, 4 local doulas with pricing details, and how California Medi-Cal covers doula services.\n\nChapters:\n0:00 Introduction\n0:13 What we cover\n0:32 Hoag Hospital Newport Beach\n0:54 MemorialCare Saddleback Medical Center\n1:16 South Coast Midwifery birth center\n1:38 Madi Rose\n2:00 Dee Ornelas\n2:18 Kelsey and Aurora\n2:37 Mathilde\n2:56 True Joy Birthing app\n3:18 Cost ranges\n3:45 Medi-Cal coverage\n4:07 Free birth plan resources\n\nFree birth plan template: https://truejoybirthing.com/birth-plan-template/\nHuntington Beach doula directory: https://truejoybirthing.com/birth-support/huntington-beach-ca/\nDownload the app: https://apps.apple.com/us/app/true-joy-birthing/id6760793180\n\n#huntingtonbeach #huntingtonbeachdoula #cadoula #medicaid #birthdoula #postpartumdoula #midwife #birthplan #medical #californiabirth #orangecounty",
        "tags": ["huntington beach doula", "huntington beach midwife", "california birth", "orange county doula", "hoag hospital newport beach", "memorialcare saddleback", "south coast midwifery", "medi-cal doula", "medicaid doula", "birth plan", "postpartum doula", "childbirth education"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "torrance-ca": {
        "title": "Torrance CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)",
        "description": "Planning a birth in Torrance, CA? This guide covers everything you need: 2 hospitals (Torrance Memorial Medical Center, Providence Little Company of Mary), South Bay Birth Center in nearby Redondo Beach, 7 local doulas with pricing details, and how California Medi-Cal covers doula services.\n\nChapters:\n0:00 Introduction\n0:12 What we cover\n0:30 Torrance Memorial Medical Center\n0:58 Providence Little Company of Mary\n1:32 South Bay Birth Center\n1:58 Doulas & midwives serving Torrance\n2:30 True Joy Birthing app\n2:56 Cost ranges\n3:24 Medi-Cal coverage\n3:53 Free birth plan resources\n\nFree birth plan template: https://truejoybirthing.com/birth-plan-template/\nTorrance doula directory: https://truejoybirthing.com/birth-support/torrance-ca/\nDownload the app: https://apps.apple.com/us/app/true-joy-birthing/id6760793180\n\n#torrancedoula #torrancebirth #cadoula #medical #birthdoula #postpartumdoula #midwife #birthplan #californiabirth #southbay #southbaydoula",
        "tags": ["torrance doula", "torrance midwife", "california birth", "south bay doula", "torrance memorial medical center", "providence little company of mary", "south bay birth center", "medi-cal doula", "medicaid doula", "birth plan", "postpartum doula", "childbirth education"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "oceanside-ca": {
        "title": "Oceanside CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)",
        "description": """Planning a birth in Oceanside, California? This guide walks you through everything: doulas and midwives serving Oceanside, hospital policies, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Oceanside doula directory → https://truejoybirthing.com/birth-support/oceanside-ca/

▸ Find Oceanside doulas & midwives
▸ Compare hospital options (Scripps Encinitas, Palomar Escondido, Sharp Mary Birch)
▸ Tour Birth Matters Inc. birth center in Oceanside
▸ Know what doula care actually costs ($1,500–$3,500)
▸ Understand California Medi-Cal doula coverage (PAVE program)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Oceanside
0:14 — What We Cover
0:36 — Scripps Memorial Hospital Encinitas
1:08 — Palomar Medical Center Escondido
1:38 — Sharp Mary Birch Hospital for Women
2:15 — Birth Matters Inc. Birth Center
2:46 — Doulas & Midwives in Oceanside
3:27 — The True Joy Birthing App
3:53 — Cost Reality ($1,500–$3,500)
4:30 — Insurance & California Medi-Cal
4:59 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#oceansidedoula #oceansidecabirth #californiamedical #birthplan #doula #pregnancyoceanside #northcountydoula #sandiegobirth #birthmatters #midwife #postpartumdoula""",
        "tags": [
            "Oceanside doula", "Oceanside birth doula", "Medi-Cal doula",
            "Oceanside pregnancy guide", "birth plan template", "first time mom",
            "Scripps Encinitas maternity", "Palomar Escondido maternity",
            "Sharp Mary Birch", "Birth Matters Oceanside",
            "doula cost", "California birth support",
            "doula near me", "Oceanside midwife", "pregnancy California",
            "free birth plan", "doula services", "birth preparation",
            "North County doula", "PAVE program",
        ],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },
    "yonkers-ny": {
        "title": "Yonkers NY Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """Planning a birth in Yonkers, NY? This guide covers everything you need: 2 hospitals (St. John's Riverside Hospital, White Plains Hospital), 4 local doulas with pricing details, and how New York Medicaid covers doula services.

Chapters:
0:00 Introduction
0:11 What we cover
0:29 St. John's Riverside Hospital
1:09 White Plains Hospital
1:43 Elise Alahakoon - ELLE Doula Services
2:04 Audelle Harvey - Audelle's Doula Services
2:25 Rebecca Tucci - Blissful Birthing Westchester NY
2:48 Hilary Baxendale - Westchester Birth and Parenting
3:10 True Joy Birthing app
3:28 Cost ranges
3:57 New York Medicaid coverage
4:29 Free birth plan resources

Free birth plan template: https://truejoybirthing.com/birth-plan-template/
Yonkers doula directory: https://truejoybirthing.com/birth-support/yonkers-ny/
Download the app: https://apps.apple.com/us/app/true-joy-birthing/id6760793180

#yonkersdoula #yonkersbirth #newyorkmedicaid #birthplan #doula #pregnancyyonkers #westchesterdoula #westchesterbirth #birthdoula #postpartumdoula #midwife #newyorkbirth""",
        "tags": ["yonkers doula", "yonkers birth doula", "new york medicaid doula", "yonkers pregnancy guide", "birth plan template", "first time mom yonkers", "westchester doula", "st johns riverside hospital", "white plains hospital", "yonkers doula cost", "new york birth support", "doula near me", "yonkers midwife", "pregnancy new york", "free birth plan", "doula services yonkers", "birth preparation", "westchester county doula", "hudson valley birth", "postpartum doula"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },

    "alexandria-va": {
        'title': "Alexandria VA Doula and Birth Plan Guide: Costs, Hospitals and Medicaid",
        'description': """Alexandria VA birth guide for expecting families. Learn about local doulas and midwives, Inova Alexandria Hospital, VHC Health, Inova Fairfax Hospital, BirthCare and Women's Health, doula costs, and Virginia Medicaid coverage.

Featured providers include Rebecca Baker of SoulSpark Birth Services, Lindsey Vick of Sunflowers Healing and Wellness, MomEase, Ryann Bernard of Del Ray Midwifery, and Balanced Birth Support.

Build your birth plan: https://truejoybirthing.com/birth-plan-template/
Alexandria birth support page: https://truejoybirthing.com/birth-support/alexandria-va/
True Joy Birthing: https://truejoybirthing.com

CHAPTERS:
0:00 Welcome to Alexandria
0:13 What this guide covers
0:31 Inova Alexandria Hospital
1:01 VHC Health
1:32 Inova Fairfax Hospital
2:07 BirthCare and Women's Health
2:30 Alexandria doulas and midwives
4:24 True Joy Birthing app
4:50 Doula costs
5:17 Virginia Medicaid coverage
5:51 Your next step

#alexandriadoula #alexandriabirth #virginiadoula #birthplan #midwife""",
        'tags': ["alexandria doula", "alexandria birth", "virginia doula", "alexandria midwife", "Inova Alexandria Hospital", "VHC Health", "BirthCare Alexandria", "birth plan", "doula cost", "Virginia Medicaid doula", "first time mom", "birth center"],
        'category_id': "27",
        'privacy_status': "public",
        'made_for_kids': False,
    },

    "washington-dc": {
        'title': "Washington DC Doula and Birth Plan Guide: Costs, Hospitals and Medicaid",
        'description': """Washington DC birth guide for expecting families. Learn about local doulas and midwives, MedStar Washington Hospital Center, Sibley Memorial Hospital, George Washington University Hospital, Community of Hope and BirthCare birth centers, doula costs, and DC Medicaid coverage.

Featured providers include Katie Baxter of Washington DC Birth, Erin Clark of Doula EAC, Vanessa Hanible of Wholesome Beginnings, Jamilah Muhayman, and Samantha Jade.

Build your birth plan: https://truejoybirthing.com/birth-plan-template/
Washington DC birth support page: https://truejoybirthing.com/birth-support/washington-dc/
True Joy Birthing: https://truejoybirthing.com

CHAPTERS:
0:00 Welcome to Washington
0:14 What this guide covers
0:35 MedStar Washington Hospital Center
0:56 Sibley Memorial Hospital
1:19 GW University Hospital
1:37 Freestanding Birth Centers
2:06 Katie Baxter
2:30 Erin Clark
3:03 Vanessa Hanible
3:34 Jamilah Muhayman
4:05 Samantha Jade
4:38 True Joy Birthing app
5:00 Doula costs
5:28 DC Medicaid coverage
6:01 Your next step

#washingtondcdoula #washingtondcbirth #dcdoula #birthplan #midwife""",
        'tags': ["washington dc doula", "washington dc birth", "DC doula", "washington midwife", "MedStar Washington Hospital Center", "Sibley Memorial Hospital", "GW University Hospital", "Community of Hope birth center", "birth plan", "doula cost", "DC Medicaid doula", "first time mom", "birth center"],
        'category_id': "27",
        'privacy_status': "public",
        'made_for_kids': False,
    },

    'acworth-ga': {
        'title': "Acworth GA Doula and Birth Plan Guide: Costs, Hospitals and Medicaid",
        'description': """Acworth GA birth guide for expecting families. Learn about local doulas and midwives, Wellstar Kennestone Hospital, Northside Hospital Cherokee, Wellstar Cobb Hospital, doula costs, and Georgia Medicaid coverage.

Featured providers include Christie Williams of Roots of Abundance, Liliana Delgado-Garcia, and North Atlanta Birth Services.

Build your birth plan: https://truejoybirthing.com/birth-plan-template/
Acworth birth support page: https://truejoybirthing.com/birth-support/acworth-ga/
True Joy Birthing: https://truejoybirthing.com

CHAPTERS:
0:00 Hospitals in Acworth
0:13 What this guide covers
0:32 Wellstar Kennestone Hospital
0:59 Northside Hospital Cherokee
1:24 Wellstar Cobb Hospital
1:50 Christie Williams
2:07 Liliana Delgado-Garcia
2:25 North Atlanta Birth Services
2:42 Free Birth Plan App
3:05 Doula costs
3:25 Medicaid and insurance
3:49 Build your birth plan

#acworthdoula #acworthbirth #georgiadoula #birthplan #midwife""",
        'tags': ["acworth doula", "acworth birth", "georgia doula", "acworth midwife", "Wellstar Kennestone Hospital", "Northside Hospital Cherokee", "Wellstar Cobb Hospital", "birth plan", "doula cost", "Georgia Medicaid doula", "first time mom", "Cobb County doula"],
        'category_id': "27",
        'privacy_status': "public",
        'made_for_kids': False,
    },

    'newport-news-va': {
        'title': 'Newport News Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Newport News — now what? This guide walks you through everything: doulas and midwives serving Newport News, hospital policies, real costs, and whether Virginia Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Newport News doula directory → https://truejoybirthing.com/birth-support/newport-news-va/

▸ Find Newport News doulas & midwives (8 providers)
▸ Compare hospital options (Bon Secours Mary Immaculate, Riverside Regional, Sentara CarePlex)
▸ Explore The Village Midwife Birth Center (freestanding birth center)
▸ Know what doula care actually costs ($800–$1,800)
▸ Understand Virginia Medicaid doula coverage ($1,078.92 per birth)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Newport News
0:13 — What This Video Covers
0:29 — Bon Secours Mary Immaculate Hospital
1:13 — Riverside Regional Medical Center
1:49 — Sentara CarePlex Hospital (Hampton)
2:18 — The Village Midwife Birth Center
2:54 — 8 Doulas & Midwives in Newport News
3:30 — The True Joy Birthing App
3:52 — Cost Reality ($800–$1,800)
4:20 — Insurance & Virginia Medicaid
4:58 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#newportnewsdoula #newportnewsbirth #virginiamedicaid #birthplan #doula #pregnancynewportnews""",
        'tags': [
            'Newport News doula', 'Newport News birth doula', 'Virginia Medicaid doula',
            'Newport News pregnancy guide', 'birth plan template', 'first time mom Newport News',
            'Newport News hospital maternity', 'Newport News doula cost',
            'doula near me', 'Newport News midwife', 'pregnancy Virginia',
            'free birth plan', 'doula services Newport News', 'birth preparation',
            'Bon Secours Mary Immaculate', 'Riverside Regional Medical Center',
            'Sentara CarePlex', 'Village Midwife Birth Center',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'costa-mesa-ca': {
        'title': 'Costa Mesa CA Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Costa Mesa — now what? This guide walks you through everything: doulas and midwives serving Costa Mesa, hospital and birth center options, real costs, and how California's Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Costa Mesa doula directory → https://truejoybirthing.com/birth-support/costa-mesa-ca/

▸ Find Costa Mesa doulas & midwives (4 providers)
▸ Compare hospital options (Hoag Hospital Newport Beach, MemorialCare Orange Coast)
▸ Explore South Coast Midwifery & Honey Midwifery birth centers
▸ Know what doula care actually costs ($1,500–$2,500)
▸ Understand California Medi-Cal doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Costa Mesa
0:13 — What This Video Covers
0:31 — Hoag Hospital Newport Beach
1:01 — MemorialCare Orange Coast Medical Center
1:25 — South Coast Midwifery Birth Center
1:46 — Honey Midwifery Birth Center
2:08 — Christine (Costa Mesa Doula)
2:30 — Tiffany Blackham
2:57 — Tessa Fisher (Abundant Blessings Midwifery)
3:18 — Kellie Gwaltney, CNM
3:42 — The True Joy Birthing App
4:09 — Cost Reality ($1,500–$2,500)
4:35 — Insurance & California Medi-Cal
5:12 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#costamesadoula #costamesabirth #californiamedicaid #birthplan #doula #pregnancycostamesa""",
        'tags': [
            'Costa Mesa doula', 'Costa Mesa birth doula', 'California Medi-Cal doula',
            'Costa Mesa pregnancy guide', 'birth plan template', 'first time mom Costa Mesa',
            'Costa Mesa hospital maternity', 'Hoag Newport Beach maternity',
            'MemorialCare Orange Coast birth', 'Costa Mesa doula cost',
            'doula near me', 'Costa Mesa midwife', 'pregnancy California',
            'free birth plan', 'doula services Costa Mesa', 'birth preparation',
            'South Coast Midwifery', 'Honey Midwifery', 'Costa Mesa birth center',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    "lakewood-co": {
        'title': "Lakewood CO Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        'description': """You just found out you're pregnant in Lakewood — now what? This guide walks you through everything: doulas and midwives serving Lakewood, hospital policies, birth center options, real costs, and how Colorado Medicaid covers doula services.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Lakewood doula directory → https://truejoybirthing.com/birth-support/lakewood-co/

▸ Find Lakewood doulas & midwives (3 providers)
▸ Compare hospital options (Intermountain Health Lutheran, AdventHealth Littleton, St. Anthony Hospital)
▸ Explore Colorado Birth and Wellness (freestanding birth center)
▸ Know what doula care actually costs ($800–$2,500)
▸ Understand Colorado Medicaid doula coverage
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Lakewood
0:13 — What This Video Covers
0:33 — Intermountain Health Lutheran Hospital
1:18 — AdventHealth Littleton — The BirthPlace
2:02 — St. Anthony Hospital
2:41 — Colorado Birth and Wellness
3:14 — Jennifer Wisse — Genesis Birth Doula
3:52 — Beth Brooks — Life On Purpose Doulas
4:27 — Sanctuary Doulas & Family Care
4:58 — The True Joy Birthing App
5:21 — Cost Reality ($800–$2,500)
5:52 — Insurance & Colorado Medicaid
6:26 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#lakewooddoula #lakewoodbirth #coloradomedicaid #birthplan #doula #pregnancylakewood""",
        'tags': [
            'Lakewood doula', 'Lakewood birth doula', 'Colorado Medicaid doula',
            'Lakewood pregnancy guide', 'birth plan template', 'first time mom Lakewood',
            'Lakewood hospital maternity', 'Lakewood doula cost',
            'doula near me', 'Lakewood midwife', 'pregnancy Colorado',
            'free birth plan', 'doula services Lakewood', 'birth preparation',
            'Intermountain Health Lutheran', 'AdventHealth Littleton', 'St. Anthony Hospital',
            'Colorado Birth and Wellness', 'Denver metro doula',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'arvada-co': {
        'title': "Arvada CO Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        'description': """You just found out you're pregnant in Arvada — now what? This guide walks you through everything: doulas and midwives serving Arvada, hospital policies, real costs, and how Colorado Medicaid covers doula services.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Arvada doula directory → https://truejoybirthing.com/birth-support/arvada-co/

▸ Find Arvada doulas & midwives (1 provider)
▸ Compare hospital options (Intermountain Health Lutheran, St. Anthony North, St. Anthony Hospital)
▸ Know what doula care actually costs ($800–$2,500)
▸ Understand Colorado Health First doula coverage ($750/birth)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Arvada
0:12 — What This Video Covers
0:29 — Intermountain Health Lutheran Medical Center
0:46 — St. Anthony North Hospital
1:02 — St. Anthony Hospital
1:15 — Doulas & Midwives in Arvada
1:26 — The True Joy Birthing App
1:47 — Cost Reality ($800–$2,500)
2:07 — Insurance & Colorado Medicaid
2:27 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#arvadadoula #arvadabirth #coloradomedicaid #birthplan #doula #pregnancyarvada""",
        'tags': [
            'Arvada doula', 'Arvada birth doula', 'Colorado Medicaid doula',
            'Arvada pregnancy guide', 'birth plan template', 'first time mom Arvada',
            'Arvada hospital maternity', 'Arvada doula cost',
            'doula near me', 'Arvada midwife', 'pregnancy Colorado',
            'free birth plan', 'doula services Arvada', 'birth preparation',
            'Intermountain Health Lutheran', 'St. Anthony North', 'St. Anthony Hospital',
            'Denver metro doula', 'Jefferson County doula',
        ],
        'category_id': '27',  # Education
        'privacy_status': 'public',
        'made_for_kids': False,
    },
"alameda-ca": {
        "title": "Alameda CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)",
        "description": "Planning a birth in Alameda, CA? This guide covers everything you need: 3 East Bay hospitals (Highland Hospital Family Birthing Center, Alta Bates Summit Medical Center, Kaiser Permanente Oakland), 4 local doulas and midwives with pricing from $1,500 to $8,000, and how California Medi-Cal covers doula services free since January 2023.\n\nChapters:\n0:00 Introduction\n0:10 What we cover\n0:31 Highland Hospital — Family Birthing Center\n1:16 Alta Bates Summit Medical Center\n1:53 Kaiser Permanente Oakland\n2:31 Lenore Musambacine — Luna Birth & Wellness\n3:00 Maureen Layag — Doula\n3:29 Evaly Long — Island Midwife\n4:00 Shelea Roosevelt — Doula\n4:22 True Joy Birthing app\n4:47 Cost ranges\n5:20 Medi-Cal coverage\n5:44 Free birth plan resources\n\nFree birth plan template: https://truejoybirthing.com/birth-plan-template/\nAlameda doula directory: https://truejoybirthing.com/birth-support/alameda-ca/\nDownload the app: https://apps.apple.com/us/app/true-joy-birthing/id6760793180\n\n#alameda #alamedadoula #cadoula #medical #birthdoula #postpartumdoula #midwife #birthplan #californiabirth #eastbaydoula",
        "tags": ["alameda doula", "alameda midwife", "california birth", "east bay doula", "oakland doula", "highland hospital", "alta bates", "kaiser oakland", "medi-cal doula", "medicaid doula", "birth plan", "postpartum doula", "home birth midwife"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },
    'fulshear-tx': {
        'title': 'Fulshear, TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Fulshear — now what? This guide walks you through everything: doulas and midwives serving Fulshear, hospital policies at Memorial Hermann Katy and Houston Methodist West, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📋 Free birth plan template → https://truejoybirthing.com/birth-plan-template/

Chapters:
0:00 Congratulations — you're pregnant in Fulshear!
0:15 Fulshear doula costs overview
0:35 Meet doulas serving Fulshear
2:35 Memorial Hermann Katy Hospital
3:20 Houston Methodist West Hospital
4:05 Katy Birth Center
4:50 Does Texas Medicaid cover doulas?
5:20 Build your birth plan free
6:40 Start your joyful birth

Doulas featured: Yvonne Estrada, Alysa Kowis, Samentha Alarcon, Karrington Searles, Delaney Vasisko

truejoybirthing.com/birth-support/fulshear-tx/""",
        'tags': [
            'fulshear tx doula', 'doula costs fulshear', 'birth plan fulshear',
            'memorial hermann katy', 'houston methodist west', 'katy birth center',
            'texas medicaid doula', 'doula houston', 'birth support fulshear',
            'first time mom fulshear', 'doula directory texas',
            'birth plan app', 'true joy birthing'
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'alvin-tx': {
        'title': 'Alvin, TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Alvin — now what? This guide walks you through everything: doulas and midwives serving Alvin, hospital policies at HCA Houston Clear Lake and HCA Houston Southeast, BioBirth Birth Center, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📋 Free birth plan template → https://truejoybirthing.com/birth-plan-template/

Chapters:
0:00 Congratulations — you're pregnant in Alvin!
0:10 What this guide covers
0:27 HCA Houston Healthcare Clear Lake
1:02 HCA Houston Healthcare Southeast
1:37 BioBirth Birth Center
2:07 Meet doulas serving Alvin
4:18 The free birth plan app
4:48 How much does a doula cost in Alvin?
5:18 Does Texas Medicaid cover doulas?
5:58 Start your joyful birth

Doulas featured: Elissa Hinson, Brianna Nichelle, Shakira Simpson, NaConda Frank

truejoybirthing.com/birth-support/alvin-tx/""",
        'tags': [
            'alvin tx doula', 'doula costs alvin', 'birth plan alvin',
            'hca clear lake', 'hca southeast', 'biobirth birth center',
            'texas medicaid doula', 'doula houston', 'birth support alvin',
            'first time mom alvin', 'doula directory texas',
            'birth plan app', 'true joy birthing'
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'american-canyon-ca': {
        'title': 'American Canyon, CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)',
        'description': """You just found out you're pregnant in American Canyon — now what? This guide walks you through everything: doulas and midwives serving American Canyon, hospital policies at Providence Queen of the Valley and Kaiser Permanente Vallejo, Napa Valley Birth Center, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📋 Free birth plan template → https://truejoybirthing.com/birth-plan-template/

Chapters:
0:00 Congratulations — you're pregnant in American Canyon!
0:13 What this guide covers
0:34 Providence Queen of the Valley Medical Center
0:58 Kaiser Permanente Vallejo Medical Center
1:20 Napa Valley Birth Center
1:47 Doulas serving American Canyon
2:07 The free birth plan app
2:30 How much does a doula cost in American Canyon?
2:55 Does Medi-Cal cover doulas?
3:21 Start your joyful birth

Doulas featured: Tiffany Murphy, Grace Magnini, Imani Lopez, Gabriela Tripp, Crystal Franco, Briahna Baskett

truejoybirthing.com/birth-support/american-canyon-ca/""",
        'tags': [
            'american canyon doula', 'doula costs american canyon', 'birth plan american canyon',
            'providence queen of the valley', 'kaiser vallejo', 'napa valley birth center',
            'california medi-cal doula', 'pave program doula', 'napa county doula',
            'solano county doula', 'vallejo doula', 'birth support american canyon',
            'first time mom american canyon', 'doula directory california',
            'birth plan app', 'true joy birthing'
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'leesburg-fl': {
        'title': 'Leesburg, FL Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Leesburg — now what? This guide walks you through everything: doulas and midwives serving Leesburg and Lake County, hospital policies at AdventHealth Waterman and UF Health Shands, real costs, and whether Florida Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📋 Free birth plan template → https://truejoybirthing.com/birth-plan-template/

Chapters:
0:00 Congratulations — you're pregnant in Leesburg!
0:12 Leesburg doula costs overview
0:29 AdventHealth Waterman Hospital
1:18 UF Health Shands Hospital
2:08 Community Birth and Wellness Center
2:46 Meet doulas serving Leesburg
5:20 Build your birth plan free
5:42 Cost reality ($800-$1,800)
6:10 Does Florida Medicaid cover doulas?
6:43 Start your joyful birth

Doulas featured: Anna Heintzelman, Ashley Jass, Rebecca Luckey

truejoybirthing.com/birth-support/leesburg-fl/""",
        'tags': [
            'leesburg fl doula', 'doula costs leesburg', 'birth plan leesburg',
            'adventhealth waterman', 'uf health shands', 'community birth wellness center',
            'florida medicaid doula', 'doula lake county', 'birth support leesburg',
            'first time mom leesburg', 'doula directory florida',
            'birth plan app', 'true joy birthing'
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'alhambra-ca': {
        'title': 'Alhambra, CA Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Alhambra — now what? This guide walks you through everything: doulas and midwives serving Alhambra, hospital policies at Garfield Medical Center, San Gabriel Valley Medical Center, and USC Arcadia Hospital, real costs, and whether California Medi-Cal covers a doula.

📱 Get the free app → https://truejoybirthing.com
📋 Free birth plan template → https://truejoybirthing.com/birth-plan-template/

Chapters:
0:00 Congratulations — you're pregnant in Alhambra!
0:13 Overview of Alhambra birth support
0:31 Garfield Medical Center
0:47 San Gabriel Valley Medical Center
1:03 USC Arcadia Hospital
1:19 Meet doulas serving Alhambra
1:29 Build your birth plan free
1:51 Cost reality ($1,200-$3,500)
2:12 Does California Medi-Cal cover doulas?
2:31 Start your joyful birth

Doulas featured: Tracy Hartley, Happy Baby Journey, Monique Salgado, Catherine Roche, Hannah Struwe

truejoybirthing.com/birth-support/alhambra-ca/""",
        'tags': [
            'alhambra ca doula', 'doula costs alhambra', 'birth plan alhambra',
            'garfield medical center', 'san gabriel valley medical center', 'usc arcadia hospital',
            'california medi-cal doula', 'doula san gabriel valley', 'birth support alhambra',
            'first time mom alhambra', 'doula directory california',
            'birth plan app', 'true joy birthing'
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'allen-park-mi': {
        'title': 'Allen Park Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Allen Park — now what? This guide walks you through everything: doulas and midwives serving Allen Park, hospital policies, real costs, and Michigan Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Allen Park doula directory → https://truejoybirthing.com/birth-support/allen-park-mi/

▸ Find Allen Park doulas & midwives
▸ Compare hospital options (Henry Ford Wyandotte, Corewell Health Taylor, DMC Hutzel)
▸ Know what doula care actually costs ($650–$2,500)
▸ Understand Michigan Medicaid doula coverage ($1,500/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Allen Park
0:13 — What This Guide Covers
0:31 — Henry Ford Wyandotte Hospital
0:53 — Corewell Health Taylor Hospital
1:13 — DMC Hutzel Women's Hospital
1:35 — Meet Allen Park Doulas & Midwives
3:32 — Build Your Birth Plan Free
3:59 — Cost Reality ($650–$2,500)
4:26 — Michigan Medicaid Covers Doulas
4:53 — Your Next Step

Doulas featured: Kayla Connors, Kara Coach, Madison Terry, Christina Henrickson, Michelle Smith

truejoybirthing.com/birth-support/allen-park-mi/""",
        'tags': [
            'allen park doula', 'allen park birth doula', 'michigan medicaid doula',
            'henry ford wyandotte hospital', 'corewell health taylor', 'dmc hutzel womens hospital',
            'doula downriver detroit', 'birth plan allen park', 'birth support allen park',
            'first time mom allen park', 'doula directory michigan',
            'birth plan app', 'true joy birthing'
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'princeton-tx': {
        'title': 'Princeton Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Princeton — now what? This guide walks you through everything: doulas and midwives serving Princeton, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Princeton doula directory → https://truejoybirthing.com/birth-support/princeton-tx/

▸ Find Princeton doulas & midwives
▸ Compare hospital options (Medical City McKinney, Baylor Scott & White McKinney)
▸ Know what doula care actually costs ($800–$2,500)
▸ See if Texas Medicaid covers your doula

Everything you need to plan your birth in Princeton, Texas — in one place.

True Joy Birthing is a free birth plan app and doula directory for first-time moms.
📱 App Store: https://apps.apple.com/us/app/true-joy-birthing/id6760793180

#PrincetonTX #Doula #BirthPlan #Pregnancy #Texas #CollinCounty #BirthSupport""",
        'tags': ['princeton tx', 'doula', 'birth plan', 'pregnancy', 'texas', 'collin county', 'birth support', 'midwife', 'medical city mckinney', 'baylor scott white', 'medicaid doula', 'birth center', 'postpartum doula', 'first time mom'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },

    'anna-tx': {
        'title': 'Anna Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Anna — now what? This guide walks you through everything: doulas and midwives serving Anna, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Anna doula directory → https://truejoybirthing.com/birth-support/anna-tx/

▸ Find Anna doulas & midwives (4 local providers)
▸ Compare hospital options (Texas Health Allen, Medical City McKinney, Baylor Scott & White McKinney)
▸ Know what doula care actually costs ($1,200–$2,200)
▸ See if Texas Medicaid covers your doula (SB 750)
▸ Allen Midwifery & Family Wellness birth center option

Everything you need to plan your birth in Anna, Texas — in one place.

True Joy Birthing is a free birth plan app and doula directory for first-time moms.
📱 App Store: https://apps.apple.com/us/app/true-joy-birthing/id6760793180

#AnnaTX #Doula #BirthPlan #Pregnancy #Texas #CollinCounty #BirthSupport""",
        'tags': ['anna tx', 'doula', 'birth plan', 'pregnancy', 'texas', 'collin county', 'birth support', 'midwife', 'medical city mckinney', 'baylor scott white', 'texas health allen', 'medicaid doula', 'birth center', 'postpartum doula', 'first time mom'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'anaheim-ca': {
        'title': 'Anaheim Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Anaheim — now what? This guide walks you through everything: doulas and midwives serving Anaheim, hospital policies, real costs, and whether California Medicaid (Medi-Cal) covers a doula.

📱 Get the free app → https://truejoybirthing.com
📖 Full Anaheim guide → https://truejoybirthing.com/birth-support/anaheim-ca/

In this video:
• 3 Anaheim hospitals (Kaiser Permanente, Anaheim Regional, OC Global Medical Center)
• South Coast Midwifery birth center
• 4 local doulas with real pricing
• How much a doula costs in Anaheim ($1,700–$3,000)
• Whether Medi-Cal covers doula care in California

Whether you're planning a hospital birth, birth center birth, or home birth in Anaheim, this guide covers your options.""",
        'tags': ['anaheim doula', 'california birth', 'doula costs', 'medicaid doula', 'birth center', 'postpartum doula', 'first time mom', 'orange county doula', 'kaiser anaheim', 'south coast midwifery'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
    },
    'arlington-heights-il': {
        'title': 'Arlington Heights Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Arlington Heights — now what? This guide walks you through everything: doulas and midwives serving Arlington Heights, hospital policies, real costs, and whether Illinois Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com

🏥 Hospitals covered:
• Endeavor Health Northwest Community Hospital (Level III NICU, Arlington Heights)
• Advocate Lutheran General Hospital (Level III NICU, Baby-Friendly, Park Ridge)

👩‍⚕️ Doulas featured:
• Karissa McCallum, CD(DONA), L.Ac. — Family Tree Holistic Health
• Tia Wente, CD(DONA), PCD(DONA), CCBE — Tree of Life Doula Services
• Rebekkah Carney, CD(DONA), PCD(DONA) — Supported Serenity
• Windy City Doulas — DONA & ProDoura Certified

💰 Cost: $900-$2,500 for a birth doula, $25-$45/hr for postpartum
📈 Illinois birth stats: 31% cesarean rate, 0.8% home birth rate
🩺 Illinois Medicaid covers doulas (Public Act 102-0004, effective Feb 2024)

⏱️ Chapters:
0:00 Congratulations
0:15 Cost Overview
0:42 Endeavor Health Northwest Community Hospital
1:52 Advocate Lutheran General Hospital
3:08 Meet the Doulas
4:30 Free Birth Plan App
5:00 Cost Breakdown
5:28 Insurance & Medicaid
5:40 Your Next Step

#doula #arlingtonheights #illinois #birthplan #doulatraining #postpartum""",
        'tags': ['doula', 'arlington heights', 'illinois', 'birth plan', 'doula cost', 'medicaid doula', 'birth support', 'postpartum doula', 'midwife', 'hospital birth', 'nicu', 'cook county', 'chicago suburb'],
        'category_id': '22',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    },
    'anchorage-ak': {
        'title': 'Anchorage Doula & Birth Plan Guide: Costs, Hospitals & Insurance (First-Time Mom)',
        'description': """You just found out you're pregnant in Anchorage — now what? This guide walks you through everything: doulas and midwives serving Anchorage, hospital policies, real costs, and how Alaska's insurance landscape works.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Anchorage doula directory → https://truejoybirthing.com/birth-support/anchorage-ak/

▸ Find Anchorage doulas & midwives (5 providers)
▸ Compare hospital options (Providence Level III NICU, Alaska Regional Level II, ANMC Level II)
▸ Explore birth center options (Anchorage Birth Center — only CABC-accredited in Alaska, Haven Midwifery)
▸ Know what doula care actually costs ($900–$2,400)
▸ Understand Alaska insurance: no Medicaid coverage, but free community doula program + TRICARE
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Anchorage
0:12 — What This Video Covers
0:29 — Providence Alaska Medical Center (Level III NICU)
0:53 — Alaska Regional Hospital (Level II NICU)
1:13 — Alaska Native Medical Center (Level II NICU)
1:34 — Anchorage Birth Center (CABC-Accredited)
1:55 — Haven Midwifery and Birth Center
2:16 — Christine Rogers — Draw Near Doula ($2,400)
2:45 — Dalecia Young — Due North Support Services ($900-$2,000)
3:15 — Aemri Marks — Independent Practice ($900-$2,000)
3:36 — Tynicha Roberts — I KAN Doula ($1,000-$2,400)
4:06 — Delissa Owen — Soldotna-Based Doula ($800-$1,500)
4:34 — The True Joy Birthing App
4:58 — Cost Reality ($900–$2,400)
5:26 — Alaska Insurance: No Medicaid, But Options Exist
5:58 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#anchoragedoula #anchoragebirth #alaskabirth #birthplan #doula #pregnancyanchorage #alaskadoula""",
        'tags': ['doula', 'anchorage', 'alaska', 'birth plan', 'doula cost', 'birth support', 'postpartum doula', 'midwife', 'hospital birth', 'nicu', 'providence alaska', 'alaska regional hospital', 'TRICARE doula', 'community doula', 'birth center', 'CABC accredited'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    },
    'cincinnati-oh': {
        'title': 'Cincinnati Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Cincinnati — now what? This guide walks you through everything: doulas and midwives serving Cincinnati, hospital policies, real costs, and how Ohio Medicaid covers doula care.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Cincinnati doula directory → https://truejoybirthing.com/birth-support/cincinnati-oh/

▸ Find Cincinnati doulas & midwives (5 providers)
▸ Compare hospital options (Christ Hospital Level III NICU, Good Samaritan Level III, UC Medical Center Level III, Mercy Anderson Level II)
▸ Explore birth center options (Cincinnati Birth Center — freestanding)
▸ Know what doula care actually costs ($800–$2,200)
▸ Understand Ohio Medicaid doula coverage (covered since Oct 2024, up to $1,200/pregnancy)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Cincinnati
0:12 — What This Video Covers
0:29 — Christ Hospital Mt. Auburn (Level III NICU)
0:47 — Good Samaritan Hospital / TriHealth (Level III NICU)
1:05 — UC Medical Center (Level III NICU)
1:23 — Mercy Health Anderson (Level II NICU)
1:41 — Cincinnati Birth Center (Freestanding)
2:01 — Gentle Seed Doulas ($1,000-$2,200)
2:23 — Cincinnati Birth and Parenting / Molly Thoms ($800-$1,100)
2:45 — Marigold Birth Collective ($800-$1,500)
3:07 — Carla Thomas / Empowered Peace Birth Services ($1,500+)
3:29 — Dr. Jodi Cunningham / BWS Doulas ($1,000-$2,000)
3:51 — The True Joy Birthing App
4:15 — Cost Reality ($800–$2,200)
4:41 — Ohio Medicaid Covers Doulas (Since Oct 2024)
5:09 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#cincinnatidoula #cincinnatibirth #ohiobirth #birthplan #doula #pregnancycincinnati #ohiodoula #ohiomedicaid""",
        'tags': ['doula', 'cincinnati', 'ohio', 'birth plan', 'doula cost', 'birth support', 'postpartum doula', 'midwife', 'hospital birth', 'nicu', 'christ hospital', 'good samaritan', 'uc medical center', 'mercy anderson', 'ohio medicaid', 'birth center', 'cincinnati birth center'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    },
    'louisville-ky': {
        'title': 'Louisville Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Louisville — now what? This guide walks you through everything: doulas and midwives serving Louisville, hospital policies, real costs, and how Kentucky Medicaid covers doula care.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Louisville doula directory → https://truejoybirthing.com/birth-support/louisville-ky/

▸ Find Louisville doulas & midwives (5 providers)
▸ Compare hospital options (Norton Hospital Level IV NICU, Norton Women's & Children's Level III, Baptist Health Louisville Level III, UofL Hospital Level III)
▸ Explore birth center options (Tree of Life Family Birth Center — freestanding)
▸ Know what doula care actually costs ($800–$2,500)
▸ Understand Kentucky Medicaid doula coverage (pilots in Humana & Anthem plans)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Louisville
0:12 — What This Video Covers
0:29 — Norton Hospital (Level IV NICU)
0:47 — Norton Women's & Children's Hospital (Level III NICU)
1:05 — Baptist Health Louisville (Level III NICU)
1:23 — UofL Hospital, Center for Women & Infants (Level III NICU)
1:41 — Tree of Life Family Birth Center (Freestanding)
2:01 — Jamie McKinney / Blissful Birth Louisville ($1,075)
2:23 — Chaney Williams / Waxing Dreamscapes ($1,400-$1,800)
2:45 — Maddie Johnson ($1,500-$2,500)
3:07 — Kathleen Thornberry ($1,200-$2,200)
3:29 — Christina Brown ($1,000)
3:51 — The True Joy Birthing App
4:15 — Cost Reality ($800–$2,500)
4:41 — Kentucky Medicaid & Insurance
5:09 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#louisvilledoula #louisvillebirth #kentuckybirth #birthplan #doula #pregnancylouisville #kentuckydoula #kentuckymedicaid""",
        'tags': ['doula', 'louisville', 'kentucky', 'birth plan', 'doula cost', 'birth support', 'postpartum doula', 'midwife', 'hospital birth', 'nicu', 'norton hospital', 'baptist health louisville', 'uofl hospital', 'kentucky medicaid', 'birth center', 'tree of life birth center'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    },
    'kansas-city-mo': {
        'title': 'Kansas City Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Kansas City — now what? This guide walks you through everything: doulas and midwives serving Kansas City, hospital policies, real costs, and how Missouri Medicaid covers doula care.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Kansas City doula directory → https://truejoybirthing.com/birth-support/kansas-city-mo/

▸ Find Kansas City doulas & midwives (9 providers)
▸ Compare hospital options (University Health The Birthplace Level III NICU, Saint Luke's Hospital Level III NICU, Children's Mercy Level IV NICU)
▸ Explore home birth practices (Natural Birth KC, Blossom Midwifery and Wellness)
▸ Know what doula care actually costs ($800–$1,800)
▸ Understand Missouri Medicaid doula coverage (covered since 2024, MO-24-0008)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Kansas City
0:15 — What This Video Covers
0:36 — University Health The Birthplace (Level IV Perinatal, Level III NICU)
0:59 — Saint Luke's Hospital (Level III NICU, Doula Partnership)
1:31 — Children's Mercy Kansas City (Level IV NICU)
1:57 — Natural Birth KC (Home Birth, Water Birth)
2:22 — Blossom Midwifery and Wellness (CNM Home Birth)
2:50 — Kansas City Doulas & Midwives (9 Providers)
3:21 — The True Joy Birthing App
3:44 — Cost Reality ($800–$1,800 Doulas, $3,500–$5,000 Midwives)
4:10 — Missouri Medicaid Covers Doulas (Since 2024)
4:38 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#kansascitydoula #kansascitybirth #missouribirth #birthplan #doula #pregnancykansascity #missouridoula #missourimedicaid""",
        'tags': ['doula', 'kansas city', 'missouri', 'birth plan', 'doula cost', 'birth support', 'postpartum doula', 'midwife', 'hospital birth', 'nicu', 'university health', 'saint lukes', 'childrens mercy', 'missouri medicaid', 'mo healthnet', 'home birth', 'natural birth kc', 'blossom midwifery'],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    },
    'melissa-tx': {
        'title': 'Melissa TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Melissa, Texas — now what? This guide walks you through everything: doulas and midwives serving Melissa, hospital policies in nearby McKinney, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Melissa doula directory → https://truejoybirthing.com/birth-support/melissa-tx/

▸ Find Melissa-area doulas & midwives
▸ Compare hospital options (Baylor Scott & White McKinney, Medical City McKinney)
▸ Explore Bella Births birth center in McKinney
▸ Know what doula care actually costs ($1,000–$2,000)
▸ Understand Texas Medicaid doula coverage (not yet statewide)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Melissa
0:16 — What This Guide Covers
0:37 — Baylor Scott and White McKinney
1:17 — Medical City McKinney
1:53 — Bella Births Birth Center
2:27 — Sydney Osborne — Chubby Cheeks Doula
2:59 — Kourtney McGowan — Doula Things Your Way
3:31 — Kate Tverytnykova
4:04 — The True Joy Birthing App
4:26 — Doula Costs ($1,000–$2,000)
4:53 — Texas Medicaid & Insurance
5:28 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#melissatxdoula #melissatxbirth #texasmedicaid #birthplan #doula #pregnancymelissa #texasdoula #collincounty #mckinneydoula""",
        'tags': [
            'Melissa doula', 'Melissa TX birth doula', 'Texas Medicaid doula',
            'Melissa pregnancy guide', 'birth plan template', 'first time mom Melissa',
            'McKinney hospital maternity', 'doula cost Melissa TX', 'Collin County birth support',
            'doula near me', 'McKinney doula', 'pregnancy Texas',
            'free birth plan', 'doula services Melissa', 'birth preparation',
            'Baylor Scott White McKinney', 'Medical City McKinney', 'Bella Births',
            'birth center McKinney', 'postpartum doula'
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    },

    'fate-tx': {
        'title': 'Fate, TX Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Fate, Texas. Now what? This guide walks you through everything: doulas and midwives serving Fate, hospital policies, real costs, and how Texas Medicaid covers doula care.

Mobile app: https://truejoybirthing.com
Free birth plan: https://truejoybirthing.com/birth-plan-template/
Fate doula directory: https://truejoybirthing.com/birth-support/fate-tx/

Find Fate-area doulas, midwives and lactation consultants (4 providers)
Compare hospital options (Texas Health Rockwall Level I NICU, Hunt Regional Greenville Level III NICU)
Explore birth centers (Sweet Pea Midwifery, Heavenly Hands Birthing Center)
Know what doula care actually costs ($1,200 to $2,500)
Understand Texas Medicaid doula coverage (SB 750, covered since Sept 2024)
Build your free birth plan step by step

CHAPTERS:
0:00 Welcome to Fate
0:12 What This Video Covers
0:28 Texas Health Rockwall (Level I NICU, Texas Ten Step)
0:51 Hunt Regional Medical Center Greenville (Level III NICU)
1:17 Sweet Pea Midwifery (CNM Birth Center, Water Birth, VBAC)
1:37 Heavenly Hands Birthing Center (Midwife-Led, Home Birth)
1:56 Suzie Sulak, Little Lilacs (BEST Certified Doula, Bilingual)
2:22 Olivia Delavega, Sweet Pea Midwifery (CNM)
2:47 Lyndee, The Bump Midwifery (LM, Twin and Breech)
3:03 Dana Fe Gonzales, Rockwall Lactation (IBCLC)
3:26 The True Joy Birthing App
3:47 What Doulas Cost in Fate
4:06 Texas Medicaid Covers Doula Care (SB 750)
4:23 Build Your Birth Plan""",
        'tags': ['fate tx doula', 'fate texas birth', 'rockwall doula', 'rockwall county doula', 'texas doula costs', 'fate birth plan', 'texas medicaid doula', 'sb 750 doula', 'true joy birthing', 'doula directory', 'birth center rockwall', 'lactation consultant rockwall'],
        'category_id': '22',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    },
    "palm-springs-fl": {
        "title": "Palm Springs FL Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        "description": """Planning a birth in Palm Springs, Florida? This complete guide walks you through everything you need to know.

Doulas in Palm Springs cost $800-$2,500. Midwifery care runs $3,500-$8,000. Florida Medicaid covers doula services under SB 264 (effective July 2024).

Hospitals covered:
- Bethesda Hospital East (Boynton Beach) - Level III NICU
- St. Mary's Medical Center (West Palm Beach) - Level III NICU
- Jupiter Medical Center (Jupiter) - Level II NICU

Birth centers:
- Palms Birth House (Boynton Beach)
- Gentle Birth Center & OBGYN (Royal Palm Beach)

Providers featured:
- Fadwah Halaby, APRN, CNM (MIDWIFE360)
- Dana Jacobs, CNM, MSN (Women's Care)
- Coastal Doulas of Palm Beach
- Elizabeth Charron, LM, CPM (Palms Birth House)
- Bonnie Kelly (Birth & Postpartum Doula, CLE)

Build your free birth plan at https://truejoybirthing.com/birth-plan-template/
Find doulas and midwives at https://truejoybirthing.com/birth-support/palm-springs-fl/

Chapters:
00:00 Intro
00:12 What This Video Covers
00:33 Bethesda Hospital East
01:09 St. Mary's Medical Center
01:38 Jupiter Medical Center
02:07 Palms Birth House
02:38 Gentle Birth Center & OBGYN
03:05 Fadwah Halaby (MIDWIFE360)
03:35 Dana Jacobs (Women's Care)
04:03 Coastal Doulas of Palm Beach
04:35 Elizabeth Charron (Palms Birth House)
05:06 Bonnie Kelly (Doula, CLE)
05:34 Free Birth Plan App
05:59 Cost Ranges
06:28 Florida Medicaid & Insurance
07:00 Get Started

#palmspringsdoula #palmspringsfl #floridabirth #doula #midwife #birthplan""",
        "tags": ["palm springs doula", "palm springs fl doula", "palm beach county doula", "florida midwife", "bethesda hospital east", "st marys medical center", "jupiter medical center", "palms birth house", "midwife360", "florida medicaid doula", "birth plan", "birth center florida"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
        "embeddable": True
    },
    'corpus-christi-tx': {
        'title': 'Corpus Christi Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Corpus Christi — now what? This guide walks you through everything: doulas and midwives serving the Coastal Bend, hospital policies, the city's only freestanding birth center, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Corpus Christi doula directory → https://truejoybirthing.com/birth-support/corpus-christi-tx/

▸ Find Corpus Christi doulas & midwives (4 providers)
▸ Compare hospital options (Corpus Christi Medical Center, Driscoll Children's Hospital)
▸ Explore the Corpus Christi Birth Center
▸ Know what doula care actually costs ($750–$1,800)
▸ Understand Texas Medicaid doula coverage (SB 750)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Corpus Christi
0:13 — Where Coastal Bend Families Deliver (Hospitals)
0:34 — Corpus Christi Medical Center (Level III NICU)
1:05 — Driscoll Children's Hospital (Level III NICU)
1:36 — Corpus Christi Birth Center
2:06 — Doulas & Midwives in Corpus Christi
2:33 — The True Joy Birthing App
2:58 — Cost Reality ($750–$1,800)
3:24 — Insurance & Texas Medicaid
3:52 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#corpuschristidoula #corpuschristibirth #texasmedicaid #birthplan #doula #pregnancycorpuschristi""",
        'tags': [
            'Corpus Christi doula', 'Corpus Christi birth doula', 'Texas Medicaid doula',
            'Corpus Christi pregnancy guide', 'birth plan template', 'first time mom Corpus Christi',
            'Corpus Christi hospital maternity', 'Corpus Christi doula cost',
            'Corpus Christi midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Corpus Christi',
            'Corpus Christi Medical Center', "Driscoll Children's Hospital",
            'Corpus Christi Birth Center', 'Coastal Bend birth',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    },
    'lubbock-tx': {
        'title': 'Lubbock Birth Guide: Hospitals, Doulas & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Lubbock — now what? This guide walks you through everything: the two hospitals where doulas and midwives are welcome, six experienced doulas and midwives across the South Plains, real costs, and whether Texas Medicaid covers a doula under SB 750.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Lubbock doula directory → https://truejoybirthing.com/birth-support/lubbock-tx/

▸ Find Lubbock doulas & midwives (6 providers)
▸ Compare hospital options (Covenant Medical Center, University Medical Center)
▸ Know what doula care actually costs ($500–$1,600)
▸ Understand Texas Medicaid doula coverage (SB 750)
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Lubbock
0:11 — Where South Plains Families Deliver (Hospitals)
0:32 — Covenant Medical Center (Level III NICU)
1:04 — University Medical Center (Doula Program)
1:41 — Doulas & Midwives in Lubbock
2:20 — The True Joy Birthing App
2:43 — Cost Reality ($500–$1,600)
3:05 — Insurance & Texas Medicaid
3:35 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#lubbockdoula #lubbockbirth #texasmedicaid #birthplan #doulalubbock #SB750doula""",
        'tags': [
            'Lubbock doula', 'Lubbock birth doula', 'Texas Medicaid doula',
            'Lubbock pregnancy guide', 'birth plan template', 'first time mom Lubbock',
            'Lubbock hospital maternity', 'Lubbock doula cost',
            'Lubbock midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Lubbock',
            'Covenant Medical Center Lubbock', 'University Medical Center Lubbock',
            'SB 750 doula', 'South Plains birth',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    },
    'laredo-tx': {
        'title': 'Laredo Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Laredo — now what? This guide walks you through everything: doulas and midwives serving Laredo, hospital policies, real costs, and whether Texas Medicaid covers a doula.

📱 Get the free app → https://truejoybirthing.com
📝 Free birth plan → https://truejoybirthing.com/birth-plan-template/
📍 Laredo doula directory → https://truejoybirthing.com/birth-support/laredo-tx/

▸ Find Laredo doulas & midwives (3 providers)
▸ Compare hospital options (Laredo Medical Center, Doctors Hospital of Laredo)
▸ Know what doula care actually costs ($700–$1,600)
▸ Understand Texas Medicaid doula coverage under SB 750
▸ Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Laredo
0:12 — What This Guide Covers
0:30 — Laredo Medical Center (Level III NICU)
1:00 — Doctors Hospital of Laredo (Level II NICU)
1:30 — Doulas & Midwives in Laredo
2:50 — The True Joy Birthing App
3:12 — Cost Reality ($700–$1,600)
3:34 — Insurance & Texas Medicaid (SB 750)
4:02 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#laredodoula #laredobirth #texasmedicaid #birthplan #doula #pregnancylaredo #SB750doula #rgvbirth #bordercitybirth""",
        'tags': [
            'Laredo doula', 'Laredo birth doula', 'Texas Medicaid doula',
            'Laredo pregnancy guide', 'birth plan template', 'first time mom Laredo',
            'Laredo hospital maternity', 'Laredo doula cost', 'Texas birth support',
            'doula near me', 'Laredo midwife', 'pregnancy Texas',
            'free birth plan', 'doula services Laredo', 'birth preparation',
            'Laredo Medical Center', 'Doctors Hospital of Laredo',
            'SB 750 doula', 'Rio Grande Valley birth', 'border city doula',
            'bilingual doula', 'Webb County doula',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    }
,
    'rosemount-mn': {
        'title': 'Rosemount MN Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': "You just found out you're pregnant in Rosemount - now what? This guide walks you through everything: doulas and midwives serving Rosemount, hospital policies, real costs, and how Minnesota Medicaid covers doula services.\n\nGet the free app - https://truejoybirthing.com\nFree birth plan - https://truejoybirthing.com/birth-plan-template/\nRosemount doula directory - https://truejoybirthing.com/birth-support/rosemount-mn/\n\nFind Rosemount doulas and midwives (3 providers: Everyday Miracles, Blooma, Nicole Bengtson)\nCompare hospital options (Fairview Ridges Hospital, Regions Hospital)\nKnow what doula care actually costs ($1,200 to $3,200)\nUnderstand Minnesota Medicaid doula coverage ($1,700 per pregnancy)\nBuild your free birth plan step by step\n\nTrue Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared - all for free.\n\nCreated by Shelbi Kohler, certified birth doula.\n\n#rosemountmndoula #minnesotadoula #minnesotamedicaid #birthplan #doula #pregnancyrosemount",
        'tags': [
            'Rosemount doula', 'Minnesota birth doula', 'Minnesota Medicaid doula',
            'Rosemount pregnancy guide', 'birth plan template', 'first time mom Rosemount',
            'Rosemount hospital maternity', 'doula cost Minnesota', 'Minnesota birth support',
            'doula near me', 'Rosemount midwife', 'pregnancy Minnesota',
            'free birth plan', 'doula services Rosemount', 'birth preparation',
            'Fairview Ridges Hospital', 'Regions Hospital St Paul',
            'Minnesota Birth Center', 'Twin Cities doula', 'Dakota County doula',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True
    },

    "lexington-ky": {
        "title": "Lexington KY Doula and Birth Plan Guide: Costs, Hospitals and Medicaid (First-Time Mom)",
        "description": (
            "Planning a birth in Lexington, Kentucky? This quick guide covers the three hospitals where doulas are welcome "
            "(UK Chandler Hospital with its Level IV NICU, Baptist Health Lexington, and Saint Joseph East Women's Hospital), "
            "the LexHealth Birth Center, 8 experienced doulas serving the Bluegrass, real doula costs ($800-$2,000), "
            "how Kentucky Medicaid handles doula care right now, and a free app that builds your birth plan step by step.\n\n"
            "Chapters:\n00:00 Welcome to Lexington\n00:13 What we cover\n00:31 UK Chandler Hospital\n00:59 Baptist Health Lexington\n"
            "01:26 Saint Joseph East\n01:52 LexHealth Birth Center\n02:16 Doulas in Lexington\n02:50 The birth plan app\n"
            "03:19 What doulas cost\n03:45 Medicaid and insurance\n04:22 Build your birth plan\n\n"
            "Free birth plan template and app: https://truejoybirthing.com\n"
            "Full Lexington guide: https://truejoybirthing.com/birth-support/lexington-ky/\n\n"
            "#lexingtonkydoula #kentuckydoula #birthplan #firsttimemom #doula #pregnancytips"
        ),
        "tags": ["lexington doula", "lexington kentucky doula", "kentucky birth", "uk chandler hospital birth",
                 "baptist health lexington maternity", "saint joseph east womens hospital", "lexhealth birth center",
                 "kentucky medicaid doula", "birth plan template", "first time mom", "doula cost"],
        "category_id": "27",
        "privacy_status": "public",
        "made_for_kids": False,
    },


    'ontario-ca': {
        'title': 'Ontario CA Doula & Birth Plan Guide: Costs, Hospitals & Medi-Cal (First-Time Mom)',
        'description': """You just found out you're pregnant in Ontario — now what? This guide walks you through everything: doulas and midwives serving Ontario, hospital policies, real costs, and whether California Medi-Cal covers a doula.

Get the free app: https://truejoybirthing.com
Free birth plan: https://truejoybirthing.com/birth-plan-template/
Ontario doula directory: https://truejoybirthing.com/birth-support/ontario-ca/

Find Ontario doulas & midwives (Pamela Uriarte, Kristin, Laurie Dietrich)
Compare hospital options (San Antonio Regional Hospital Level III NICU, Kaiser Permanente Ontario Medical Center Level II NICU, Pomona Valley Hospital Medical Center)
Know what doula care actually costs ($1,200-$2,500)
Understand California Medi-Cal doula coverage
Build your free birth plan step by step

CHAPTERS:
0:00 — Welcome to Ontario
0:11 — What This Guide Covers
0:27 — San Antonio Regional Hospital (Level III NICU)
0:44 — Kaiser Permanente Ontario Medical Center (Level II NICU)
1:00 — Pomona Valley Hospital Medical Center
1:17 — Doulas & Midwives in Ontario
1:28 — The True Joy Birthing App
1:52 — Doula Costs ($1,200-$2,500)
2:15 — Insurance & California Medi-Cal
2:36 — Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared — all for free.

Created by Shelbi Kohler, certified birth doula.

#ontariodoula #ontarioca #californiamedicaid #inlandempiredoula #birthplan #doula #pregnancyontario""",
        'tags': [
            'Ontario CA doula', 'Ontario birth doula', 'Inland Empire doula',
            'California Medi-Cal doula', 'Ontario pregnancy guide', 'birth plan template',
            'Ontario hospital maternity', 'Ontario doula cost', 'San Antonio Regional Hospital',
            'Kaiser Ontario', 'Pomona Valley Hospital', 'first time mom Ontario',
            'doula near me', 'pregnancy California', 'free birth plan',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
    },
    'concord-nc': {
        'title': 'Concord NC Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)',
        'description': """You just found out you're pregnant in Concord, NC â now what? This guide walks you through everything: doulas and midwives serving Concord, hospital policies, real costs, and whether North Carolina Medicaid covers a doula.

Get the free app: https://truejoybirthing.com
Free birth plan: https://truejoybirthing.com/birth-plan-template/
Concord doula directory: https://truejoybirthing.com/birth-support/concord-nc/

Find Concord doulas and midwives (3 providers: Heart of Grace Birth Services, Tiffany St. Louis, What The Bump)
Compare hospital options (Atrium Health Cabarrus, Level IV NICU)
Know what doula care actually costs ($800-$2,500)
Understand North Carolina Medicaid doula coverage
Build your free birth plan step by step

CHAPTERS:
0:00 â Welcome to Concord
0:11 â What This Guide Covers
0:30 â Atrium Health Cabarrus (Level IV NICU)
0:55 â Doulas & Midwives in Concord
1:20 â The True Joy Birthing App
1:45 â Doula Costs ($800-$2,500)
2:05 â Insurance & NC Medicaid
2:25 â Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared â all for free.

Created by Shelbi Kohler, certified birth doula.

#concordnc #concordnc #northcarolinamedicaid #birthplan #doula #pregnancyconcord""",
        'tags': [
            'Concord NC doula', 'Concord birth doula', 'North Carolina Medicaid doula',
            'Concord pregnancy guide', 'birth plan template', 'first time mom Concord',
            'Concord hospital maternity', 'Concord NC doula cost', 'North Carolina birth support',
            'doula near me', 'Concord midwife', 'pregnancy North Carolina',
            'free birth plan', 'doula services Concord', 'birth preparation',
            'Atrium Health Cabarrus',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
    },

    'la-habra-ca': {
        'title': "La Habra, California Doula and Birth Plan Guide: Costs, Hospitals and Medicaid (First-Time Mom)",
        'description': """You just found out you're pregnant in La Habra, California, now what? This guide walks you through everything: doulas and midwives serving La Habra and north Orange County, hospital policies, real costs, and how California's Medi-Cal covers doula services.

Get the free app, https://truejoybirthing.com
Free birth plan, https://truejoybirthing.com/birth-plan-template/
La Habra doula directory, https://truejoybirthing.com/birth-support/la-habra-ca/

Find La Habra doulas and midwives (3 providers: Aloha Lamaze and Breastfeeding Services, Temple and Terrain Doula Services, Newborn Nurtury Doula Services)
Compare hospital options (Providence St. Jude Medical Center, PIH Health Whittier Hospital, Anaheim Regional Medical Center)
Know what doula care actually costs ($800 to $2,500)
Understand California Medi-Cal doula coverage (covered since January 2023)
Build your free birth plan step by step

CHAPTERS:
0:00, Welcome to La Habra
0:15, What This Guide Covers
0:35, Providence St. Jude Medical Center (Level III NICU)
0:46, PIH Health Whittier Hospital (Level III NICU)
0:58, Anaheim Regional Medical Center (Level III NICU)
1:10, Doulas and Midwives in La Habra
1:29, The True Joy Birthing App
1:53, Cost Reality ($800-$2,500)
2:16, Insurance and California Medi-Cal
2:34, Your Next Step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared, all for free.

Created by Shelbi Kohler, certified birth doula.

#lahabradoula #lahabrabirth #californiamedicaid #birthplan #doula #pregnancylahabra""",
        'tags': [
            'La Habra doula', 'California birth doula', 'California Medi-Cal doula',
            'La Habra pregnancy guide', 'birth plan template', 'first time mom La Habra',
            'La Habra hospital maternity', 'La Habra doula cost', 'California birth support',
            'doula near me', 'La Habra midwife', 'pregnancy California',
            'free birth plan', 'doula services La Habra', 'birth preparation',
            'Providence St Jude Medical Center', 'PIH Health Whittier', 'Anaheim Regional Medical Center',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
    },


# ═══════════════════════════════════════════════════════════════
    'redwood-city-ca': {
        'title': "Redwood City, California Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        'description': """You just found out you're pregnant in Redwood City - now what? This guide walks you through everything: doulas and midwives serving Redwood City, hospital policies, real costs, and how California Medicaid covers doula services.

Get the free app - https://truejoybirthing.com
Free birth plan - https://truejoybirthing.com/birth-plan-template/
Redwood City doula directory - https://truejoybirthing.com/birth-support/redwood-city-ca/

Find Redwood City doulas and midwives (3 providers: Together Birth & Body, Mairi Doula, Redwood Doulas)
Compare hospital options (Sequoia Hospital, Kaiser Permanente Redwood City Medical Center)
Know what doula care actually costs ($800 to $2500)
Understand California Medicaid doula coverage
Build your free birth plan step by step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared - all for free.

Created by Shelbi Kohler, certified birth doula.

#redwoodcitycadoula #cadoula #camedicaid #birthplan #doula #pregnancyredwoodcity""",
        'tags': [
            'Redwood City doula',
            'California birth doula',
            'California Medicaid doula',
            'Redwood City pregnancy guide',
            'birth plan template',
            'first time mom Redwood City',
            'Redwood City hospital maternity',
            'doula cost California',
            'California birth support',
            'doula near me',
            'Redwood City midwife',
            'pregnancy California',
            'free birth plan',
            'doula services Redwood City',
            'birth preparation',
            'Sequoia Hospital',
            'Kaiser Permanente Redwood City Medical Center',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
    },

    'palo-alto-ca': {
        'title': "Palo Alto, California Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        'description': """You just found out you're pregnant in Palo Alto - now what? This guide walks you through everything: doulas and midwives serving Palo Alto, hospital policies, real costs, and how California Medicaid covers doula services.

Get the free app - https://truejoybirthing.com
Free birth plan - https://truejoybirthing.com/birth-plan-template/
Palo Alto doula directory - https://truejoybirthing.com/birth-support/palo-alto-ca/

Find Palo Alto doulas and midwives (3 providers: Blossom Birth and Family, Doula by Mari, Nubia Jones)
Compare hospital options (Lucile Packard Children's Hospital Stanford, El Camino Hospital)
Know what doula care actually costs ($800 to $2500)
Understand California Medicaid doula coverage
Build your free birth plan step by step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared - all for free.

Created by Shelbi Kohler, certified birth doula.

#paloaltocadoula #cadoula #camedicaid #birthplan #doula #pregnancypaloalto""",
        'tags': [
            'Palo Alto doula',
            'California birth doula',
            'California Medicaid doula',
            'Palo Alto pregnancy guide',
            'birth plan template',
            'first time mom Palo Alto',
            'Palo Alto hospital maternity',
            'doula cost California',
            'California birth support',
            'doula near me',
            'Palo Alto midwife',
            'pregnancy California',
            'free birth plan',
            'doula services Palo Alto',
            'birth preparation',
            "Lucile Packard Children's Hospital Stanford",
            'El Camino Hospital',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
    },

    'san-mateo-ca': {
        'title': "San Mateo, California Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)",
        'description': """You just found out you're pregnant in San Mateo - now what? This guide walks you through everything: doulas and midwives serving San Mateo, hospital policies, real costs, and how California Medicaid covers doula services.

Get the free app - https://truejoybirthing.com
Free birth plan - https://truejoybirthing.com/birth-plan-template/
San Mateo doula directory - https://truejoybirthing.com/birth-support/san-mateo-ca/

Find San Mateo doulas and midwives (3 providers: San Mateo Doula, Thais Mendonca Schweitzer, Sweetbay Doula)
Compare hospital options (San Mateo Medical Center, Sequoia Hospital)
Know what doula care actually costs ($800 to $2500)
Understand California Medicaid doula coverage
Build your free birth plan step by step

True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared - all for free.

Created by Shelbi Kohler, certified birth doula.

#sanmateocadoula #cadoula #camedicaid #birthplan #doula #pregnancysanmateo""",
        'tags': [
            'San Mateo doula',
            'California birth doula',
            'California Medicaid doula',
            'San Mateo pregnancy guide',
            'birth plan template',
            'first time mom San Mateo',
            'San Mateo hospital maternity',
            'doula cost California',
            'California birth support',
            'doula near me',
            'San Mateo midwife',
            'pregnancy California',
            'free birth plan',
            'doula services San Mateo',
            'birth preparation',
            'San Mateo Medical Center',
            'Sequoia Hospital',
        ],
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
    },

}
# Auto-generate CITY_META from cities.ts when slug not in dict above
# ═══════════════════════════════════════════════════════════════

CITIES_TS_PATH = os.path.expanduser(
    '~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/projects/truejoybirthing-website/src/data/cities.ts'
)
VIDEO_EMBEDS_PATH = os.path.expanduser(
    '~/.openclaw/workspace/Kit/life/brands/TrueJoyBirthing/projects/truejoybirthing-website/src/data/video-embeds.ts'
)

STATE_NAMES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'DC': 'Washington DC',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois',
    'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana',
    'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan',
    'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana',
    'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota',
    'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
    'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota',
    'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
}


def _parse_city_field(block, field, default=''):
    """Extract a string field from a cities.ts block (handles strings and numbers)."""
    # Try string value first: field: "value"
    m = re.search(rf'{field}:\s*"([^"]*)"', block)
    if m:
        return m.group(1)
    # Try number value: field: 1234
    m = re.search(rf'{field}:\s*(\d+)', block)
    if m:
        return m.group(1)
    return default


def _parse_city_array(block, field):
    """Extract an array of names from a cities.ts block (depth-aware)."""
    if f'{field}:' not in block:
        return []
    start = block.index(f'{field}:')
    br_start = block.index('[', start)
    depth = 0
    i = br_start
    while i < len(block):
        if block[i] == '[':
            depth += 1
        elif block[i] == ']':
            depth -= 1
            if depth == 0:
                break
        i += 1
    section = block[br_start:i+1]
    return re.findall(r'name:\s*"([^"]*)"', section)


def generate_city_meta(slug):
    """Auto-generate YouTube metadata from cities.ts data. Fallback when slug not in CITY_META."""
    import re as _re

    if not os.path.exists(CITIES_TS_PATH):
        return None

    with open(CITIES_TS_PATH) as f:
        content = f.read()

    # Find city block (depth-aware)
    marker = f'"{slug}": {{'
    start = content.find(marker)
    if start == -1:
        return None
    i = content.index('{', start) + 1
    depth = 1
    while i < len(content) and depth > 0:
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
        i += 1
    block = content[start:i]

    city = _parse_city_field(block, 'city', slug.replace('-', ' ').title())
    state_code = slug.rsplit('-', 1)[-1].upper()
    state_name = STATE_NAMES.get(state_code, state_code)
    cost_low = _parse_city_field(block, 'costLow', '0')
    cost_high = _parse_city_field(block, 'costHigh', '0')

    # Providers
    provider_names = _parse_city_array(block, 'localDoulas')
    provider_list = ', '.join(provider_names) if provider_names else 'local doulas'
    provider_count = len(provider_names)

    # Hospitals
    hospital_names = _parse_city_array(block, 'hospitalDetails')
    hospital_list = ', '.join(hospital_names) if hospital_names else 'local hospitals'

    # Medicaid
    medicaid_note = _parse_city_field(block, 'medicaidNote', '')
    has_medicaid = medicaid_note.lower().startswith('yes')

    # Build title
    title = f"{city}, {state_name} Doula & Birth Plan Guide: Costs, Hospitals & Medicaid (First-Time Mom)"

    # Build description
    desc_lines = [
        f"You just found out you're pregnant in {city} - now what? This guide walks you through everything: doulas and midwives serving {city}, hospital policies, real costs, and how {state_name} Medicaid covers doula services.",
        "",
        f"Get the free app - https://truejoybirthing.com",
        f"Free birth plan - https://truejoybirthing.com/birth-plan-template/",
        f"{city} doula directory - https://truejoybirthing.com/birth-support/{slug}/",
        "",
        f"Find {city} doulas and midwives ({provider_count} providers: {provider_list})",
        f"Compare hospital options ({hospital_list})",
        f"Know what doula care actually costs (${cost_low} to ${cost_high})",
    ]
    if has_medicaid:
        desc_lines.append(f"Understand {state_name} Medicaid doula coverage")
    desc_lines.extend([
        "Build your free birth plan step by step",
        "",
        "True Joy Birthing helps first-time moms build their birth plans, find local support, and walk into the hospital prepared - all for free.",
        "",
        "Created by Shelbi Kohler, certified birth doula.",
        "",
        f"#{slug.replace('-', '')}doula #{state_code.lower()}doula #{state_code.lower()}medicaid #birthplan #doula #pregnancy{city.lower().replace(' ', '')}",
    ])
    description = "\n".join(desc_lines)

    # Build tags
    tags = [
        f'{city} doula', f'{state_name} birth doula',
        f'{state_name} Medicaid doula', f'{city} pregnancy guide',
        'birth plan template', f'first time mom {city}',
        f'{city} hospital maternity', f'doula cost {state_name}',
        f'{state_name} birth support', 'doula near me',
        f'{city} midwife', f'pregnancy {state_name}',
        'free birth plan', f'doula services {city}', 'birth preparation',
    ]
    # Add hospital names as tags
    for h in hospital_names[:3]:
        tags.append(h[:50])

    return {
        'title': title[:100],  # YouTube title limit
        'description': description[:5000],  # YouTube description limit
        'tags': tags,
        'category_id': '27',
        'privacy_status': 'public',
        'made_for_kids': False,
        'embeddable': True,
    }


def get_city_meta(slug):
    """Get city metadata from CITY_META dict, or auto-generate from cities.ts."""
    meta = CITY_META.get(slug)
    if meta:
        return meta
    auto_meta = generate_city_meta(slug)
    if auto_meta:
        print(f"  📝 Auto-generated CITY_META for {slug} from cities.ts")
        return auto_meta
    return None


def append_video_embed(slug, video_id, title, duration_seconds, chapters=None):
    """Append a new entry to video-embeds.ts after YouTube upload."""
    if not os.path.exists(VIDEO_EMBEDS_PATH):
        print(f"  ⚠️  video-embeds.ts not found at {VIDEO_EMBEDS_PATH}")
        return False

    with open(VIDEO_EMBEDS_PATH) as f:
        content = f.read()

    # Check if slug already exists
    if f'"{slug}"' in content:
        print(f"  ⏭️  {slug} already in video-embeds.ts — skipping append")
        return True

    # Build the embed entry
    duration_str = f"{int(duration_seconds // 60)}:{int(duration_seconds % 60):02d}"
    desc_short = f"Watch the full {title.split(':')[0]} — all in about {duration_str}."

    chapters_str = ""
    if chapters:
        chapters_lines = []
        for ts, label in chapters:
            chapters_lines.append(f"        [{ts}, \"{label}\"],")
        chapters_str = "\n    chapters: [\n" + "\n".join(chapters_lines) + "\n    ],\n"

    entry = f'''
  "{slug}": {{
    videoId: "{video_id}",
    title: "{title.split(':')[0]}",
    description: "{desc_short}",
    duration: {int(duration_seconds)},
{chapters_str}  }},
'''

    # Insert before the closing brace of the main object
    # Find the last closing brace
    last_brace = content.rfind('}')
    if last_brace > 0:
        # Find the end of the last entry (look for the comma/brace before the final })
        insert_point = last_brace
        # Check if there's a trailing comma before the }
        before = content[:insert_point].rstrip()
        if before.endswith(','):
            content = before + '\n' + entry + '\n' + content[insert_point:]
        else:
            content = before + ',\n' + entry + '\n' + content[insert_point:]

        with open(VIDEO_EMBEDS_PATH, 'w') as f:
            f.write(content)
        print(f"  ✅ Appended {slug} to video-embeds.ts (videoId: {video_id})")
        return True
    else:
        print(f"  ⚠️  Could not find insertion point in video-embeds.ts")
        return False


def get_access_token():
    """Get a fresh access token using the saved refresh token.
    
    Always refreshes — access tokens expire after 1 hour. The refresh token
    is long-lived (does not expire unless revoked). Saves the new access token
    and expiry back to token.json so other tools can reuse it.
    """
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

    new_access_token = resp.json()['access_token']
    expires_in = resp.json().get('expires_in', 3600)

    # Save refreshed token back to file for reuse by other tools
    token_data['token'] = new_access_token
    token_data['access_token'] = new_access_token
    token_data['expiry'] = str(int(time.time()) + expires_in)
    try:
        with open(TOKEN_PATH, 'w') as f:
            json.dump(token_data, f, indent=2)
    except Exception:
        pass  # Non-fatal — the token works for this session regardless

    return new_access_token


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

    meta = get_city_meta(slug)
    if not meta:
        print(f"ERROR: No metadata configured for slug '{slug}' and auto-generation failed.")
        print(f"Ensure {slug} exists in cities.ts.")
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
            'embeddable': meta.get('embeddable', True),
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

    # Step 2: Upload the video file using chunked resumable upload
    # Sends in CHUNK_SIZE byte chunks with resume capability — prevents
    # timeout on large files over slow connections.
    file_size = os.path.getsize(video_path)
    CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks

    uploaded = 0
    attempt = 0
    max_attempts = 5

    while uploaded < file_size:
        chunk_end = min(uploaded + CHUNK_SIZE - 1, file_size - 1)
        chunk_len = chunk_end - uploaded + 1
        attempt += 1

        with open(video_path, 'rb') as f:
            f.seek(uploaded)
            chunk = f.read(chunk_len)

        try:
            upload_resp = requests.put(
                session_uri,
                data=chunk,
                headers={
                    'Content-Length': str(chunk_len),
                    'Content-Range': f'bytes {uploaded}-{chunk_end}/{file_size}',
                },
                timeout=120,
            )
        except requests.exceptions.RequestException as e:
            if attempt < max_attempts:
                print(f"  ⚠️  Chunk upload failed (attempt {attempt}), retrying... ({e})")
                # Query the server for current upload position
                try:
                    probe = requests.put(
                        session_uri,
                        headers={'Content-Range': f'bytes */{file_size}'},
                        timeout=30,
                    )
                    if probe.status_code == 308:
                        uploaded = int(probe.headers.get('Range', f'bytes=0-{uploaded - 1}').split('-')[1]) + 1
                        attempt = 0
                        continue
                    elif probe.status_code in (200, 201):
                        uploaded = file_size
                        upload_resp = probe
                        break
                except Exception:
                    pass
                continue
            else:
                print(f"ERROR: Upload failed after {max_attempts} attempts")
                return None

        if upload_resp.status_code == 308:
            # Chunk accepted, more to go
            uploaded = chunk_end + 1
            attempt = 0
            progress = (uploaded / file_size) * 100
            print(f"  Uploaded {progress:.0f}% ({uploaded:,}/{file_size:,}B)")
        elif upload_resp.status_code in (200, 201):
            # Final chunk — upload complete
            uploaded = file_size
            print(f"  ✅ Upload 100% complete")
        else:
            print(f"ERROR: Upload failed ({upload_resp.status_code})")
            print(upload_resp.text[:500])
            return None

    if upload_resp.status_code not in (200, 201):
        print(f"ERROR: Upload completed but unexpected status ({upload_resp.status_code})")
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


def delete_existing_videos_for_city(slug, city_title_prefix):
    """Find and delete any existing YouTube videos for this city before uploading the new one.

    This is a HARD GATE — prevents duplicate city videos on the channel.
    Searches the channel for videos whose titles start with the city name
    (e.g. "Denver Doula" matches "Denver Doula & Birth Plan Guide...").

    Args:
        slug: City slug (e.g. 'denver-co')
        city_title_prefix: Title prefix to match (e.g. 'Denver Doula' or 'Denver Birth')

    Returns list of deleted video IDs.
    """
    import requests

    token = get_access_token()
    auth = f"Bearer {token}"
    channel_id = "UCfXgNjzycfboUKVAC-eqabw"  # TJB channel ID

    print(f"\n  🔍 Checking for existing videos matching '{city_title_prefix}'...")

    deleted_ids = []

    # Search all channel videos for matching titles
    page_token = None
    matching_videos = []

    while True:
        params = {
            'part': 'snippet',
            'channelId': channel_id,
            'maxResults': '50',
            'type': 'video',
            'order': 'date',
        }
        if page_token:
            params['pageToken'] = page_token

        resp = requests.get(
            'https://www.googleapis.com/youtube/v3/search',
            headers={'Authorization': auth},
            params=params,
            timeout=30,
        )

        if resp.status_code != 200:
            print(f"  ⚠️  Search failed ({resp.status_code}) — skipping duplicate check")
            return []

        data = resp.json()
        for item in data.get('items', []):
            title = item['snippet']['title']
            vid_id = item['id']['videoId'] if item['id']['kind'] == 'youtube#video' else None
            if vid_id and city_title_prefix.lower() in title.lower():
                matching_videos.append({'id': vid_id, 'title': title})

        page_token = data.get('nextPageToken')
        if not page_token:
            break

    if not matching_videos:
        print(f"  ✅ No existing videos found for '{city_title_prefix}' — clean upload.")
        return []

    print(f"  ⚠️  Found {len(matching_videos)} existing video(s) for '{city_title_prefix}':")
    for v in matching_videos:
        print(f"     → {v['id']}: {v['title'][:65]}")

    # Delete all matching videos
    for v in matching_videos:
        print(f"  🗑️  Deleting {v['id']}...")
        del_resp = requests.delete(
            f"https://www.googleapis.com/youtube/v3/videos?id={v['id']}",
            headers={'Authorization': auth},
            timeout=30,
        )
        if del_resp.status_code == 204:
            print(f"     ✅ Deleted")
            deleted_ids.append(v['id'])
        else:
            print(f"     ⚠️  Delete failed ({del_resp.status_code}): {del_resp.text[:200]}")

    # Also update video-embeds.ts if any deleted IDs are referenced there
    embeds_path = VIDEO_EMBEDS_PATH
    if os.path.exists(embeds_path) and deleted_ids:
        with open(embeds_path) as f:
            content = f.read()
        for old_id in deleted_ids:
            if old_id in content:
                print(f"  ⚠️  WARNING: Deleted video {old_id} is still referenced in video-embeds.ts!")
                print(f"     Update the embed to the new video ID after upload completes.")

    return deleted_ids


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

    # ─── Pre-upload duplicate deletion gate (MANDATORY) ───
    # Extract city name from slug for title matching (e.g. "denver-co" → "Denver")
    city_name = slug.rsplit('-', 1)[0].replace('-', ' ').title()
    # Also try with the CITY_META title if available
    meta = get_city_meta(slug) or {}
    meta_title = meta.get('title', '')
    # Extract the city prefix from the title (everything before "Doula" or "Birth")
    import re as _re
    title_match = _re.match(r'^(.+?)\s+(?:Doula|Birth)', meta_title)
    city_title_prefix = title_match.group(1).strip() if title_match else city_name

    print(f"\n  Running duplicate deletion gate...")
    # PATCHED: Do NOT hard-delete — task requires old video → unlisted, not deleted.
    # deleted = delete_existing_videos_for_city(slug, city_title_prefix)
    deleted = []
    print(f"  ⏭️  Duplicate deletion skipped (old video will be set to unlisted post-upload).")
    if deleted:
        print(f"  🗑️  Deleted {len(deleted)} duplicate(s) before upload.")

    # ─── Pre-upload: record the PREVIOUS live video id (to unlist after) ───
    # Sources, in priority order: video-embeds.ts in the website repo, then the
    # out/{slug}-youtube-id.txt file. Anything recorded here that is still
    # PUBLIC gets set to unlisted after the new upload succeeds.
    prev_video_ids = set()
    import re as _re2
    embeds_path = VIDEO_EMBEDS_PATH if os.path.exists(VIDEO_EMBEDS_PATH) else None
    if embeds_path:
        embeds_path = __import__('pathlib').Path(embeds_path)
    id_file = os.path.join(PROJECT_DIR, 'out', f'{slug}-youtube-id.txt')
    if embeds_path:
        m = _re2.search(r'"%s":\s*\{[^}]*?videoId:\s*"([A-Za-z0-9_-]{11})"' % slug,
                        embeds_path.read_text(), _re2.S)
        if m:
            prev_video_ids.add(m.group(1))
            print(f"  Previous live video (embeds): {m.group(1)}")
    if os.path.exists(id_file):
        prev = open(id_file).read().strip()
        if re.fullmatch(r'[A-Za-z0-9_-]{11}', prev or ''):
            prev_video_ids.add(prev)
            print(f"  Previous video (id file): {prev}")
    if not prev_video_ids:
        print(f"  No previous video recorded for {slug} — nothing to unlist.")

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

    # Auto-append to video-embeds.ts if not already there
    meta = get_city_meta(slug)
    if meta:
        # Try to get duration from master WAV
        duration_seconds = 180  # default
        master_wav = os.path.join(PROJECT_DIR, 'public', 'audio', slug, f'{slug}-master.wav')
        if os.path.exists(master_wav):
            try:
                dur_result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                     '-of', 'default=noprint_wrappers=1:nokey=1', master_wav],
                    capture_output=True, text=True, timeout=10
                )
                if dur_result.returncode == 0 and dur_result.stdout.strip():
                    duration_seconds = float(dur_result.stdout.strip())
            except Exception:
                pass
        append_video_embed(slug, video_id, meta['title'], duration_seconds)

    print(f"\n✅ Upload to YouTube complete!")
    print(f"   https://youtu.be/{video_id}")
    print(f"   Embed:  https://www.youtube-nocookie.com/embed/{video_id}")

    # ─── Post-upload: swap embed videoId + unlist old public videos ───
    # The website embed must ALWAYS point at the new upload. The append
    # function skips existing slugs, so do an in-place videoId swap.
    if embeds_path:
        embeds_src = embeds_path.read_text()
        em = _re2.search(r'("%s":\s*\{[^}]*?videoId:\s*")([A-Za-z0-9_-]{11})(")' % slug, embeds_src, _re2.S)
        if em and em.group(2) != video_id:
            embeds_src = embeds_src[:em.start(2)] + video_id + embeds_src[em.end(2):]
            embeds_path.write_text(embeds_src)
            print(f"  🔁 Embed videoId swapped: {em.group(2)} -> {video_id}")
            print(f"     (website repo — commit + deploy to publish)")
        elif em:
            print(f"  Embed already points at {video_id}")
        else:
            print(f"  ⚠️ No embed entry found for {slug} in video-embeds.ts — append step should have added it")

    # Unlist every previously-live video that is still PUBLIC
    if prev_video_ids:
        try:
            token = get_access_token()
            for old_id in prev_video_ids:
                if old_id == video_id:
                    continue
                chk = subprocess.run(
                    ['curl', '-s', f'https://www.googleapis.com/youtube/v3/videos?part=status&id={old_id}',
                     '-H', f'Authorization: Bearer {token}'], capture_output=True, text=True, timeout=30)
                import json as _json
                items = _json.loads(chk.stdout).get('items', [])
                privacy = items[0]['status']['privacyStatus'] if items else 'missing'
                if privacy == 'public':
                    up = __import__('requests').put(
                        'https://www.googleapis.com/youtube/v3/videos?part=status',
                        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                        json={'id': old_id, 'status': {'privacyStatus': 'unlisted'}}, timeout=30)
                    print(f"  🔒 Unlisted old video {old_id} (was public) — rc={up.status_code}")
                else:
                    print(f"  ✓ Old video {old_id} already {privacy}")
        except Exception as e:
            print(f"  ⚠️ Could not unlist old videos automatically: {e}")
            print(f"     MANUAL STEP: set {', '.join(prev_video_ids - {video_id})} to unlisted")

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