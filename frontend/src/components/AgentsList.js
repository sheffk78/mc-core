import { useState, useEffect, useCallback } from "react";
import { fetchAgents } from "@/lib/api";
import { getBrandColor, getBrandName, timeAgo } from "@/lib/brands";

export default function AgentsList({ brand, brands, limit, embedded }) {
  const [agents, setAgents] = useState([]);

  const load = useCallback(() => {
    fetchAgents(brand).then(data => {
      setAgents(limit ? data.slice(0, limit) : data);
    }).catch(console.error);
  }, [brand, limit]);

  useEffect(() => { load(); }, [load]);

  if (agents.length === 0) {
    return <div className="mc-empty" data-testid="agents-empty">No agents found</div>;
  }

  return (
    <div data-testid="agents-list">
      {agents.map(agent => (
        <div key={agent.id} className="mc-agent-item" data-testid={`agent-item-${agent.id}`}>
          <div
            className="mc-agent-avatar"
            style={{ background: agent.avatar_color || getBrandColor(agent.brand) }}
            data-testid="agent-avatar"
          >
            {agent.initials || agent.name.slice(0, 2).toUpperCase()}
          </div>
          <div className="mc-agent-info">
            <div className="mc-agent-name">{agent.name}</div>
            <div className="mc-agent-desc">{agent.role}</div>
          </div>
          <div className="mc-agent-right">
            <span className={`mc-agent-status ${agent.status}`} data-testid="agent-status">
              {agent.status}
            </span>
            <span className="mc-agent-last">{timeAgo(agent.last_activity)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
