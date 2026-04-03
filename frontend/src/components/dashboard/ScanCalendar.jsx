import { useMemo, useState } from 'react';


const RISK_CLASS = {
  High: 'is-high',
  Medium: 'is-medium',
  Low: 'is-low',
};


function buildMonthGrid(scans) {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const totalCells = Math.ceil((startOffset + lastDay.getDate()) / 7) * 7;
  const map = new Map();

  scans.forEach((scan) => {
    const date = new Date(scan.created_at || scan.date);
    if (date.getFullYear() === year && date.getMonth() === month) {
      map.set(date.getDate(), scan);
    }
  });

  return Array.from({ length: totalCells }, (_, index) => {
    const dayNumber = index - startOffset + 1;
    if (dayNumber < 1 || dayNumber > lastDay.getDate()) {
      return null;
    }

    return {
      dayNumber,
      scan: map.get(dayNumber) || null,
    };
  });
}


function ScanCalendar({ scans, error }) {
  const [selectedDay, setSelectedDay] = useState(null);
  const grid = useMemo(() => buildMonthGrid(scans), [scans]);
  const now = new Date();

  return (
    <section className="dashboard-card calendar-card">
      <div className="dashboard-card__header">
        <h3>Scan History Timeline</h3>
        <span>{now.toLocaleString('en-US', { month: 'long', year: 'numeric' })}</span>
      </div>

      {error ? (
        <div className="panel-error-card">{error}</div>
      ) : (
        <>
          <div className="calendar-grid calendar-grid--header">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
              <span key={day}>{day}</span>
            ))}
          </div>

          <div className="calendar-grid">
            {grid.map((cell, index) => {
              if (!cell) {
                return <div key={`empty-${index}`} className="calendar-cell calendar-cell--empty" />;
              }

              return (
                <button
                  key={cell.dayNumber}
                  type="button"
                  className={`calendar-cell ${selectedDay === cell.dayNumber ? 'is-selected' : ''}`}
                  onClick={() => setSelectedDay(cell.dayNumber === selectedDay ? null : cell.dayNumber)}
                >
                  <span>{cell.dayNumber}</span>
                  {cell.scan && <span className={`calendar-dot ${RISK_CLASS[cell.scan.risk_level]}`} />}
                  {cell.scan && selectedDay === cell.dayNumber && (
                    <div className="calendar-tooltip">
                      <strong>{cell.scan.predicted_disease || cell.scan.diagnosis}</strong>
                      <span>{cell.scan.risk_level} risk</span>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}


export default ScanCalendar;
