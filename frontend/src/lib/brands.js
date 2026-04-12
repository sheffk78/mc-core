// Brand configuration — edit colors here to change everywhere
export const BRAND_COLORS = {
  'all': '#8a8480',
  'agentic-trust': '#c85a2a',
  'aav': '#2d6a4f',
  'safe-spend': '#2a5c8a',
  'arl': '#7c5cbf',
  'true-joy-birthing': '#c2756b',
  'trustoffice': '#5a8a6a',
  'wingpoint': '#b06a10',
  'anchorpoint': '#6a7c8a',
};

export function getBrandColor(slug) {
  return BRAND_COLORS[slug] || '#8a8480';
}

export function getBrandBg(slug) {
  const color = getBrandColor(slug);
  // Return a very light tint of the brand color
  return `${color}14`;
}

export function getBrandName(slug, brands) {
  if (!brands) return slug;
  const b = brands.find(br => br.slug === slug);
  return b ? b.name : slug;
}

export function timeAgo(isoString) {
  if (!isoString) return '';
  const now = new Date();
  const then = new Date(isoString);
  const diffMs = now - then;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return then.toLocaleDateString("en-US", { timeZone: "America/Denver" });
}

export function dueDateStatus(isoString) {
  if (!isoString) return { label: '', className: 'normal' };
  const now = new Date();
  const due = new Date(isoString);
  const diffMs = due - now;
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffDays < -7) return { label: `${Math.abs(diffDays)}d overdue`, className: 'overdue' };
  if (diffDays < 0) return { label: `${Math.abs(diffDays)}d overdue`, className: 'overdue' };
  if (diffDays === 0) return { label: 'Due today', className: 'soon' };
  if (diffDays <= 3) return { label: `Due in ${diffDays}d`, className: 'soon' };
  return { label: `Due in ${diffDays}d`, className: 'normal' };
}
