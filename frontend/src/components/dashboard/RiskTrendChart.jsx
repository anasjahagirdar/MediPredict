import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';


function RiskTrendChart({ scanData = [], error }) {
  const chartData = [...scanData]
    .slice(0, 5)
    .reverse()
    .map((scan) => ({
      x: scan.date || `Scan ${scan.scan_number}`,
      bp_systolic: Number(scan.bp_systolic) || 0,
      bmi: Number(scan.bmi) || 0,
    }));

  return (
    <section className="dashboard-card chart-card">
      <div className="dashboard-card__header">
        <h3>Vitals Trend (Last 5 Scans)</h3>
      </div>

      {error ? (
        <div className="panel-error-card">{error}</div>
      ) : chartData.length === 0 ? (
        <div className="panel-empty-card">
          No scan history yet. Run your first analysis to see your vitals trend here.
        </div>
      ) : (
        <div className="chart-card__body">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="bp_systolic"
                name="Systolic BP"
                stroke="#e11d48"
                strokeWidth={3}
              />
              <Line
                type="monotone"
                dataKey="bmi"
                name="BMI"
                stroke="#2563eb"
                strokeWidth={3}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}


export default RiskTrendChart;
