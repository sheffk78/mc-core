// ════════════════════════════════════════════════════════════════════════════
// Tacoma — Scene data for the Tacoma, WA city guide video
// Custom-written for Tacoma's specific hospitals, costs, and Medicaid info
// ════════════════════════════════════════════════════════════════════════════

import { TJBCityVideoData } from './types';

export const tacomaWaData: TJBCityVideoData = {
  video_metadata: {
    title: "Tacoma Birth Guide: Hospitals, Doulas, Midwives & More",
    city: "Tacoma",
    state: "WA",
    slug: "tacoma-wa",
    duration_seconds: 193.44,
    fps: 30,
    medicaid: true,
    hasBirthCenter: false,
    hasAppScreenshot: true,
  },
  scenes: [
    {
      scene_id: "01_hook",
      scene_type: "tjb_city_hook",
      duration_seconds: 11.20,
      narration: "Just found out you're pregnant in Tacoma? Awesome. Now you've got eighty tabs open on hospitals, doulas, midwives, insurance. Let's close every single one of them right now.",
      text_content: {
        city: "Tacoma",
        state: "Washington",
        slug: "tacoma-wa",
        subtitle: "Your Birth Planning Guide",
      },
      image_source: "images/tacoma-wa-birth-doula-skyline.webp",
    },
    {
      scene_id: "02_overview",
      scene_type: "tjb_city_bridge",
      duration_seconds: 22.08,
      narration: "Here's what we're covering in this video: which hospitals welcome doulas and midwives, the doulas and midwives you can work with in Tacoma, what everything costs including midwifery care, how Washington Apple Health can help, and a free app that builds your birth plan step by step. Let's start with where you can deliver.",
      text_content: {
        city: "Tacoma",
        state: "WA",
      },
    },
    {
      scene_id: "03a_tacoma_general",
      scene_type: "tjb_hospital_card",
      duration_seconds: 21.20,
      narration: "Tacoma General Hospital on Martin Luther King Jr Way is Pierce County's largest birth hospital with around 4,000 deliveries per year. It has a Level 4 NICU through the adjacent Mary Bridge Children's Hospital, private birthing suites with jetted tubs, and doulas are integrated into the TeamBirth process. They also have an on-site lactation boutique.",
      image_source: "images/tacoma-tacoma-general-hospital.webp",
      text_content: {
        name: "Tacoma General Hospital – MultiCare",
        address: "315 Martin Luther King Jr Way, Tacoma, WA 98405",
        nicuLevel: "IV",
        badges: ["Level IV NICU", "Doula-Friendly", "Private Suites", "Midwifery Program"],
        description: "Pierce County's largest birth hospital with a full midwifery practice and private birthing suites, serving roughly 4,000 deliveries per year. Doulas are integrated into the TeamBirth shared decision-making process.",
      },
    },
    {
      scene_id: "03b_st_joseph",
      scene_type: "tjb_hospital_card",
      duration_seconds: 21.28,
      narration: "St. Joseph Medical Center on Tacoma's Hilltop has a Level 3 NICU with a collaborative midwifery program, beautiful remodeled private birthing suites with city and mountain views, and waterbirth is available. They support VBAC and have 24/7 OB hospitalists on site with IBCLC certified lactation consultants.",
      image_source: "images/tacoma-st-joseph-hospital.webp",
      text_content: {
        name: "St. Joseph Medical Center – Virginia Mason Franciscan Health",
        address: "1717 South J Street, Tacoma, WA 98405",
        nicuLevel: "III",
        badges: ["Level III NICU", "Doula-Friendly", "Waterbirth", "Midwifery Program", "VBAC Supported"],
        description: "A Level III NICU hospital on Tacoma's Hilltop offering maternal-fetal medicine, collaborative midwifery program, private birthing suites with city and mountain views. Waterbirth and VBAC are supported.",
      },
    },
    {
      scene_id: "03c_good_sam",
      scene_type: "tjb_hospital_card",
      duration_seconds: 22.80,
      narration: "Good Samaritan Hospital in Puyallup, just east of Tacoma, has a Level 2 NICU with 24/7 neonatology coverage and a well-regarded midwifery integrated birth unit. All rooms are private birthing suites with jetted tubs, wireless monitoring for mobility during labor, and nitrous oxide is available for pain management.",
      image_source: "images/tacoma-good-samaritan-hospital.webp",
      text_content: {
        name: "Good Samaritan Hospital – MultiCare (Puyallup)",
        address: "1802 E 39th Ave, Puyallup, WA 98372",
        nicuLevel: "II",
        badges: ["Level II NICU", "Doula-Friendly", "Midwifery Unit", "Private Suites", "Nitrous Oxide"],
        description: "Located just east of Tacoma in Puyallup, features a Level II NICU with 24/7 neonatology coverage and a midwifery-integrated birth unit. All rooms are private birthing suites with jetted tubs.",
      },
    },
    {
      scene_id: "04_providers",
      scene_type: "tjb_provider_grid",
      duration_seconds: 8.48,
      narration: "Tacoma has experienced doulas and midwives ready to support you. See who's serving your area — and message them directly — in the app.",
      text_content: {
        providerCount: 12,
        screenshotPath: "images/tjb-app-dashboard.webp",
        description: "Tacoma's doula community includes Katie Pumphrey of MamaEarth Doula, Adrianne Buyer, Kristin Lanning of Called To Birth, and Allie Wright of Alma Birth Doula — each offering personalized birth and postpartum support across Pierce County.",
        costRange: "$1,200–$3,500",
        serviceArea: ["Tacoma", "Puyallup", "Lakewood", "Gig Harbor"],
        acceptingClients: true,
        services: ["Birth Doula", "Postpartum", "Lactation", "Childbirth Education"],
      },
    },
    {
      scene_id: "05_app",
      scene_type: "tjb_app_feature",
      duration_seconds: 23.84,
      narration: "Here's the part every Tacoma mom should know about. The True Joy Birthing app is completely free — no account, no catch. Nine guided sections walk you through your entire birth plan. You can find and message doulas and midwives near you right inside the app. Then export your plan as a PDF to share with your provider. It's the tool every mom needs in her pocket.",
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
      duration_seconds: 17.12,
      narration: "In Tacoma, doulas typically charge between one thousand two hundred and three thousand five hundred dollars for full spectrum support. Midwives range from five thousand to eight thousand dollars depending on the type of care. Most offer payment plans, so don't let price stop you from reaching out.",
      text_content: {
        costRange: "Doulas: $1.2K–$3.5K \u00b7 Midwives: $5K–$8K",
        label: "Birth support costs in Tacoma",
        description: "Most doulas and midwives offer payment plans. Some doulas in Tacoma accept Washington Apple Health (Medicaid). Start interviewing around week 20, book by week 28.",
        numericLow: 1200,
        numericHigh: 8000,
      },
    },
    {
      scene_id: "07_insurance",
      scene_type: "tjb_insurance_branch",
      duration_seconds: 24.24,
      narration: "Great news — Washington Apple Health covers doula services statewide, including Pierce County. Doulas register with the Washington State Department of Health and bill through ProviderOne, with reimbursement around fifteen hundred dollars per birth package covering prenatal visits, labor support, and postpartum follow-up. And most commercial insurance plans in Washington cover midwifery care, too.",
      text_content: {
        branch: "covers",
        stateName: "Washington",
        headline: "Apple Health Covers Doulas in Washington",
        detail: "Washington Apple Health (Medicaid) reimburses doulas approximately $1,500 per birth package, covering prenatal visits, labor support, and postpartum follow-up. Doulas must register with the Washington State Department of Health and bill through ProviderOne. CNM midwifery care is covered by most private insurance in Washington, and state law requires plans to cover midwife and birth center care.",
        policyBadge: "Apple Health Medicaid",
        amount: "~$1,500/birth",
        phoneNumber: "1-800-562-3022",
      },
    },
    {
      scene_id: "08_cta",
      scene_type: "tjb_city_cta",
      duration_seconds: 21.20,
      narration: "Your birth plan is one of the most important tools you'll have. It tells your care team exactly what matters to you — who you want in the room, how you want to manage pain, what happens after delivery. You can build yours with the free PDF birth plan, watch our walkthrough series, or use the mobile app. All free. All designed to help you walk into your birth confident and prepared.",
      text_content: {
        city: "Tacoma",
        slug: "tacoma-wa",
      },
    },
  ],
};
