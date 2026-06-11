// ════════════════════════════════════════════════════════════════════════════
// Root — Remotion entry point, registers all compositions
// ════════════════════════════════════════════════════════════════════════════

import React from 'react';
import { Composition, Folder } from 'remotion';
import { TJB } from './style/tjb-tokens';
import { TJBCityVideo } from './TJBCityVideo';
import { denverData, denverFirstTwoScenes } from './data/denver-example';
import { norfolk_vaData } from './data/norfolk-va-data';
import { tacomaWaData } from './data/tacoma-wa-data';
import {
  CityHookSlide,
  CityBridgeSlide,
  HospitalCardSlide,
  ProviderPortraitSlide,
  AppFeatureSlide,
  CostRevealSlide,
  InsuranceBranchSlide,
  CityCTASlide,
} from './scenes/index';

const fps = 30;

// Full Denver video
const totalFrames = denverData.scenes.reduce(
  (sum: number, s: { duration_seconds: number }) => sum + Math.max(Math.round(s.duration_seconds * fps), 1),
  0
);

// First-two-scenes test (54s of audio)
const firstTwoFrames = denverFirstTwoScenes.scenes.reduce(
  (sum: number, s: { duration_seconds: number }) => sum + Math.max(Math.round(s.duration_seconds * fps), 1),
  0
);

export const Root: React.FC = () => {
  return (
    <>
      <Folder name="TJB-City-Videos">
        <Composition
          id="Tacoma-City-Guide"
          component={TJBCityVideo}
          durationInFrames={tacomaWaData.scenes.reduce((s, c) => s + Math.max(Math.round(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: tacomaWaData, audioPath: 'audio/tacoma-wa/denver-master.wav'}}
        />


        <Composition
          id="norfolk-va-City-Guide"
          component={TJBCityVideo}
          durationInFrames={norfolk_vaData.scenes.reduce((s, c) => s + Math.max(Math.round(c.duration_seconds * 30), 1), 0)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{videoData: norfolk_vaData, audioPath: 'audio/norfolk-va/norfolk-master.wav'}}
        />
        <Composition
          id="Denver-City-Guide"
          component={TJBCityVideo}
          durationInFrames={totalFrames}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{
            videoData: denverData,
            audioPath: 'audio/denver-co/denver-master.wav',
          }}
        />

        <Composition
          id="Denver-60s-Test"
          component={TJBCityVideo}
          durationInFrames={firstTwoFrames}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{
            videoData: denverFirstTwoScenes,
            audioPath: 'audio/denver-co/denver-master.wav',
          }}
        />

        {/* ── Individual slide test compositions ── */}
        <Composition
          id="test-app-section"
          component={TJBCityVideo}
          durationInFrames={Math.ceil(24.00 * 30)}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{
            videoData: {
              video_metadata: {
                title: "App Section Test",
                city: "Denver",
                state: "CO",
                slug: "denver-co",
                duration_seconds: 24.00,
                fps: 30,
                medicaid: true,
                hasBirthCenter: false,
                hasAppScreenshot: false,
              },
              scenes: [denverData.scenes.find(s => s.scene_id === "04_app")!],
            },
            audioPath: 'audio/denver-co/denver-master.wav',
          }}
        />

        <Composition
          id="test-city-hook"
          component={() => <CityHookSlide city="Denver" state="Colorado" slug="denver-co" subtitle="Your Birth Planning Guide" skylineImage="images/denver-co-birth-doula-skyline.webp" />}
          durationInFrames={90}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-city-bridge"
          component={() => <CityBridgeSlide city="Denver" state="Colorado" slug="denver-co" />}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-hospital-card"
          component={() => (
            <HospitalCardSlide
              name="UCHealth University of Colorado Hospital"
              address="12605 E 16th Ave, Aurora, CO 80045"
              nicuLevel="III"
              photo="images/denver-uchealth-hospital.webp"
              badges={["Level III NICU", "Doula-Friendly", "Medicaid", "VBAC Supported"]}
              description="The region's academic medical center and highest-level NICU provider in the state. VBAC is supported, doulas welcome as part of the care team."
            />
          )}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-portrait-verified"
          component={() => (
            <ProviderPortraitSlide
              name="Sonja Spitzer"
              practice="Embrace Birth Services"
              photo="images/doulas/sonja-spitzer.webp"
              isVerified={true}
              isMidwife={false}
              description="Former family law attorney turned doula. CAPPA certified postpartum doula. Offers birth and postpartum support."
              costRange="$1,200\u2013$1,900"
              serviceArea={["Denver", "Golden", "Lakewood"]}
              acceptingClients={true}
              services={["Birth Doula", "Postpartum Doula", "Childbirth Education"]}
            />
          )}
          durationInFrames={90}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-portrait-midwife"
          component={() => (
            <ProviderPortraitSlide
              name="Melissa Sexton & Samantha Venn"
              practice="Meadowsweet Midwifery"
              photo="images/doulas/meadowsweet-midwifery.webp"
              isVerified={true}
              isMidwife={true}
              description="Home birth midwifery practice serving Denver since 2010. Offering prenatal, birth, and postpartum care."
              costRange="$6,500 (global fee)"
              serviceArea={["Denver", "Lakewood", "Arvada"]}
              acceptingClients={true}
              services={["Home Birth", "Prenatal Care", "Postpartum Care", "Water Birth"]}
            />
          )}
          durationInFrames={90}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-app-feature"
          component={() => (
            <AppFeatureSlide
              headline="Build Your Birth Plan"
              features={[
                "Nine guided sections — hospital preferences, pain management, who's in the room",
                "Find and connect with doulas and midwives near you",
                "Export a PDF to share with your provider",
                "Free. No account needed. Works on iPhone.",
              ]}
              subtitle="Free \u00b7 No account needed"
            />
          )}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-cost-reveal"
          component={() => (
            <CostRevealSlide
              costRange="$1,000\u2013$3,000"
              label="Average doula cost in Denver"
              description="Most doulas offer payment plans. Start interviewing around week 20, book by week 28."
            />
          )}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-insurance-covers"
          component={() => (
            <InsuranceBranchSlide
              branch="covers"
              stateName="Colorado"
              headline="Medicaid Covers Doulas in Colorado"
              detail="Health First Colorado (the state's Medicaid program) reimburses doulas up to $750 per birth for a full spectrum doula package: prenatal, labor, and postpartum visits."
              policyBadge="HB 23-1027"
              amount="$750/birth"
              phoneNumber="1-800-221-3943"
            />
          )}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-insurance-no-coverage"
          component={() => (
            <InsuranceBranchSlide
              branch="no_coverage"
              stateName="Georgia"
              headline="Georgia Medicaid Doesn't Cover Doulas Right Now"
              detail="Most doulas offer sliding-scale fees and payment plans. Ask when you interview. The Joyful Birth Plan app is always free, no matter what."
            />
          )}
          durationInFrames={120}
          fps={fps}
          width={1920}
          height={1080}
        />

        <Composition
          id="test-city-cta"
          component={() => (
            <CityCTASlide
              city="Denver"
              slug="denver-co"
            />
          )}
          durationInFrames={90}
          fps={fps}
          width={1920}
          height={1080}
        />
      </Folder>
    </>
  );
};