// ════════════════════════════════════════════════════════════════════════════
// Norfolk — Scene data for the Norfolk, VA city guide video
// Custom-written for Norfolk's specific hospitals, costs, and Medicaid info
// ════════════════════════════════════════════════════════════════════════════

import { TJBCityVideoData } from './types';

export const norfolk_vaData: TJBCityVideoData = {
  video_metadata: {
    title: "Norfolk Birth Guide: Hospitals, Doulas, Midwives & More",
    city: "Norfolk",
    state: "VA",
    slug: "norfolk-va",
    duration_seconds: 196.93,
    fps: 30,
    medicaid: true,
    hasBirthCenter: false,
    hasAppScreenshot: true,
  },
  scenes: [
    {
      scene_id: "01_hook",
      scene_type: "tjb_city_hook",
      duration_seconds: 11.23,
      narration: "Just found out you're pregnant in Norfolk? Awesome. Now you've got eighty tabs open on hospitals, doulas, midwives, insurance. Let's close every single one of them right now.",
      text_content: {
        city: "Norfolk",
        state: "Virginia",
        slug: "norfolk-va",
        subtitle: "Your Birth Planning Guide",
      },
      image_source: "images/norfolk-va-birth-doula-skyline.webp",
    },
    {
      scene_id: "02_overview",
      scene_type: "tjb_city_bridge",
      duration_seconds: 18.24,
      narration: "Here's what we're covering in this video: which hospitals welcome doulas and midwives, the doulas and midwives you can work with in Norfolk, what everything costs including midwifery care, how Virginia Medicaid can help, and a free app that builds your birth plan step by step. Let's start with where you can deliver.",
      text_content: {
        city: "Norfolk",
        state: "VA",
      },
    },
    {
      scene_id: "03a_sentara_norfolk",
      scene_type: "tjb_hospital_card",
      duration_seconds: 27.20,
      narration: "Sentara Norfolk General Hospital on Gresham Drive is a 563-bed academic teaching hospital and the only Level I trauma center in Hampton Roads. It has a full obstetrics program with a NICU and direct access to CHKD's pediatric specialists. Doulas are generally welcome here — confirm current policies during your hospital tour.",
      text_content: {
        name: "Sentara Norfolk General Hospital",
        address: "600 Gresham Dr, Norfolk, VA 23507",
        badges: ["Level I Trauma", "Teaching Hospital", "Doula-Friendly", "NICU"],
        description: "563-bed academic hospital for EVMS, the region's only Level I trauma center with full obstetrics program and direct access to CHKD's pediatric specialists for higher-risk cases.",
      },
      image_source: "images/sentara-norfolk-hospital.webp",
    },
    {
      scene_id: "03b_chkd",
      scene_type: "tjb_hospital_card",
      duration_seconds: 23.20,
      narration: "Children's Hospital of The King's Daughters sits right next to Sentara in the Ghent neighborhood. CHKD is a 206-bed freestanding children's hospital. It doesn't handle deliveries itself, but its neonatal and pediatric specialists work closely with Sentara's labor and delivery team for any infant needing advanced care after birth.",
      text_content: {
        name: "Children's Hospital of The King's Daughters",
        address: "601 Children's Lane, Norfolk, VA 23507",
        badges: ["Pediatric Specialty", "Neonatal Care", "Adjacent to Sentara"],
        description: "206-bed freestanding children's hospital adjacent to Sentara in Ghent. Pediatric and neonatal specialists collaborate with Sentara's L&D team for infants needing advanced care.",
      },
      image_source: "images/chkd-hospital.webp",
    },
    {
      scene_id: "04_providers",
      scene_type: "tjb_provider_scroll",
      duration_seconds: 15.60,
      narration: "Norfolk has over two dozen doulas and midwives ready to support you. Birth doulas, postpartum specialists, overnight support — browse everyone serving your area and message them directly right in the app.",
      text_content: {
        screenshotPath: "images/norfolk-fullpage-scroll.png",
        providerCount: 26,
        maxScroll: 3420,
        city: "Norfolk",
      },
    },
    {
      scene_id: "05_app",
      scene_type: "tjb_app_feature",
      duration_seconds: 24.88,
      narration: "Here's the part every Norfolk mom should know about. The True Joy Birthing app is completely free — no account, no catch. Nine guided sections walk you through your entire birth plan. You can find and message doulas and midwives near you right inside the app. Then export your plan as a PDF to share with your provider. It's the tool every mom needs in her pocket.",
      text_content: {
        headline: "Build Your Birth Plan",
        screenshotPath: "images/tjb-app-dashboard.webp",
        features: [
          "Nine guided sections — hospital preferences, pain management, who's in the room",
          "Find and connect with doulas AND midwives near you",
          "Export a PDF to share with your provider or midwife",
          "Free. No account needed. Works on iPhone.",
        ],
        subtitle: "Free \u00b7 No account needed",
      },
    },
    {
      scene_id: "06_cost",
      scene_type: "tjb_cost_reveal",
      duration_seconds: 24.28,
      narration: "In Norfolk, doulas typically charge between one thousand two hundred and two thousand five hundred dollars. Doulas offer payment plans, and some accept Virginia Medicaid directly. Midwifery care runs five thousand to eight thousand dollars depending on the type of care, and many midwives in Virginia accept insurance. The investment is real, but the right support makes every difference.",
      text_content: {
        costRange: "$1,200\u2013$2,500",
        label: "Doulas \u00b7 $1K\u2013$3K \u00b7 Midwives \u00b7 $5K\u2013$8K",
        description: "Most doulas offer payment plans. Some in Norfolk accept Virginia Medicaid. Midwives often accept insurance.",
        numericLow: 1200,
        numericHigh: 8000,
      },
    },
    {
      scene_id: "07_insurance",
      scene_type: "tjb_insurance_branch",
      duration_seconds: 30.60,
      narration: "Great news — Virginia covers doula services through Medicaid, effective January first, 2024. Families on VA Medicaid can get doula support through their managed care plan with reimbursement managed by the Virginia Department of Medical Assistance Services. Midwifery care including CNM midwives is covered by most private insurance plans in Virginia. And if you're near the naval base, check your Tricare plan — some Tricare options now include doula benefits.",
      text_content: {
        branch: "covers",
        stateName: "Virginia",
        headline: "Virginia Medicaid Covers Doulas",
        detail: "Virginia Medicaid has covered doula services since January 1, 2024. Families access doula support through their managed care plan. Reimbursement rates and doula enrollment requirements are managed through the Virginia Department of Medical Assistance Services.",
        policyBadge: "Virginia Medicaid",
        amount: "Covered since 2024",
        phoneNumber: "1-855-242-8282",
      },
    },
    {
      scene_id: "08_cta",
      scene_type: "tjb_city_cta",
      duration_seconds: 21.70,
      narration: "Your birth plan is one of the most important tools you'll have. It tells your care team exactly what matters to you — who you want in the room, how you want to manage pain, what happens after delivery. You can build yours with the free PDF birth plan, watch our walkthrough series, or use the mobile app. All free. All designed to help you walk into your birth confident and prepared. We'll put the link below.",
      text_content: {
        city: "Norfolk",
        slug: "norfolk-va",
      },
    },
  ],
};
