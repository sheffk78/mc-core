import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";
import Overview from "@/components/Overview";
import TasksList from "@/components/TasksList";
import InboxesList from "@/components/InboxesList";
import ActivityFeed from "@/components/ActivityFeed";
import CalendarView from "@/components/CalendarView";
import ScheduleView from "@/components/ScheduleView";
import SettingsView from "@/components/SettingsView";
import ChatView from "@/components/ChatView";
import { fetchBrands, fetchStats } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";

function App() {
  const [brands, setBrands] = useState([]);
  const [activeBrand, setActiveBrand] = useState("all");
  const [activeView, setActiveView] = useState("overview");
  const [stats, setStats] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const triggerRefresh = useCallback(() => {
    setRefreshKey(k => k + 1);
  }, []);

  // WebSocket real-time handler
  const handleWsEvent = useCallback((msg) => {
    const { type } = msg;
    if (
      type === "approval_new" ||
      type === "approval_updated" ||
      type === "action_item_new" ||
      type === "action_item_updated" ||
      type === "activity_log" ||
      type === "inbox_updated" ||
      type === "schedule_updated" ||
      type === "sync_state"
    ) {
      triggerRefresh();
    }
  }, [triggerRefresh]);

  const { connected } = useWebSocket(handleWsEvent);

  const loadBrands = useCallback(() => {
    fetchBrands().then(setBrands).catch(console.error);
  }, []);

  useEffect(() => {
    loadBrands();
  }, [loadBrands]);

  useEffect(() => {
    fetchStats(activeBrand).then(setStats).catch(console.error);
  }, [activeBrand, refreshKey]);

  const VIEW_NAMES = {
    overview: "Overview",
    chat: "Chat",
    tasks: "Tasks",
    inboxes: "Inboxes",
    schedule: "Schedule",
    calendar: "Calendar",
    activity: "Activity",
    settings: "Settings",
  };

  const renderView = () => {
    switch (activeView) {
      case "chat":
        return <ChatView />;
      case "tasks":
        return <TasksList brand={activeBrand} brands={brands} onAction={triggerRefresh} refreshKey={refreshKey} />;
      case "inboxes":
        return <InboxesList brand={activeBrand} brands={brands} refreshKey={refreshKey} />;
      case "schedule":
        return <ScheduleView brand={activeBrand} brands={brands} onAction={triggerRefresh} refreshKey={refreshKey} />;
      case "calendar":
        return <CalendarView />;
      case "activity":
        return <ActivityFeed brand={activeBrand} brands={brands} refreshKey={refreshKey} />;
      case "settings":
        return <SettingsView onBrandsChanged={loadBrands} />;
      default:
        return (
          <Overview
            brand={activeBrand}
            brands={brands}
            stats={stats}
            onAction={triggerRefresh}
            onNavigate={setActiveView}
            refreshKey={refreshKey}
          />
        );
    }
  };

  return (
    <BrowserRouter>
      <div className="mc-layout" data-testid="mc-layout">
        <Sidebar
          brands={brands}
          activeBrand={activeBrand}
          onBrandChange={setActiveBrand}
          activeView={activeView}
          onViewChange={setActiveView}
          stats={stats}
          wsConnected={connected}
        />
        <div className="mc-main">
          <Topbar
            brands={brands}
            activeBrand={activeBrand}
            viewName={VIEW_NAMES[activeView] || "Overview"}
            onAction={triggerRefresh}
            activeBrandSlug={activeBrand}
            onNavigate={setActiveView}
            wsConnected={connected}
          />
          <div className="mc-content">
            <Routes>
              <Route path="*" element={renderView()} />
            </Routes>
          </div>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
