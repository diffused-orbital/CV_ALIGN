import './login.css'; // reuse existing styles
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { forgotPassword, resetPassword } from '../api';
import InlineMessage from '../components/InlineMessage';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      const data = await forgotPassword(email);
      // In production the token arrives by email; here we carry it forward.
      setResetToken(data.reset_token);
      setStep(2);
      setMessage('Email verified. Choose a new password.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not start password reset. Please try again.');
    }
  };

  const handleResetSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    try {
      await resetPassword(resetToken, password);
      setMessage('Password reset successful! Redirecting to login…');
      setTimeout(() => navigate('/login'), 1200);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not reset password. Please try again.');
    }
  };

  return (
    <div className="login-container">
      <button className="home-button" onClick={() => navigate('/login')}>
        <span className="home-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 960">
            <path d="M400,880 L0,480 L400,80 L471,151 L142,480 L471,809 L400,880 Z" />
          </svg>
        </span>
      </button>

      <div className="login-box">
        <h1 className="title">CV ALIGNER</h1>
        <p className="subtitle">Reset your password</p>

        {step === 1 ? (
          <form className="login-form" onSubmit={handleEmailSubmit}>
            <input
              type="email"
              name="email"
              placeholder="Enter your account email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <button type="submit">Continue</button>
          </form>
        ) : (
          <form className="login-form" onSubmit={handleResetSubmit}>
            <input
              type="password"
              name="password"
              placeholder="New password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <input
              type="password"
              name="confirm"
              placeholder="Confirm new password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
            <button type="submit">Reset Password</button>
          </form>
        )}

        <InlineMessage type="error">{error}</InlineMessage>
        <InlineMessage type="success">{message}</InlineMessage>

        <p className="register-link">
          Remembered it? <span onClick={() => navigate('/login')}>Back to Login</span>
        </p>
      </div>
    </div>
  );
}
