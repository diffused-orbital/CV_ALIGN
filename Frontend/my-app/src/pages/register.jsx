import './login.css'; // reuse existing styles
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { registerUser } from '../api'; // this should point to src/api.js

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    role: '',
  });

  const handleChange = (e) => {
    setForm(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await registerUser(form);
      alert("✅ Registration successful!");
      navigate('/login'); // go to login page
    } catch (err) {
       console.error("FULL ERROR:", err);
       console.error("RESPONSE:", err.response?.data);
       alert("❌ Registration failed: " + (err.response?.data?.detail || "Unknown error"));
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
        <p className="subtitle">Create your account</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <input
            name="username"
            type="text"
            placeholder="Username"
            value={form.username}
            onChange={handleChange}
            required
          />
          <input
            name="email"
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={handleChange}
            required
          />
          <input
            name="password"
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={handleChange}
            required
          />
          <select
            name="role"
            className="role-select"
            value={form.role}
            onChange={handleChange}
            required
          >
            <option value="" disabled>Select Role</option>
            <option value="candidate">Candidate</option>
            <option value="recruiter">Recruiter</option>
          </select>

          <button type="submit">Register</button>
        </form>

        <p className="register-link">
          Already have an account?{' '}
          <span onClick={() => navigate('/login')}>Login</span>
        </p>
      </div>
    </div>
  );
}
