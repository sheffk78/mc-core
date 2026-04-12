/**
 * Cron expression utilities.
 * Actual schedule calculation (next run times, weekly events) is done
 * server-side via GET /api/v1/schedule/weekly.
 */

const DOW_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function formatTime(h, m) {
  const hh = parseInt(h, 10);
  const mm = m === "0" ? "00" : String(m).padStart(2, "0");
  if (hh === 0) return `12:${mm} AM`;
  if (hh < 12) return `${hh}:${mm} AM`;
  if (hh === 12) return `12:${mm} PM`;
  return `${hh - 12}:${mm} PM`;
}

/**
 * Return a human-readable description of a 5-field cron expression.
 * e.g. "0 9 * * 1-5" → "Mon–Fri at 9:00 AM"
 */
export function describeCron(cron) {
  if (!cron) return "No schedule set";
  const parts = cron.trim().split(/\s+/);
  if (parts.length !== 5) return cron;
  const [min, hour, dom, , dow] = parts;

  // Monthly: 0 9 1 * *
  if (dom !== "*" && dow === "*" && hour !== "*" && min !== "*") {
    const suffix =
      dom === "1" ? "st" : dom === "2" ? "nd" : dom === "3" ? "rd" : "th";
    return `Monthly on ${dom}${suffix} at ${formatTime(hour, min)}`;
  }

  // Daily: 0 9 * * *
  if (dom === "*" && dow === "*" && hour !== "*" && min !== "*") {
    return `Daily at ${formatTime(hour, min)}`;
  }

  // Day-of-week pattern: e.g. 0 9 * * 1-5
  if (dow !== "*" && hour !== "*" && min !== "*") {
    let dayLabel;
    if (dow.includes("-")) {
      const [start, end] = dow.split("-").map(Number);
      if (start === 1 && end === 5) {
        dayLabel = "Mon\u2013Fri";
      } else {
        dayLabel = `${DOW_NAMES[start]}\u2013${DOW_NAMES[end]}`;
      }
    } else {
      dayLabel = dow
        .split(",")
        .map((d) => DOW_NAMES[parseInt(d, 10)] || d)
        .join(", ");
    }
    return `${dayLabel} at ${formatTime(hour, min)}`;
  }

  // Every hour at :MM
  if (hour === "*" && min !== "*" && !min.startsWith("*/")) {
    return `Every hour at :${String(min).padStart(2, "0")}`;
  }

  // Every N minutes
  if (min.startsWith("*/")) {
    const interval = min.split("/")[1];
    return `Every ${interval} minute${interval === "1" ? "" : "s"}`;
  }

  return cron;
}
