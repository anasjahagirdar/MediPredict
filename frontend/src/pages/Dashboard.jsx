import { HeartPulse } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import Navbar from '../components/Navbar';
import PatientProfileCard from '../components/dashboard/PatientProfileCard';
import RecentScansList from '../components/dashboard/RecentScansList';
import RiskDistributionBars from '../components/dashboard/RiskDistributionBars';
import RiskTrendChart from '../components/dashboard/RiskTrendChart';
import ScanCalendar from '../components/dashboard/ScanCalendar';
import StatsRow from '../components/dashboard/StatsRow';
import SymptomDoughnut from '../components/dashboard/SymptomDoughnut';
import { getDashboardSummary, getScanHistory, getSymptomFrequency } from '../api/health';
import { useAuth } from '../context/AuthContext';

const DEFAULT_SUMMARY = {
  patient_name: '',
  total_scans: 0,
  high_risk_count: 0,
  latest_bmi: 0,
  latest_sugar: 0,
  latest_bp: '--',
  current_date: '--',
};


function getPanelError(error) {
  if (!error?.response) {
    return 'Server unreachable. Check your connection.';
  }

  return error?.response?.data?.message || 'Request failed';
}


function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [summary, setSummary] = useState(DEFAULT_SUMMARY);
  const [symptomData, setSymptomData] = useState([]);
  const [scanHistory, setScanHistory] = useState([]);
  const [errors, setErrors] = useState({
    summary: '',
    symptoms: '',
    scans: '',
  });

  useEffect(() => {
    async function loadDashboard() {
      setIsLoading(true);
      setErrors({
        summary: '',
        symptoms: '',
        scans: '',
      });

      const results = await Promise.allSettled([
        getDashboardSummary(),
        getSymptomFrequency(),
        getScanHistory(),
      ]);

      const [summaryResult, symptomResult, scanResult] = results;

      if (summaryResult.status === 'fulfilled') {
        setSummary(summaryResult.value || DEFAULT_SUMMARY);
      } else {
        setErrors((current) => ({
          ...current,
          summary: getPanelError(summaryResult.reason),
        }));
      }

      if (symptomResult.status === 'fulfilled') {
        setSymptomData(symptomResult.value.symptoms || []);
      } else {
        setErrors((current) => ({
          ...current,
          symptoms: getPanelError(symptomResult.reason),
        }));
      }

      if (scanResult.status === 'fulfilled') {
        setScanHistory(scanResult.value.scans || []);
      } else {
        setErrors((current) => ({
          ...current,
          scans: getPanelError(scanResult.reason),
        }));
      }

      setIsLoading(false);
    }

    loadDashboard();
  }, []);

  if (isLoading && !summary.total_scans && scanHistory.length === 0 && symptomData.length === 0) {
    return (
      <div className="dashboard-page">
        <Navbar />
        <div className="dashboard-loading">
          <div className="dashboard-skeleton dashboard-skeleton--left" />
          <div className="dashboard-skeleton dashboard-skeleton--center" />
          <div className="dashboard-skeleton dashboard-skeleton--right" />
        </div>
      </div>
    );
  }

  if (summary.total_scans === 0 && scanHistory.length === 0) {
    return (
      <div className="dashboard-page">
        <Navbar />
        <div className="dashboard-empty-state">
          <div className="dashboard-empty-state__icon">
            <HeartPulse size={36} />
          </div>
          <h1>Welcome to your health history workspace</h1>
          <p>
            No scans have been recorded yet. Run your first analysis to populate
            your dashboard, charts, and symptom history.
          </p>
          <button type="button" onClick={() => navigate('/analyze')}>
            Run First Analysis
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <Navbar />
      <main className="dashboard-layout">
        <div className="dashboard-layout__left">
          <PatientProfileCard summary={summary} user={user} onAnalyze={() => navigate('/analyze')} />
        </div>

        <div className="dashboard-layout__center">
          <section className="dashboard-welcome-card">
            <h1>Welcome back, {summary?.patient_name || user?.first_name || user?.username}</h1>
            <p>
              Review your most recent diagnostics, monitor scan patterns, and continue
              symptom analysis from one patient-centric dashboard.
            </p>
            {errors.summary && <div className="panel-error-card">{errors.summary}</div>}
          </section>

          <StatsRow summary={summary} />
          <RiskTrendChart scanData={scanHistory} error={errors.scans} />
          <ScanCalendar scans={scanHistory} error={errors.scans} />
        </div>

        <div className="dashboard-layout__right">
          <SymptomDoughnut data={symptomData} error={errors.symptoms} />
          <RiskDistributionBars scans={scanHistory} error={errors.scans} />
          <RecentScansList scans={scanHistory} error={errors.scans} />
        </div>
      </main>
    </div>
  );
}


export default Dashboard;
