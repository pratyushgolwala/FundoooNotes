import React, { useState, useContext } from 'react';
import '../styles/auth.css';
import authService from '../../services/authService';
import { AuthContext } from '../../context/AuthContext';

export default function Login({ onSuccess }) {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('login');
  const [userId, setUserId] = useState(null);
  const [otpCode, setOtpCode] = useState('');
  const { login } = useContext(AuthContext);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authService.login(formData);
      setUserId(response.data.payload.user_id);
      setStep('otp');
    } catch (err) {
      setError(err.response?.data?.payload?.detail || err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
  e.preventDefault();
  setError('');
  setLoading(true);

  try {
    const response = await authService.verifyOtp({
      user_id: userId,
      otp: otpCode,
    });
    
    // Save credentials and redirect immediately
    login(response.data.payload.access_token, userId);
    
    // Clear form and redirect
    setOtpCode('');
    setUserId(null);
    setStep('login');
    
    // Call success callback to navigate to dashboard
    onSuccess();
  } catch (err) {
    setError(err.response?.data?.payload?.detail || err.response?.data?.detail || 'OTP verification failed');
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>📝 FundooNotes</h1>
          <p className="auth-subtitle">
            {step === 'login' ? 'Welcome back' : 'Enter OTP'}
          </p>
        </div>

        {error && <div className="auth-error">{error}</div>}

        {step === 'login' ? (
          <form onSubmit={handleLogin} className="auth-form">
            <div className="form-group">
              <label htmlFor="username">Email or Username</label>
              <input
                id="username"
                type="text"
                placeholder="Enter email or username"
                value={formData.username}
                onChange={(e) =>
                  setFormData({ ...formData, username: e.target.value })
                }
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Enter password"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                required
              />
            </div>

            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleOtpSubmit} className="auth-form">
            <p className="otp-message">
              We've sent a 6-digit code to your email
            </p>

            <div className="form-group">
              <label htmlFor="otp">Enter OTP</label>
              <input
                id="otp"
                type="text"
                placeholder="000000"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                maxLength="6"
                required
              />
            </div>

            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? 'Verifying...' : 'Verify OTP'}
            </button>

            <button
              type="button"
              className="auth-link"
              onClick={() => setStep('login')}
            >
              Back to login
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
