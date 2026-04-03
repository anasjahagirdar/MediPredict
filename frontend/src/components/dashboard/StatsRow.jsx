import { AlertTriangle, Calendar, ClipboardList } from 'lucide-react';


function getDayMonthLabel(currentDate) {
  if (!currentDate) {
    return '--';
  }

  const parts = currentDate.split(',');
  if (parts.length < 2) {
    return currentDate;
  }

  return parts[1].trim().replace(', 2026', '');
}


function StatsRow({ summary }) {
  return (
    <section className="stats-row">
      <article className="dashboard-card stats-row__card">
        <div className="stats-row__icon"><Calendar size={18} /></div>
        <p className="stats-row__number">{getDayMonthLabel(summary?.current_date)}</p>
        <p className="stats-row__label">CURRENT DATE</p>
        <p className="stats-row__subtext">{summary?.current_date || '--'}</p>
      </article>

      <article className="dashboard-card stats-row__card">
        <div className="stats-row__icon"><ClipboardList size={18} /></div>
        <p className="stats-row__number">{summary?.total_scans ?? 0}</p>
        <p className="stats-row__label">PREDICTION HISTORY</p>
        <p className="stats-row__subtext">Total AI scans run</p>
      </article>

      <article className="dashboard-card stats-row__card">
        <div className="stats-row__icon"><AlertTriangle size={18} /></div>
        <p className={`stats-row__number ${(summary?.high_risk_count ?? 0) > 0 ? 'is-risk' : 'is-safe'}`}>
          {summary?.high_risk_count ?? 0}
        </p>
        <p className="stats-row__label">SEVERE ALERTS</p>
        <p className="stats-row__subtext">High risk diagnoses</p>
      </article>
    </section>
  );
}


export default StatsRow;
