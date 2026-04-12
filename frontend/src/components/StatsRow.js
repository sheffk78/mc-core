export default function StatsRow({ stats }) {
  if (!stats) return null;

  const cards = [
    {
      label: "Pending Approvals",
      value: stats.pending_approvals,
      sub: stats.pending_approvals > 0
        ? <span className="warn">{stats.pending_approvals} awaiting review</span>
        : <span className="up">All clear</span>,
    },
    {
      label: "Open Tasks",
      value: stats.open_tasks,
      sub: stats.open_tasks > 5
        ? <span className="warn">Attention needed</span>
        : <span>On track</span>,
    },
    {
      label: "Pending Emails",
      value: stats.pending_emails,
      sub: <span>Across all inboxes</span>,
    },
  ];

  return (
    <div className="mc-stats-row" data-testid="stats-row">
      {cards.map((card, i) => (
        <div className="mc-stat-card" key={i} data-testid={`stat-card-${i}`}>
          <div className="mc-stat-label">{card.label}</div>
          <div className="mc-stat-value">{card.value}</div>
          <div className="mc-stat-sub">{card.sub}</div>
        </div>
      ))}
    </div>
  );
}
