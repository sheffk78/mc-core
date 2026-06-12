// ══════════════════════════════════════════════════════════════════════════════
// Fremont — Scene data for the Fremont, CA city guide video v4
// Durations updated from actual Voxtral TTS output
// ══════════════════════════════════════════════════════════════════════════════

import { TJBCityVideoData } from './types';

export const fremont_caData: TJBCityVideoData = {
  video_metadata: {
    title: "Fremont Birth Guide: Hospitals, Doulas, Midwives & More",
    city: "Fremont",
    state: "CA",
    slug: "fremont-ca",
    duration_seconds: 180.84,
    fps: 30,
    medicaid: true,
    hasBirthCenter: false,
    hasAppScreenshot: true,
  },
  scenes: [
    {
      scene_id: "01_hook",
      scene_type: "tjb_city_hook",
      duration_seconds: 13.07,
      narration: "Just found out you're pregnant in Fremont? Awesome. Now you've got eighty tabs open on hospitals, doulas, midwives, insurance. Let's close every single one of them right now.",
      text_content: {
        city: "Fremont",
        state: "CA",
        slug: "fremont-ca",
        subtitle: "Your Birth Planning Guide",
      },
      image_source: "images/fremont-ca-birth-doula-skyline.webp",
    },
    {
      scene_id: "02_overview",
      scene_type: "tjb_city_bridge",
      duration_seconds: 20.37,
      narration: "Here's what we're covering in this video: which hospitals welcome doulas and midwives, the doulas and midwives you can work with in Fremont, what everything costs including midwifery care, how California Medi-Cal can help, and a free app that builds your birth plan step by step. Let's start with where you can deliver.",
      text_content: {
        city: "Fremont",
        state: "CA",
      },
    },
    {
      scene_id: "03a_washington_hospital",
      scene_type: "tjb_hospital_card",
      duration_seconds: 24.56,
      narration: "Washington Hospital on Mowry Avenue near I-880 is Fremont's community hospital with a Special Care Nursery for babies who need extra monitoring. It handles about two thousand deliveries per year and they have twenty-four seven OB hospitalist coverage. Doulas are welcome, and they accept Medi-Cal. One heads up: the I-880 interchange near the hospital backs up significantly during commute hours — plan your route around that.",
      image_source: "images/fremont-ca-birth-doula-skyline.webp",
      text_content: {
        name: "Washington Hospital",
        address: "2000 Mowry Ave, Fremont, CA 94538",
        nicuLevel: "II",
        badges: ["Special Care Nursery", "Doula-Friendly", "Medi-Cal Accepted", "24/7 OB Coverage"],
        description: "Fremont's community hospital with ~2,000 births/year. 24/7 OB hospitalist coverage, Special Care Nursery, and doula-friendly policies.",
      },
    },
    {
      scene_id: "03b_el_camino_health",
      scene_type: "tjb_hospital_card",
      duration_seconds: 19.04,
      narration: "El Camino Health in Mountain View, about fifteen minutes south of Fremont, has a Level III NICU and a dedicated birth center. It's one of the region's highest-rated maternity programs. Doulas are welcome, and they offer private suites, water birth options, and lactation support. Also accepts Medi-Cal.",
      text_content: {
        name: "El Camino Health — Mountain View",
        address: "2500 Grant Rd, Mountain View, CA 94040",
        nicuLevel: "III",
        badges: ["Level III NICU", "Doula-Friendly", "Waterbirth", "Private Suites", "IBCLC"],
        description: "One of the region's highest-rated maternity programs, ~15 min south of Fremont. Level III NICU, waterbirth, private suites, and lactation support.",
      },
      image_source: "images/el-camino-hospital.webp",
    },
    {
      scene_id: "04_providers",
      scene_type: "tjb_provider_scroll",
      duration_seconds: 15.60,
      narration: "Fremont has over two dozen doulas and midwives ready to support you. Birth doulas, postpartum specialists, lactation consultants, overnight care — browse everyone serving your area and message them directly right in the app.",
      text_content: {
        screenshotPath: "images/fremont-fullpage-scroll.png",
        providerCount: 33,
        maxScroll: 5200,
        city: "Fremont",
      },
    },
    {
      scene_id: "05_app",
      scene_type: "tjb_app_feature",
      duration_seconds: 24.1,
      narration: "Here's the part every Fremont mom should know about. The True Joy Birthing app is completely free, no account, no catch. Nine guided sections walk you through your entire birth plan. You can find and message doulas and midwives near you right inside the app. Then export your plan as a PDF to share with your provider. It's the tool every mom needs in her pocket.",
      text_content: {
        headline: "Build Your Birth Plan",
        screenshotPath: "images/tjb-app-dashboard.webp",
        features: [
          "Nine guided sections — hospital preferences, pain management, who's in the room",
          "Find and connect with doulas and midwives near you",
          "Export a PDF to share with your provider",
          "Free. No account needed. Works on iPhone.",
        ],
      },
    },
    {
      scene_id: "06_cost",
      scene_type: "tjb_cost_reveal",
      duration_seconds: 22.83,
      narration: "Here's the reality: a doula in Fremont typically costs $1,500 to $3,000. Most doulas offer payment plans, and some accept Medi-Cal. Midwifery care runs $5,000 to $8,000 for home birth or birth center care, and many midwives accept insurance. The investment is real, but the support is worth every dollar.",
      text_content: {
        costRange: "$1,500–$3,000",
        label: "Doulas · $1K–$3K · Midwives · $5K–$8K",
        description: "Most doulas offer payment plans. Midwives often accept insurance.",
      },
    },
    {
      scene_id: "07_insurance",
      scene_type: "tjb_insurance_branch",
      duration_seconds: 22.2,
      narration: "California's Medi-Cal program covers doula services through the PAVE program, reimbursing around $1,587 per pregnancy. Midwives are covered by most insurance plans in California. Even if you have private insurance, some plans now include doula benefits. The app has resources to help you navigate your options.",
      text_content: {
        branch: "covers",
        stateName: "CA",
        headline: "Medi-Cal covers doula and midwifery care",
        detail: "California's Medi-Cal program covers doula services through the PAVE program, reimbursing around $1,587 per pregnancy. Midwifery care including home birth and birth center delivery is covered by most Medi-Cal plans. Private insurance in California is increasingly including doula benefits — check your plan for details.",
        policyBadge: "PAVE Program",
        amount: "~$1,587 per pregnancy",
        phoneNumber: "1-800-880-5305",
      },
    },
    {
      scene_id: "08_cta",
      scene_type: "tjb_city_cta",
      duration_seconds: 19.07,
      narration: "A birth plan tells your care team exactly what matters to you, who you want in the room, how you want to manage pain, what happens after delivery. You can build yours with the free PDF template, watch our walkthrough series, or use the mobile app. It's all free, and it's all ready for you right now.",
      text_content: {
        city: "Fremont",
        slug: "fremont-ca",
      },
    },
  ],
};