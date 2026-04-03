import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import '../styles/LoginPage.css';


function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
    setError('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      await login(formData.username, formData.password);
      navigate('/dashboard', { replace: true });
    } catch (requestError) {
      if (!requestError.response) {
        setError('Server unreachable. Check your connection.');
      } else {
        setError(requestError?.response?.data?.detail || 'Request failed');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card-shell">
        <div className="auth-card-shell__content">
          <p className="auth-eyebrow">MediPredict.ai</p>
          <h1>Sign in to your health intelligence dashboard</h1>
          <p className="auth-copy">
            Track prior scans, monitor risk patterns, and continue symptom analysis
            from a single secure workspace.
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            {location.state?.successMessage && (
              <p className="auth-success">{location.state.successMessage}</p>
            )}

            <label className="auth-field">
              <span>Username</span>
              <input
                name="username"
                type="text"
                value={formData.username}
                onChange={handleChange}
                autoComplete="username"
                required
              />
            </label>

            <label className="auth-field">
              <span>Password</span>
              <input
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                autoComplete="current-password"
                required
              />
            </label>

            {error && <p className="auth-error">{error}</p>}

            <button className="auth-submit-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <p className="auth-footer-copy">
            Don&apos;t have an account? <Link to="/signup">Create one</Link>
          </p>
        </div>
      </div>
    </div>
  );
}


export default LoginPage;
