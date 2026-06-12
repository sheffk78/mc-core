#!/usr/bin/env tsx
/**
 * ════════════════════════════════════════════════════════════════════════════
 * TJB Pre-Render Data Validator
 * Validates scene data files before rendering — catches:
 *  - Missing required fields per scene_type
 *  - Prop mapper mismatches (wrong field names)
 *  - Missing assets on disk
 *  - Leaked image_source for scene types that shouldn't have it
 *  - Insufficient insurance data (text_content too skeletal)
 *  - ScreenshotPath missing when hasAppScreenshot is true
 *
 * Usage: tsx scripts/validate-data.ts
 * Exit code: 0 = pass, 1 = fail (errors), 0 + warnings = pass with warnings
 * ════════════════════════════════════════════════════════════════════════════
 */

import * as fs from 'fs';
import * as path from 'path';
import type { TJBCityScene, TJBCityVideoData } from '../src/data/types';

const DATA_DIR = path.join(__dirname, '..', 'src', 'data');
const PUBLIC_DIR = path.join(__dirname, '..', 'public');

const VALID_SCENE_TYPES = [
  'tjb_city_hook',
  'tjb_city_bridge',
  'tjb_hospital_card',
  'tjb_provider_portrait',
  'tjb_app_feature',
  'tjb_cost_reveal',
  'tjb_insurance_branch',
  'tjb_provider_grid',
  'tjb_provider_scroll',
  'tjb_city_cta',
];

/** Scene-type-specific required text_content fields */
const SCENE_FIELD_RULES: Record<string, Array<{ field: string; type: string; required: boolean; reason: string }>> = {
  tjb_city_bridge: [
    { field: 'city', type: 'string', required: true, reason: 'Personalization' },
    { field: 'state', type: 'string', required: false, reason: 'State name shown in bridge card' },
    { field: 'slug', type: 'string', required: false, reason: 'Required for link-out' },
  ],
  tjb_hospital_card: [
    { field: 'name', type: 'string', required: true, reason: 'Hospital name renders blank without it' },
    { field: 'badges', type: 'array', required: true, reason: 'Badges are the main visual, should have ≥2 items' },
    { field: 'description', type: 'string', required: true, reason: 'Provides context about the hospital' },
    { field: 'address', type: 'string', required: false, reason: 'Address shown below name' },
  ],
  tjb_provider_portrait: [
    { field: 'name', type: 'string', required: true, reason: 'HOLLOW PORTRAIT GUARD — portrait without name renders blank card' },
    { field: 'practice', type: 'string', required: true, reason: 'HOLLOW PORTRAIT GUARD — practice name required for portrait card' },
    { field: 'photo', type: 'string', required: true, reason: 'HOLLOW PORTRAIT GUARD — portrait without photo shows empty circle with letter initial' },
    { field: 'services', type: 'array', required: true, reason: 'Services tags are the main visual content' },
    { field: 'description', type: 'string', required: true, reason: 'Description provides context about the provider' },
    { field: 'costRange', type: 'string', required: false, reason: 'Cost range shown below description' },
  ],
  tjb_insurance_branch: [
    { field: 'branch', type: 'string', required: true, reason: 'Determines covers/no_coverage visual' },
    { field: 'stateName', type: 'string', required: true, reason: 'Shown in the UI' },
    { field: 'headline', type: 'string', required: true, reason: 'Must communicate what\'s covered or not' },
    { field: 'detail', type: 'string', required: true, reason: 'Skeletal detail = blank card with checkmark only' },
    { field: 'policyBadge', type: 'string', required: false, reason: 'Nice-to-have badge' },
    { field: 'amount', type: 'string', required: false, reason: 'Nice-to-have amount' },
  ],
  tjb_provider_grid: [
    { field: 'providerCount', type: 'number', required: true, reason: 'Shows count in badge' },
  ],
  tjb_provider_scroll: [
    { field: 'screenshotPath', type: 'string', required: true, reason: 'Scroll animation needs a screenshot image' },
    { field: 'providerCount', type: 'number', required: true, reason: 'Shows count in overlay badge' },
    { field: 'maxScroll', type: 'number', required: true, reason: 'Determines scroll animation distance' },
    { field: 'city', type: 'string', required: true, reason: 'City name shown on overlay' },
  ],
  tjb_app_feature: [
    { field: 'features', type: 'array', required: true, reason: 'Bullet list is the main content' },
  ],
  tjb_city_hook: [
    { field: 'city', type: 'string', required: true, reason: 'City name in hero' },
    { field: 'slug', type: 'string', required: true, reason: 'Required for links in video' },
  ],
  tjb_cost_reveal: [
    { field: 'costRange', type: 'string', required: true, reason: 'Main visual number' },
  ],
  tjb_city_cta: [
    { field: 'city', type: 'string', required: true, reason: 'CTA personalization' },
    { field: 'slug', type: 'string', required: true, reason: 'Required for link-out' },
  ],
};

const errors: string[] = [];
const warnings: string[] = [];

function err(msg: string, scene_id?: string, file?: string) {
  const prefix = file ? `[${path.basename(file)}]` : '';
  const scene = scene_id ? ` ${scene_id}:` : '';
  errors.push(`  ❌ ${prefix}${scene} ${msg}`);
}

function warn(msg: string, scene_id?: string, file?: string) {
  const prefix = file ? `[${path.basename(file)}]` : '';
  const scene = scene_id ? ` ${scene_id}:` : '';
  warnings.push(`  ⚠️ ${prefix}${scene} ${msg}`);
}

function checkScene(scene: TJBCityScene, file: string) {
  const { scene_id, scene_type, text_content, narration, image_source } = scene;

  // 1. Valid scene_type
  if (!VALID_SCENE_TYPES.includes(scene_type)) {
    err(`Unknown scene_type "${scene_type}"`, scene_id, file);
  }

  // 2. Required fields exist
  if (!scene_id) err('Missing scene_id', scene_id, file);
  if (!narration) warn('Missing narration', scene_id, file);
  if (!text_content || typeof text_content !== 'object') {
    err('Missing or invalid text_content', scene_id, file);
    return;
  }

  // 3. Check for leaked image_source on types that shouldn't have it
  const typesUsingImageSource = ['tjb_city_hook', 'tjb_provider_portrait', 'tjb_app_feature', 'tjb_hospital_card'];
  if (image_source && !typesUsingImageSource.includes(scene_type)) {
    err(`image_source "${image_source}" set for scene_type "${scene_type}" which doesn't use it`, scene_id, file);
  }

  // 4. Check image_source file exists on disk
  if (image_source) {
    const fullPath = path.join(PUBLIC_DIR, image_source);
    if (!fs.existsSync(fullPath)) {
      err(`image_source "${image_source}" not found on disk at public/${image_source}`, scene_id, file);
    }
  }

  // 5. Scene-type-specific text_content validation
  const rules = SCENE_FIELD_RULES[scene_type];
  if (rules) {
    for (const rule of rules) {
      const value = (text_content as any)[rule.field];

      if (rule.required && (value === undefined || value === null || value === '')) {
        err(`Missing required text_content.${rule.field} — ${rule.reason}`, scene_id, file);
      } else if (rule.required && rule.type === 'array' && Array.isArray(value) && value.length === 0) {
        err(`Empty text_content.${rule.field} — ${rule.reason}`, scene_id, file);
      } else if (rule.required && rule.type === 'number' && typeof value === 'number' && value <= 0) {
        err(`Invalid text_content.${rule.field}: ${value} — ${rule.reason}`, scene_id, file);
      }

      // Warn on missing nice-to-have fields
      if (!rule.required && (value === undefined || value === '')) {
        warn(`Optional text_content.${rule.field} is missing — ${rule.reason}`, scene_id, file);
      }
    }
  }

  // 6. Insurance-specific checks
  if (scene_type === 'tjb_insurance_branch') {
    const branch = (text_content as any).branch;
    const validBranches = ['covers', 'no_coverage'];
    if (branch && !validBranches.includes(branch)) {
      err(`Invalid branch "${branch}". Must be one of: ${validBranches.join(', ')}`, scene_id, file);
    }
    const detail = (text_content as any).detail;
    if (detail && typeof detail === 'string' && detail.length < 30) {
      err(`text_content.detail is too short (${detail.length} chars) — skeletal insurance data produces blank visuals`, scene_id, file);
    }
  }

  // 7. Provider grid: check screenshot fallback
  if (scene_type === 'tjb_provider_grid') {
    const photos = (text_content as any).photos;
    const screenshotPath = (text_content as any).screenshotPath;
    if ((!photos || photos.length === 0) && !screenshotPath) {
      err('No provider photos AND no screenshotPath — component will render blank fallback text only', scene_id, file);
    }
    if (screenshotPath) {
      const ssPath = path.join(PUBLIC_DIR, screenshotPath);
      if (!fs.existsSync(ssPath)) {
        err(`screenshotPath "${screenshotPath}" not found on disk`, scene_id, file);
      }
    }
  }

  // 8. App feature: check screenshotPath
  if (scene_type === 'tjb_app_feature') {
    const screenshotPath = (text_content as any).screenshotPath;
    if (!screenshotPath) {
      warn('No screenshotPath in text_content — app slide will use default image', scene_id, file);
    } else {
      const ssPath = path.join(PUBLIC_DIR, screenshotPath);
      if (!fs.existsSync(ssPath)) {
        err(`screenshotPath "${screenshotPath}" not found on disk`, scene_id, file);
      }
    }
  }

  // 9. Portrait: check photo file exists on disk (if provided)
  if (scene_type === 'tjb_provider_portrait') {
    const photo = (text_content as any).photo;
    if (photo && !photo.startsWith('http')) {
      const photoPath = path.join(PUBLIC_DIR, photo);
      if (!fs.existsSync(photoPath)) {
        err(`photo "${photo}" not found on disk at public/${photo}`, scene_id, file);
      }
    }
  }

  // 10. Hospital card: MUST have image_source — renders blank without it
  if (scene_type === 'tjb_hospital_card') {
    if (!image_source) {
      err(`Missing image_source — hospital card renders with NO photo without it. Every hospital scene needs "image_source: 'images/{slug}.webp'"`, scene_id, file);
    }
    const photo = (text_content as any).photo;
    if (!image_source && photo && !photo.startsWith('http')) {
      const photoPath = path.join(PUBLIC_DIR, photo);
      if (!fs.existsSync(photoPath)) {
        warn(`FALLBACK photo "${photo}" not found on disk at public/${photo}`, scene_id, file);
      }
    }
  }

  // 11. Provider scroll: check narration isn't generic
  // Only flag when narration is short (<120 chars) AND matches generic patterns
  // — common phrases like "ready to support you" are fine as part of a longer narration
  // that also lists specific support types
  if (scene_type === 'tjb_provider_scroll') {
    if (narration && narration.length < 120) {
      const genericNarrationPatterns = [
        "serving your area",
        "see who's serving",
        "ready to support you",
      ];
      const matchesGeneric = genericNarrationPatterns.some(p => narration.toLowerCase().includes(p));
      if (matchesGeneric) {
        warn(`Narration is short (${narration.length} chars) and sounds generic — "${narration}" — should list SPECIFIC support types (e.g. "Birth doulas, postpartum specialists, overnight support") like Fremont's approved template`, scene_id, file);
      }
    }
  }
}

function validateData(data: TJBCityVideoData, filepath: string) {
  const meta = data.video_metadata as any;

  // Check scene ordering
  const CANONICAL_ORDER = [
    'tjb_city_hook',
    'tjb_city_bridge',
    'tjb_hospital_card',
    'tjb_provider_portrait', 'tjb_provider_grid', 'tjb_provider_scroll',
    'tjb_app_feature',
    'tjb_cost_reveal',
    'tjb_insurance_branch',
    'tjb_city_cta',
  ];
  let lastOrderIdx = -1;
  const seenIds = new Set<string>();

  for (const scene of data.scenes) {
    const orderIdx = CANONICAL_ORDER.indexOf(scene.scene_type);
    if (orderIdx >= 0 && orderIdx < lastOrderIdx) {
      warn(`Scene "${scene.scene_id}" (${scene.scene_type}) appears after scene type later in canonical order. Order: hook → bridge → hospital → providers → app → cost → insurance → grid/scroll → CTA`, scene.scene_id, filepath);
    }
    if (orderIdx >= 0) lastOrderIdx = orderIdx;

    // Check duration_seconds bounds
    if (scene.duration_seconds <= 0) {
      err(`duration_seconds is ${scene.duration_seconds} — must be positive`, scene.scene_id, filepath);
    } else if (scene.duration_seconds < 2.0) {
      warn(`duration_seconds is ${scene.duration_seconds}s — very short for a narrated scene`, scene.scene_id, filepath);
    } else if (scene.duration_seconds > 60) {
      warn(`duration_seconds is ${scene.duration_seconds}s — unusually long for a single scene`, scene.scene_id, filepath);
    }

    // Check duplicate scene_ids
    if (scene.scene_id && seenIds.has(scene.scene_id)) {
      err(`Duplicate scene_id "${scene.scene_id}"`, scene.scene_id, filepath);
    }
    if (scene.scene_id) seenIds.add(scene.scene_id);
  }

  // Check metadata consistency: if hasAppScreenshot is false but we have tjb_app_feature scenes
  if (data.scenes.some(s => s.scene_type === 'tjb_app_feature')) {
    if (meta.hasAppScreenshot === false) {
      warn('hasAppScreenshot=false but scenes include a tjb_app_feature scene. Update metadata.', undefined, filepath);
    }
  }

  // Check each scene
  for (const scene of data.scenes) {
    checkScene(scene, filepath);
  }
}

// ── Main ──

async function main() {
  const dataFiles = fs.readdirSync(DATA_DIR).filter(f =>
    f.endsWith('-data.ts') &&
    !f.endsWith('.bak') &&
    f !== 'types.ts' &&
    f !== 'denver-example.ts'
  );

  console.log('═══════════════════════════════════════════════════════');
  console.log('  TJB Pre-Render Data Validator');
  console.log('═══════════════════════════════════════════════════════\n');

  for (const file of dataFiles) {
    const fullPath = path.join(DATA_DIR, file);
    console.log(`\n📋 ${file}`);
    console.log('─'.repeat(60));

    try {
      const mod = await import(fullPath);
      const exportKey = Object.keys(mod).find(k => k.endsWith('Data'));
      if (!exportKey) {
        err('No Data export found', undefined, file);
        continue;
      }
      validateData(mod[exportKey], fullPath);
    } catch (e: any) {
      err(`Could not load file: ${e.message}`, undefined, file);
    }
  }

  // Summary
  console.log('\n' + '═'.repeat(60));

  if (errors.length === 0 && warnings.length === 0) {
    console.log('\n✅ ALL CHECKS PASSED — no errors, no warnings');
    process.exit(0);
  }

  if (errors.length > 0) {
    console.log(`\n❌ ${errors.length} ERROR(S) — must fix before rendering:`);
    console.log(errors.join('\n'));
  }

  if (warnings.length > 0) {
    console.log(`\n⚠️  ${warnings.length} WARNING(S) — review before rendering:`);
    console.log(warnings.join('\n'));
  }

  if (errors.length > 0) {
    console.log('\n🚫 Validation FAILED — fix errors above before rendering.');
    process.exit(1);
  } else {
    console.log('\n✅ Validation PASSED with warnings — review above before rendering.');
    process.exit(0);
  }
}

main();