import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import '../styles/LoginPage.css';
import '../styles/SignupPage.css';


const INITIAL_STATE = {
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  password: '',
  confirm_password: '',
};

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]{3,}$/;
const EMAIL_ERROR_MESSAGE = 'Please enter a valid email address.';


function SignupPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [formData, setFormData] = useState(INITIAL_STATE);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name } = event.target;
    let { value } = event.target;

    if (name === 'first_name' || name === 'last_name') {
      value = value.replace(/[^a-zA-Z\s]/g, '');
    }

    setFormData((current) => ({ ...current, [name]: value }));
    setError('');
  };

  const handleNameKeyDown = (event) => {
    if (event.ctrlKey || event.metaKey || event.altKey) {
      return;
    }
    if (event.key.length === 1 && !/[a-zA-Z\s]/.test(event.key)) {
      event.preventDefault();
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!EMAIL_REGEX.test(formData.email.trim())) {
      setError(EMAIL_ERROR_MESSAGE);
      return;
    }

    if (formData.password !== formData.confirm_password) {
      setError('Passwords must match.');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      await register({
        first_name: formData.first_name,
        last_name: formData.last_name,
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });
      navigate('/login', {
        replace: true,
        state: { successMessage: 'Account created successfully. Please sign in.' },
      });
    } catch (requestError) {
      if (!requestError.response) {
        setError('Server unreachable. Check your connection.');
      } else {
        const data = requestError.response.data;
        if (typeof data === 'object') {
          const firstValue = Object.values(data).flat()[0];
          setError(firstValue || 'Request failed');
        } else {
          setError('Request failed');
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card-shell auth-card-shell--wide">
        <div className="auth-card-shell__content">
          <p className="auth-eyebrow">Create account</p>
          <h1>Start your MediPredict health history</h1>
          <p className="auth-copy">
            Create a secure account to save every scan, compare outcomes over time,
            and access your personalized dashboard.
          </p>

          <form className="auth-form auth-form--grid" onSubmit={handleSubmit}>
            <label className="auth-field">
              <span>First Name</span>
              <input
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                onKeyDown={handleNameKeyDown}
                required
              />
            </label>

            <label className="auth-field">
              <span>Last Name</span>
              <input
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                onKeyDown={handleNameKeyDown}
                required
              />
            </label>

            <label className="auth-field">
              <span>Username</span>
              <input name="username" value={formData.username} onChange={handleChange} required />
            </label>

            <label className="auth-field">
              <span>Email</span>
              <input name="email" type="email" value={formData.email} onChange={handleChange} required />
              {error === EMAIL_ERROR_MESSAGE && <p className="auth-error">{error}</p>}
            </label>

            <label className="auth-field">
              <span>Password</span>
              <input name="password" type="password" value={formData.password} onChange={handleChange} required />
            </label>

            <label className="auth-field">
              <span>Confirm Password</span>
              <input
                name="confirm_password"
                type="password"
                value={formData.confirm_password}
                onChange={handleChange}
                required
              />
            </label>

            {error && error !== EMAIL_ERROR_MESSAGE && <p className="auth-error auth-error--full">{error}</p>}

            <button className="auth-submit-button auth-submit-button--full" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <p className="auth-footer-copy">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}


export default SignupPage;
