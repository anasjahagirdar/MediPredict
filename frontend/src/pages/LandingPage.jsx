import { Activity, Cpu, Database, Heart, ShieldCheck, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import '../styles/LandingPage.css';


function LandingPage({ isAuthenticated }) {
  const navigate = useNavigate();

  return (
    <div className="landing-container">
      <div className="side-data-stream left-stream">
        <span>System Online // Azure Cloud // Random Forest v2.1 // Secure Node 01</span>
      </div>
      <div className="side-data-stream right-stream">
        <span>Processing Biomarkers // JWT Access // Authenticated Records // Clinical UX</span>
      </div>

      <main className="main-layout">
        <div className="content-left">
          <div className="badge">
            <ShieldCheck size={18} />
            <span>MEDICAL FUTURISM PLATFORM</span>
          </div>

          <h1 className="title-main">
            MediPredict
            <br />
            Intelligence
          </h1>

          <p className="description">
            Secure patient sign-in, longitudinal scan history, and a dedicated AI
            analysis workflow designed for repeat diagnostic simulation.
          </p>

          <div className="landing-actions">
            {isAuthenticated ? (
              <>
                <button className="secondary-action" onClick={() => navigate('/dashboard')}>
                  Open Dashboard
                </button>
                <button className="predict-btn" onClick={() => navigate('/analyze')}>
                  Continue Analysis
                </button>
              </>
            ) : (
              <>
                <button
                  className="secondary-action"
                  onClick={() => navigate('/login', { state: { mode: 'login' } })}
                >
                  Login
                </button>
                <button
                  className="predict-btn"
                  onClick={() => navigate('/login', { state: { mode: 'signup' } })}
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </div>

        <div className="visual-right">
          <Activity size={280} className="central-icon" />

          <div className="data-node node-1">
            <Heart size={18} />
            <span>Blood Pressure</span>
          </div>
          <div className="data-node node-2">
            <Database size={18} />
            <span>Scan History Vault</span>
          </div>
          <div className="data-node node-3">
            <Cpu size={18} />
            <span>16-Feature Random Forest</span>
          </div>
          <div className="data-node node-4">
            <Zap size={18} />
            <span>User Guided Analysis</span>
          </div>
        </div>
      </main>
    </div>
  );
}


export default LandingPage;
