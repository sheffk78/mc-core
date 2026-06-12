// ════════════════════════════════════════════════════════════════════════════
// ProviderScrollSlide (tjb_provider_scroll) — Full-screen browser scroll
// through the Fremont provider directory. No phone frame.
// The screenshot spans from "Doulas & Midwives Serving Fremont" through
// all provider cards and into the next section (Hospitals).
// Scroll stops at content end — never hits blank white space.
// ════════════════════════════════════════════════════════════════════════════

import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate, Easing, Img, staticFile, useVideoConfig } from 'remotion';
import { TJB } from '../style/tjb-tokens';
import { TJBBrandChrome } from './TJBBrandChrome';

export interface ProviderScrollSlideProps {
  screenshotPath: string;
  providerCount: number;
  /**
   * Total scrollable pixels in the screenshot.
   * Screenshot is 1920xN, but we only scroll the vertical.
   * The visible area is 1080px tall, so maxScroll = N - 1080.
   */
  maxScroll: number;
  city: string;
}

export const ProviderScrollSlide: React.FC<ProviderScrollSlideProps> = ({
  screenshotPath,
  providerCount,
  maxScroll,
  city,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Fade in
  const sectionOpacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.ease),
  });

  // Vertical scroll: starts a few frames in, ends slightly before the audio finishes
  const scrollStart = 5;
  const scrollEnd = durationInFrames - 8;

  const scrollProgress = interpolate(frame, [scrollStart, scrollEnd], [0, maxScroll], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.ease),
  });

  // Top fade gradient to make the scroll edge feel natural
  const topFadeOpaque = interpolate(frame, [scrollStart, scrollStart + 8], [0.8, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Count badge slide-in
  const badgeOpacity = interpolate(frame, [5, 18], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.ease),
  });
  const badgeY = interpolate(frame, [5, 18], [-20, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.ease),
  });

  return (
    <AbsoluteFill style={{ background: '#fff', fontFamily: TJB.FONT_BODY }}>
      {/* Full-screen scrolling page content */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 1920,
          height: 1080,
          overflow: 'hidden',
        }}
      >
        <Img
          src={staticFile(screenshotPath)}
          style={{
            width: 1920,
            height: 'auto',
            position: 'absolute',
            top: -scrollProgress,
            left: 0,
            opacity: sectionOpacity,
          }}
        />

        {/* Top fade — soft gradient at the top edge */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 60,
            background: `linear-gradient(180deg, rgba(255,255,255,1) 0%, rgba(255,255,255,0.85) 30%, rgba(255,255,255,0) 100%)`,
            opacity: topFadeOpaque,
            pointerEvents: 'none',
            zIndex: 5,
          }}
        />

        {/* Bottom fade — soft blend into the chrome */}
        {/* NOTE: This must use WHITE (255,255,255) to match the web page screenshot
             background. Using a warm off-white like BG_LIGHT (#FAF8F5) creates a visible
             horizontal gradient band. Fixed June 12, 2026. */}
        <div
          style={{
            position: 'absolute',
            bottom: TJB.FOOTER_HEIGHT,
            left: 0,
            right: 0,
            height: 40,
            background: `linear-gradient(0deg, rgba(255,255,255,1) 0%, rgba(255,255,255,0) 100%)`,
            pointerEvents: 'none',
            zIndex: 5,
          }}
        />
      </div>

      {/* Provider count badge — top right corner */}
      <div
        style={{
          position: 'absolute',
          top: 30,
          right: 40,
          zIndex: 10,
          opacity: badgeOpacity,
          transform: `translateY(${badgeY}px)`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            background: 'rgba(255,255,255,0.92)',
            backdropFilter: 'blur(8px)',
            borderRadius: 40,
            padding: '10px 22px',
            boxShadow: '0 4px 20px rgba(110,108,153,0.12)',
          }}
        >
          <span style={{
            fontFamily: TJB.FONT_HEADLINE,
            fontSize: 32,
            fontWeight: 700,
            color: TJB.LAVENDER_600,
            lineHeight: 1,
          }}>
            {providerCount}
          </span>
          <span style={{
            fontFamily: TJB.FONT_BODY,
            fontSize: 17,
            fontWeight: 600,
            color: TJB.LAVENDER_500,
          }}>
            doulas &amp; midwives
          </span>
        </div>
        <p style={{
          fontFamily: TJB.FONT_BODY,
          fontSize: 14,
          color: TJB.MUTED,
          lineHeight: 1.4,
          margin: 0,
          marginTop: 8,
          textAlign: 'right',
          maxWidth: 300,
          background: 'rgba(255,255,255,0.7)',
          padding: '4px 16px',
          borderRadius: 20,
        }}>
          Real providers serving {city} — browse photos, services, and availability
        </p>
      </div>

      <TJBBrandChrome variant="light" />
    </AbsoluteFill>
  );
};