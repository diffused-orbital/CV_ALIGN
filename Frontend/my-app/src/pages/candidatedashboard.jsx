import './candidatedashboard.css';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function CandidateDashboard() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [applications, setApplications] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      try {
        const response = await axios.get('http://localhost:8000/candidate/dashboard', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        setUsername(response.data.candidate);
        setApplications(response.data.applications);
      } catch (err) {
        console.error('Error loading candidate dashboard:', err);
        navigate('/login');
      }
    };

    fetchData();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
  <div className="dashboard-bg">
    <button className="logout-btn" onClick={handleLogout} title="Logout">
      <svg xmlns="http://www.w3.org/2000/svg" height="32px" viewBox="0 -960 960 960" width="32px" fill="#e3e3e3">
        <path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h280v80H200v560h280v80H200Zm440-160-55-58 102-102H360v-80h327L585-622l55-58 200 200-200 200Z" />
      </svg>
    </button>

    <div className="dashboard-header">
      <div className="company-title">CV ALIGNER</div>
      <div className="dashboard-greeting">Hello, {username}!</div>
    </div>

    {/* Scrollable table area */}
    <div className="dashboard-table-scroll-wrap">
      <div className="dashboard-table-area">
        <div className="dashboard-table-header glass">
          <div>Job Title</div>
          <div>Company</div>
          <div>Status</div>
        </div>

        {applications.length === 0 ? (
          <div className="dashboard-empty glass">
            No company applied currently.
          </div>
        ) : (
          applications.map((app, idx) => (
            <div key={idx} className="dashboard-tile glass">
              <div>{app.job_title}</div>
              <div>{app.company}</div>
              <div className={`status ${app.status.toLowerCase()}`}>{app.status}</div>
            </div>
          ))
        )}
      </div>
    </div>
  </div>
);
}
