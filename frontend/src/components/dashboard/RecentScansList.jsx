import { X } from 'lucide-react';
import { useState } from 'react';


function getSymptoms(scan) {
  const symptomMap = [
    ['symptom_fever', 'Fever'],
    ['symptom_cough', 'Cough'],
    ['symptom_fatigue', 'Fatigue'],
    ['symptom_headache', 'Headache'],
    ['symptom_chest_pain', 'Chest Pain'],
    ['symptom_breathlessness', 'Breathlessness'],
    ['symptom_sweating', 'Sweating'],
    ['symptom_nausea', 'Nausea'],
  ];

  return symptomMap
    .filter(([key]) => Number(scan[key]) === 1)
    .map(([, label]) => label);
}


function RecentScansList({ scans, error }) {
  const [selectedScan, setSelectedScan] = useState(null);
  const recentScans = scans.slice(0, 5);

  return (
    <>
      <section className="dashboard-card recent-scans-card">
        <div className="dashboard-card__header">
          <h3>Recent Scan Reports</h3>
        </div>

        {error ? (
          <div className="panel-error-card">{error}</div>
        ) : recentScans.length === 0 ? (
          <div className="panel-empty-card">No scans yet</div>
        ) : (
          <div className="recent-scans-list">
            {recentScans.map((scan) => (
              <button
                className="recent-scans-list__item"
                key={scan.id}
                type="button"
                onClick={() => setSelectedScan(scan)}
              >
                <span className={`recent-scans-list__dot recent-scans-list__dot--${scan.risk_level.toLowerCase()}`} />
                <div className="recent-scans-list__content">
                  <strong>{scan.predicted_disease || scan.diagnosis}</strong>
                  <span>{scan.date}</span>
                </div>
                <span className="recent-scans-list__badge">{scan.confidence}%</span>
              </button>
            ))}
          </div>
        )}
      </section>

      {selectedScan && (
        <div className="scan-modal-backdrop" role="presentation" onClick={() => setSelectedScan(null)}>
          <div className="scan-modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
            <div className="scan-modal__header">
              <div>
                <h3>{selectedScan.predicted_disease || selectedScan.diagnosis}</h3>
                <p>{selectedScan.date} | {selectedScan.risk_level} risk</p>
              </div>
              <button type="button" onClick={() => setSelectedScan(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="scan-modal__grid">
              <div>
                <span>Blood Pressure</span>
                <strong>{selectedScan.bp_systolic}/{selectedScan.bp_diastolic}</strong>
              </div>
              <div>
                <span>Blood Sugar</span>
                <strong>{selectedScan.sugar_level}</strong>
              </div>
              <div>
                <span>Heart Rate</span>
                <strong>{selectedScan.heart_rate}</strong>
              </div>
              <div>
                <span>BMI</span>
                <strong>{selectedScan.bmi}</strong>
              </div>
              <div>
                <span>Confidence</span>
                <strong>{selectedScan.confidence}%</strong>
              </div>
              <div>
                <span>Gender</span>
                <strong>{Number(selectedScan.gender) === 1 ? 'Male' : 'Female'}</strong>
              </div>
            </div>

            <div className="scan-modal__section">
              <span>Symptoms</span>
              <div className="scan-modal__chips">
                {getSymptoms(selectedScan).length > 0 ? (
                  getSymptoms(selectedScan).map((item) => <span key={item}>{item}</span>)
                ) : (
                  <span>None recorded</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}


export default RecentScansList;
