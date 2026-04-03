import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Send,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import Navbar from '../components/Navbar';
import { predictHealth } from '../api/health';
import '../styles/AnalyzePage.css';


const INITIAL_FORM = {
  bp_systolic: '',
  bp_diastolic: '',
  sugar_level: '',
  cholesterol: '',
  heart_rate: '',
  bmi: '',
  age: '',
  gender: 1,
  symptom_fever: 0,
  symptom_cough: 0,
  symptom_fatigue: 0,
  symptom_headache: 0,
  symptom_chest_pain: 0,
  symptom_breathlessness: 0,
  symptom_sweating: 0,
  symptom_nausea: 0,
};

const VITAL_FIELDS = [
  { name: 'age', label: 'Age', min: 1, max: 110, placeholder: '45' },
  { name: 'bmi', label: 'BMI', min: 10, max: 60, placeholder: '24.5' },
  { name: 'bp_systolic', label: 'BP Systolic', min: 70, max: 220, placeholder: '120' },
  { name: 'bp_diastolic', label: 'BP Diastolic', min: 40, max: 140, placeholder: '80' },
  { name: 'sugar_level', label: 'Sugar Level', min: 50, max: 400, placeholder: '110' },
  { name: 'cholesterol', label: 'Cholesterol', min: 100, max: 400, placeholder: '190' },
  { name: 'heart_rate', label: 'Heart Rate', min: 40, max: 180, placeholder: '74' },
];

const SYMPTOMS = [
  { key: 'symptom_fever', label: 'Fever' },
  { key: 'symptom_cough', label: 'Cough' },
  { key: 'symptom_fatigue', label: 'Fatigue' },
  { key: 'symptom_headache', label: 'Headache' },
  { key: 'symptom_chest_pain', label: 'Chest Pain' },
  { key: 'symptom_breathlessness', label: 'Breathlessness' },
  { key: 'symptom_sweating', label: 'Sweating' },
  { key: 'symptom_nausea', label: 'Nausea' },
];


function AnalyzePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState(INITIAL_FORM);
  const [validationErrors, setValidationErrors] = useState({});
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
    setValidationErrors((current) => ({ ...current, [name]: '' }));
    setError('');
  };

  const handleGenderChange = (value) => {
    setFormData((current) => ({ ...current, gender: value }));
  };

  const toggleSymptom = (key) => {
    setFormData((current) => ({
      ...current,
      [key]: current[key] === 1 ? 0 : 1,
    }));
  };

  const validateStepOne = () => {
    const nextErrors = {};

    VITAL_FIELDS.forEach((field) => {
      const value = Number(formData[field.name]);
      if (formData[field.name] === '' || Number.isNaN(value)) {
        nextErrors[field.name] = 'Required';
      } else if (value < field.min || value > field.max) {
        nextErrors[field.name] = `${field.min}-${field.max}`;
      }
    });

    setValidationErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setError('');

    try {
      const response = await predictHealth({
        ...formData,
        bp_systolic: Number(formData.bp_systolic),
        bp_diastolic: Number(formData.bp_diastolic),
        sugar_level: Number(formData.sugar_level),
        cholesterol: Number(formData.cholesterol),
        heart_rate: Number(formData.heart_rate),
        bmi: Number(formData.bmi),
        age: Number(formData.age),
        gender: Number(formData.gender),
      });
      setResult(response);
      setStep(3);
    } catch (requestError) {
      if (!requestError.response) {
        setError('Server unreachable. Check your connection.');
      } else {
        setError(requestError?.response?.data?.message || 'Request failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const resetAnalysis = () => {
    setStep(1);
    setFormData(INITIAL_FORM);
    setValidationErrors({});
    setError('');
    setResult(null);
  };

  return (
    <div className="analyze-page">
      <Navbar />
      <div className="analyze-page__container">
        <div className="analyze-card">
          <header className="analyze-card__header">
            <p className="analyze-card__eyebrow">Medical Diagnostic Simulation</p>
            <h1>{step === 3 ? 'Analysis Complete' : 'Analyse Symptoms'}</h1>
            <p className="analyze-card__copy">
              {step === 3
                ? 'Your latest diagnostic result has been saved to the dashboard history.'
                : 'Complete the vitals and symptom flow to run the 16-feature prediction model.'}
            </p>

            {step !== 3 && (
              <div className="analyze-card__steps">
                <span className={`analyze-card__step ${step >= 1 ? 'is-active' : ''}`}>1</span>
                <span className={`analyze-card__step-line ${step >= 2 ? 'is-active' : ''}`} />
                <span className={`analyze-card__step ${step >= 2 ? 'is-active' : ''}`}>2</span>
              </div>
            )}
          </header>

          {step === 1 && (
            <div className="analyze-panel">
              <div className="analyze-grid">
                {VITAL_FIELDS.map((field) => (
                  <label key={field.name} className="analyze-field">
                    <span>{field.label}</span>
                    <input
                      name={field.name}
                      type="number"
                      placeholder={field.placeholder}
                      value={formData[field.name]}
                      onChange={handleInputChange}
                    />
                    {validationErrors[field.name] && (
                      <small>{validationErrors[field.name]}</small>
                    )}
                  </label>
                ))}

                <div className="analyze-field">
                  <span>Gender</span>
                  <div className="analyze-gender-toggle">
                    <button
                      type="button"
                      className={Number(formData.gender) === 1 ? 'is-active' : ''}
                      onClick={() => handleGenderChange(1)}
                    >
                      Male
                    </button>
                    <button
                      type="button"
                      className={Number(formData.gender) === 0 ? 'is-active' : ''}
                      onClick={() => handleGenderChange(0)}
                    >
                      Female
                    </button>
                  </div>
                </div>
              </div>

              <div className="analyze-panel__actions">
                <button type="button" className="analyze-button analyze-button--primary" onClick={() => validateStepOne() && setStep(2)}>
                  Symptom Check
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="analyze-panel">
              <div className="analyze-symptoms">
                {SYMPTOMS.map((symptom) => (
                  <button
                    key={symptom.key}
                    type="button"
                    className={`analyze-symptom ${Number(formData[symptom.key]) === 1 ? 'is-selected' : ''}`}
                    onClick={() => toggleSymptom(symptom.key)}
                  >
                    {Number(formData[symptom.key]) === 1 ? <CheckCircle2 size={18} /> : <span className="analyze-symptom__bullet" />}
                    <span>{symptom.label}</span>
                  </button>
                ))}
              </div>

              {error && (
                <div className="analyze-error-banner">
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}

              <div className="analyze-panel__actions analyze-panel__actions--split">
                <button type="button" className="analyze-button analyze-button--secondary" onClick={() => setStep(1)} disabled={isLoading}>
                  <ChevronLeft size={18} />
                  Back
                </button>
                <button type="button" className="analyze-button analyze-button--primary" onClick={handleSubmit} disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 size={18} className="analyze-spinner" />
                      Analysing...
                    </>
                  ) : (
                    <>
                      <Send size={18} />
                      Run Prediction
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {step === 3 && result && (
            <div className={`analyze-result-card analyze-result-card--${result.risk_level.toLowerCase()}`}>
              <div className="analyze-result-card__top">
                <p className="analyze-result-card__label">Primary Diagnosis</p>
                <span className={`analyze-result-card__risk analyze-result-card__risk--${result.risk_level.toLowerCase()}`}>
                  {result.risk_level} Risk
                </span>
              </div>

              <h2>{result.diagnosis}</h2>

              <div className="analyze-result-card__confidence">
                <div className="analyze-result-card__confidence-header">
                  <span>Confidence Score</span>
                  <strong>{result.confidence}%</strong>
                </div>
                <progress className="analyze-result-card__progress" value={result.confidence} max="100" />
              </div>

              <div className="analyze-result-card__section">
                <span>Suggested Medications</span>
                <div className="analyze-result-card__chips">
                  {result.medications.length > 0 ? (
                    result.medications.map((item) => <span key={item}>{item}</span>)
                  ) : (
                    <span>No medication mapping found</span>
                  )}
                </div>
              </div>

              <div className="analyze-result-card__actions">
                <button type="button" className="analyze-button analyze-button--secondary" onClick={resetAnalysis}>
                  Run Another Scan
                </button>
                <button type="button" className="analyze-button analyze-button--primary" onClick={() => navigate('/dashboard')}>
                  View Dashboard
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


export default AnalyzePage;
