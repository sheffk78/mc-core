import { useState, useEffect, useCallback } from "react";
import { fetchActivity } from "@/lib/api";
import { getBrandColor, getBrandName, timeAgo } from "@/lib/brands";
import { Check, X, ClipboardList, Settings, AlertTriangle, Mail, Send } from "lucide-react";

const TYPE_CONFIG = {
  approval: { Icon: Check, className: "approval" },
  task: { Icon: ClipboardList, className: "task" },
  system: { Icon: Settings, className: "system" },
  error: { Icon: AlertTriangle, className: "error" },
  email_in: { Icon: Mail, className: "approval" },
  email_out: { Icon: Send, className: "task" },
};

export default function ActivityFeed({ brand, brands, limit, embedded, refreshKey }) {
  const [entries, setEntries] = useState([]);

  const load = useCallback(() => {
    fetchActivity(brand, limit || 20).then(setEntries).catch(console.error);
  }, [brand, limit]);

  useEffect(() => { load(); }, [load, refreshKey]);

  if (entries.length === 0) {
    return <div className="mc-empty" data-testid="activity-empty">No activity yet</div>;
  }

  return (
    <div data-testid="activity-feed">
      {entries.map(entry => {
        const config = TYPE_CONFIG[entry.type] || TYPE_CONFIG.system;
        return (
          <div key={entry.id} className="mc-activity-item" data-testid={`activity-item-${entry.id}`}>
            <div className={`mc-activity-icon ${config.className}`}>
              <config.Icon size={13} />
            </div>
            <div className="mc-activity-body">
              <div className="mc-activity-text">
                <strong>{entry.text}</strong>
              </div>
              {entry.detail && (
                <div className="mc-activity-detail">{entry.detail}</div>
              )}
            </div>
            <span className="mc-activity-time">{timeAgo(entry.time)}</span>
          </div>
        );
      })}
    </div>
  );
}
