import { db } from "../db";
import { brands } from "../schema";

const SLUG_REGEX = /^[a-z0-9]+$/;

const BRANDS = [
  { name: "TrustOffice", slug: "trustoffice", color: "#c85a2a", sort_order: 1 },
  { name: "WingPoint", slug: "wingpoint", color: "#6b7c4a", sort_order: 2 },
  { name: "AgenticTrust", slug: "agentictrust", color: "#3d5a7a", sort_order: 3 },
  { name: "True Joy Birthing", slug: "truejoybirthing", color: "#a0522d", sort_order: 4 },
];

// Validate slug constraints before insert
for (const brand of BRANDS) {
  if (!SLUG_REGEX.test(brand.slug)) {
    throw new Error(
      `Invalid slug "${brand.slug}" — must match /^[a-z0-9]+$/. ` +
        `Re-run after fixing brand data.`
    );
  }
}

// Insert brands with conflict-ignore (idempotent)
db.insert(brands).values(BRANDS).onConflictDoNothing().run();

console.log("Seed complete");
