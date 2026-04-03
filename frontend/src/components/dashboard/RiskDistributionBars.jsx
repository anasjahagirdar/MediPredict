function RiskDistributionBars({ scans, error }) {
  const highCount = scans.filter((item) => item.risk_level === 'High').length;
  const mediumCount = scans.filter((item) => item.risk_level === 'Medium').length;
  const lowCount = scans.filter((item) => item.risk_level === 'Low').length;
  const total = scans.length || 1;

  const rows = [
    {
      label: 'High',
      count: highCount,
      percent: Math.round((highCount / total) * 100),
      tone: 'high',
    },
    {
      label: 'Medium',
      count: mediumCount,
      percent: Math.round((mediumCount / total) * 100),
      tone: 'medium',
    },
    {
      label: 'Low',
      count: lowCount,
      percent: Math.round((lowCount / total) * 100),
      tone: 'low',
    },
  ];

  return (
    <section className="dashboard-card distribution-card">
      <div className="dashboard-card__header">
        <h3>Risk Distribution</h3>
      </div>

      {error ? (
        <div className="panel-error-card">{error}</div>
      ) : (
        <div className="distribution-card__rows">
          {rows.map((row) => (
            <div key={row.label} className="distribution-card__row">
              <div className="distribution-card__meta">
                <span>{row.label}</span>
                <strong>{row.count} ({row.percent}%)</strong>
              </div>
              <progress
                className={`distribution-card__progress distribution-card__progress--${row.tone}`}
                value={row.percent}
                max="100"
              />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}


export default RiskDistributionBars;
