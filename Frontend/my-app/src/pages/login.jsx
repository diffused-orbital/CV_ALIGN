import './Login.css';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser, fetchUserProfile } from '../api'; // Adjust path if needed
import InlineMessage from '../components/InlineMessage';

export default function Login() {
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      // 1. Login request to FastAPI
      const data = await loginUser(form);

      // 2. Store token in localStorage
      localStorage.setItem('token', data.access_token);

      // 3. Get user info using token
      const user = await fetchUserProfile(data.access_token);

      // 4. Navigate to dashboard based on role
      if (user.role === 'candidate') {
        navigate('/candidate-dashboard');
      } else if (user.role === 'recruiter') {
        navigate('/recruiter-dashboard');
      } else {
        setError('This account has an unrecognized role.');
      }
    } catch (err) {
      console.error("Login error:", err);
      setError(err.response?.data?.detail || 'Login failed. Please check your email and password.');
    }
  };

  return (
    <div className="login-container">
      <button className="home-button" onClick={() => navigate('/')}>
        <span className="home-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 960">
            <path d="M400,880 L0,480 L400,80 L471,151 L142,480 L471,809 L400,880 Z" />
          </svg>
        </span>
      </button>

      <div className="login-box">
        <h1 className="title">CV ALIGNER</h1>
        <p className="subtitle">Login to continue</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <input
            type="email"
            name="username"
            placeholder="Email"
            value={form.username}
            onChange={handleChange}
            required
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={form.password}
            onChange={handleChange}
            required
          />
          <button type="submit">Login</button>
        </form>

        <InlineMessage type="error">{error}</InlineMessage>

        <p className="register-link">
          <span onClick={() => navigate('/forgot-password')}>Forgot password?</span>
        </p>
        <p className="register-link">
          New to CV ALIGNER ? <span onClick={() => navigate('/register')}>Register</span>
        </p>
      </div>
    </div>
  );
}
