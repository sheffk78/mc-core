import { getBrandColor } from "@/lib/brands";
import { Hexagon, Mail, LayoutList, Activity, CheckSquare, CalendarDays, Timer, Settings, MessageCircle } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

const NAV_ITEMS = [
  { key: "overview", label: "Overview", Icon: Hexagon },
  { key: "chat", label: "Chat", Icon: MessageCircle },
  { key: "tasks", label: "Tasks", Icon: CheckSquare, badgeKey: "open_tasks" },
  { key: "inboxes", label: "Inboxes", Icon: LayoutList },
  { key: "schedule", label: "Schedule", Icon: Timer },
  { key: "calendar", label: "Calendar", Icon: CalendarDays },
  { key: "activity", label: "Activity", Icon: Activity },
  { key: "settings", label: "Settings", Icon: Settings },
];

export default function Sidebar({ brands, activeBrand, onBrandChange, activeView, onViewChange, stats, wsConnected }) {
  const filteredBrands = brands.filter(b => b.slug !== "all");

  return (
    <aside className="mc-sidebar" data-testid="sidebar">
      <div className="mc-sidebar-top">
        <div className="mc-wordmark" data-testid="wordmark">
          Mission <em>Control</em>
        </div>
        <div className="mc-version">v1.0 — OpenClaw</div>
      </div>

      <ScrollArea className="flex-1">
        <div className="mc-sidebar-section">
          <div className="mc-sidebar-label">Brands</div>
          <div
            className={`mc-brand-item ${activeBrand === "all" ? "active" : ""}`}
            onClick={() => onBrandChange("all")}
            data-testid="brand-all"
          >
            <span className="mc-brand-dot" style={{ background: "#8a8480" }} />
            <span>All Brands</span>
          </div>
          {filteredBrands.map(b => (
            <div
              key={b.slug}
              className={`mc-brand-item ${activeBrand === b.slug ? "active" : ""}`}
              onClick={() => onBrandChange(b.slug)}
              data-testid={`brand-${b.slug}`}
            >
              <span className="mc-brand-dot" style={{ background: getBrandColor(b.slug) }} />
              <span>{b.name}</span>
            </div>
          ))}
        </div>

        <div className="mc-sidebar-section">
          <div className="mc-sidebar-label">Views</div>
          {NAV_ITEMS.map(item => {
            const badge = item.badgeKey && stats ? stats[item.badgeKey] : null;
            return (
              <div
                key={item.key}
                className={`mc-nav-item ${activeView === item.key ? "active" : ""}`}
                onClick={() => onViewChange(item.key)}
                data-testid={`nav-${item.key}`}
              >
                <span className="mc-nav-icon">
                  <item.Icon size={14} />
                </span>
                <span>{item.label}</span>
                {badge > 0 && <span className="mc-nav-badge">{badge}</span>}
              </div>
            );
          })}
        </div>
      </ScrollArea>

      <div className="mc-sidebar-footer" data-testid="sidebar-footer">
        <span
          className="mc-status-dot"
          style={{ background: wsConnected ? "var(--mc-green)" : "var(--mc-amber)" }}
          data-testid="ws-status-dot"
        />
        <span>{wsConnected ? "Connected" : "Reconnecting..."}</span>
      </div>
    </aside>
  );
}
