import { useState, useEffect } from "react";
import { getBrandColor, getBrandName } from "@/lib/brands";
import { Plus, Send, RefreshCw } from "lucide-react";
import { syncAgentMail } from "@/lib/api";
import NewTaskDialog from "@/components/NewTaskDialog";
import ComposeDialog from "@/components/ComposeDialog";

export default function Topbar({ brands, activeBrand, viewName, onAction, onNavigate, wsConnected }) {
  const [time, setTime] = useState(new Date());
  const [showNewTask, setShowNewTask] = useState(false);
  const [showCompose, setShowCompose] = useState(false);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 30000);
    return () => clearInterval(timer);
  }, []);

  const brandName = activeBrand === "all" ? "All Brands" : getBrandName(activeBrand, brands);
  const brandColor = getBrandColor(activeBrand);

  const TZ = "America/Denver";
  const formatTime = (d) =>
    d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true, timeZone: TZ });

  const formatDate = (d) =>
    d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", timeZone: TZ });

  const handleSync = async () => {
    setSyncing(true);
    try {
      await syncAgentMail();
      if (onAction) onAction();
    } catch (e) {
      console.error(e);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="mc-topbar" data-testid="topbar">
      <div className="mc-topbar-left">
        <div className="mc-topbar-brand-tag" data-testid="topbar-brand">
          <span className="mc-brand-dot" style={{ background: brandColor }} />
          {brandName}
        </div>
        <span className="mc-topbar-sep" />
        <span className="mc-topbar-view">{viewName}</span>
      </div>
      <div className="mc-topbar-right">
        <span className="mc-topbar-time" data-testid="topbar-time">
          {formatTime(time)} — {formatDate(time)}
        </span>
        <span
          data-testid="ws-connection-badge"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "9.5px",
            fontWeight: 500,
            padding: "2px 8px",
            borderRadius: "10px",
            background: wsConnected ? "var(--mc-green-bg)" : "var(--mc-amber-bg)",
            color: wsConnected ? "var(--mc-green)" : "var(--mc-amber)",
          }}
        >
          <span style={{
            width: "5px", height: "5px", borderRadius: "50%",
            background: wsConnected ? "var(--mc-green)" : "var(--mc-amber)",
          }} />
          {wsConnected ? "Live" : "Offline"}
        </span>
        <button
          className="mc-btn mc-btn-outline mc-btn-sm"
          onClick={handleSync}
          disabled={syncing}
          data-testid="sync-btn"
          title="Sync AgentMail"
        >
          <RefreshCw size={11} style={syncing ? { animation: "spin 1s linear infinite" } : {}} />
          {syncing ? "Syncing..." : "Sync"}
        </button>
        <button
          className="mc-btn mc-btn-outline mc-btn-sm"
          onClick={() => setShowCompose(true)}
          data-testid="compose-btn"
        >
          <Send size={11} />
          Compose
        </button>
        <button
          className="mc-btn mc-btn-outline mc-btn-sm"
          onClick={() => setShowNewTask(true)}
          data-testid="new-task-btn"
        >
          <Plus size={12} />
          New Task
        </button>
      </div>
      <NewTaskDialog
        open={showNewTask}
        onOpenChange={setShowNewTask}
        brands={brands}
        defaultBrand={activeBrand !== "all" ? activeBrand : ""}
        onCreated={() => { onAction(); setShowNewTask(false); }}
      />
      <ComposeDialog
        open={showCompose}
        onOpenChange={setShowCompose}
        onSent={onAction}
      />
    </div>
  );
}
