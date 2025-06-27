import './login.css'; // Same style used
import { useNavigate } from 'react-router-dom';

export default function Register() {
  const navigate = useNavigate();

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

        <form className="login-form">
          <input type="text" placeholder="Full Name" required />
          <input type="email" placeholder="Email" required />
          <input type="text" placeholder="Username" required />
          <input type="password" placeholder="Password" required />
          <select className="role-select" required>
            <option value="" disabled selected>Select Role</option>
            <option value="candidate">Candidate</option>
            <option value="recruiter">Recruiter</option>
          </select>
          <button type="submit">Register</button>
        </form>

        <p className="register-link">
          Already have an account ?{' '}
          <span onClick={() => navigate('/login')}>Login</span>
        </p>
      </div>
    </div>
  );
}
