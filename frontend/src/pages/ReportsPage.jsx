import { Download } from 'lucide-react';
import { useEffect, useState } from 'react';

import Navbar from '../components/Navbar';
import { downloadReport, getScanHistory } from '../api/health';
import '../styles/AnalyzePage.css';


function getPageError(error) {
  if (!error?.response) {
    return 'Server unreachable. Check your connection.';
  }

  return error?.response?.data?.message || 'Request failed';
}


function ReportsPage() {
  const [scans, setScans] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    async function loadReports() {
      try {
        setIsLoading(true);
        const data = await getScanHistory();
        setScans(data.scans || []);
      } catch (requestError) {
        setError(getPageError(requestError));
      } finally {
        setIsLoading(false);
      }
    }

    loadReports();
  }, []);

  const handleDownload = async (recordId) => {
    try {
      setDownloadingId(recordId);
      await downloadReport(recordId);
    } catch (requestError) {
      setError(getPageError(requestError));
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="analyze-page">
      <Navbar />
      <div className="analyze-page__container">
        <div className="analyze-card">
          <header className="analyze-card__header">
            <p className="analyze-card__eyebrow">Records Workspace</p>
            <h1>Medical Reports &amp; History</h1>
          </header>

          <section className="dashboard-card">
            {error && <div className="panel-error-card">{error}</div>}

            {isLoading ? (
              <p>Loading reports...</p>
            ) : scans.length === 0 ? (
              <p>Report generation and historical PDF exports feature coming soon.</p>
            ) : (
              <div className="reports-table-wrapper">
                <table className="reports-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Diagnosis</th>
                      <th>Risk Level</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scans.map((scan) => (
                      <tr key={scan.id}>
                        <td>{scan.date}</td>
                        <td>{scan.predicted_disease || scan.diagnosis}</td>
                        <td>{scan.risk_level}</td>
                        <td>
                          <button
                            type="button"
                            className="analyze-button analyze-button--secondary"
                            onClick={() => handleDownload(scan.id)}
                            disabled={downloadingId === scan.id}
                          >
                            <Download size={16} />
                            {downloadingId === scan.id ? 'Downloading...' : 'Download PDF'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}


export default ReportsPage;
