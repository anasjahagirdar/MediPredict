function getInitials(user) {
  const first = user?.first_name?.[0] || user?.username?.[0] || 'M';
  const last = user?.last_name?.[0] || user?.username?.[1] || 'P';
  return `${first}${last}`.toUpperCase();
}


function getProgressTone(type, value) {
  if (type === 'bmi') {
    if (value > 30) {
      return 'high';
    }
    if (value >= 25) {
      return 'medium';
    }
    return 'low';
  }

  if (value > 140) {
    return 'high';
  }
  if (value >= 100) {
    return 'medium';
  }
  return 'low';
}


function PatientProfileCard({ summary, user, onAnalyze }) {
  const bmiValue = summary?.latest_bmi || 0;
  const sugarValue = summary?.latest_sugar || 0;

  return (
    <section className="dashboard-card patient-profile-card">
      <div className="patient-profile-card__avatar">{getInitials(user)}</div>
      <h2>{summary?.patient_name || user?.username}</h2>
      <p className="patient-profile-card__username">@{user?.username}</p>

      <div className="dashboard-divider" />

      <p className="dashboard-section-label">Health Metrics</p>

      <div className="metric-progress">
        <div className="metric-progress__header">
          <span>Current BMI</span>
          <strong>{bmiValue ? bmiValue.toFixed(1) : '--'}</strong>
        </div>
        <progress
          className={`metric-progress__bar metric-progress__bar--${getProgressTone('bmi', bmiValue)}`}
          value={Math.min(Math.max(((bmiValue - 10) / 30) * 100, 0), 100)}
          max="100"
        />
      </div>

      <div className="metric-progress">
        <div className="metric-progress__header">
          <span>Blood Sugar</span>
          <strong>{sugarValue ? `${sugarValue.toFixed(1)}` : '--'}</strong>
        </div>
        <progress
          className={`metric-progress__bar metric-progress__bar--${getProgressTone('sugar', sugarValue)}`}
          value={Math.min(Math.max(((sugarValue - 50) / 250) * 100, 0), 100)}
          max="100"
        />
      </div>

      <div className="patient-profile-card__bp">
        <span>Latest BP</span>
        <strong>{summary?.latest_bp || '--'}</strong>
      </div>

      <button className="patient-profile-card__cta" type="button" onClick={onAnalyze}>
        Run New Analysis
      </button>
    </section>
  );
}


export default PatientProfileCard;
