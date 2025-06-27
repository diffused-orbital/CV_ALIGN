import './Login.css'; 
import { useNavigate } from 'react-router-dom';

export default function Login() {
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
        <p className="subtitle">Login to continue</p>

        <form className="login-form">
          <input type="text" placeholder="Username" required />
          <input type="password" placeholder="Password" required />
          <button type="submit">Login</button>
        </form>

        <p className="register-link">
          New to CV ALIGNER ?{' '}
          <span onClick={() => navigate('/register')}>Register</span>
        </p>
      </div>
    </div>
  );
}
