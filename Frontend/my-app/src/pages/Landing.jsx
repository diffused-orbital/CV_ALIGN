import './Landing.css';
import { useNavigate } from 'react-router-dom';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="landing-container">
      <header className="landing-header">
        <h1 className="title">CV ALIGNER</h1>
      </header>

      <main className="landing-main">
        <h2 className="quote">Let your resume speak, intelligently.</h2>
      </main>

      <footer className="landing-footer">
        <button className="get-started" onClick={() => navigate('/login')}>
        Get Started 
        </button>
      </footer>
    </div>
  );
}
