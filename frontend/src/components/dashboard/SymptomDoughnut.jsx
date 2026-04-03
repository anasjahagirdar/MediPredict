import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

const PIE_COLORS = ['#E8C547', '#1E1E2E', '#F59E0B', '#22C55E', '#EF4444'];

function SymptomDoughnut({ data, error }) {
  const sortedData = [...data].sort((a, b) => b.count - a.count).slice(0, 5);
  const total = sortedData.reduce((sum, item) => sum + item.count, 0);

  return (
    <section className="dashboard-card chart-card chart-card--compact">
      <div className="dashboard-card__header">
        <h3>Symptom Frequency - All Scans</h3>
      </div>

      {error ? (
        <div className="panel-error-card">{error}</div>
      ) : total === 0 ? (
        <div className="panel-empty-card">No symptoms recorded yet</div>
      ) : (
        <>
          <div className="chart-card__body chart-card__body--compact">
            <ResponsiveContainer width="100%" height={230}>
              <PieChart>
                <Pie
                  data={sortedData}
                  dataKey="count"
                  nameKey="name"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                  cy="45%"
                >
                  {sortedData.map((item, index) => (
                    <Cell key={item.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend
                  verticalAlign="bottom"
                  iconSize={10}
                  wrapperStyle={{
                    paddingTop: '20px',
                    fontSize: '12px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="symptom-legend" style={{ marginTop: '15px' }}>
            {sortedData.map((item, index) => (
              <div className="symptom-legend__item" key={item.name}>
                <span className={`symptom-legend__swatch symptom-legend__swatch--${index % PIE_COLORS.length}`} />
                <span>{item.name}</span>
                <strong>{item.count}</strong>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

export default SymptomDoughnut;