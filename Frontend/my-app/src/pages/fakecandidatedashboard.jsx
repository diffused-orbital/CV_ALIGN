import './candidatedashboard.css';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function FakeCandidateDashboard() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('John Doe');
  const [applications, setApplications] = useState([]);

  useEffect(() => {
    setUsername("John Doe");
    // Fake data to simulate many applications
    const fakeData = Array.from({ length: 30 }, (_, i) => ({
      job_title: `Frontend Developer ${i + 1}`,
      company: `Tech Corp ${i + 1}`,
      status: ['Pending', 'Accepted', 'Rejected'][i % 3]
    }));
    setApplications(fakeData);
  }, []);

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
        <div className="dashboard-greeting">Hello, {username} !</div>
      </div>
     <button className="apply-button" onClick={() => navigate('/candidate/upload')}>
        <span className="apply-icon">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3">
                <path d="M170-228q-38-45-61-99T80-440h82q6 43 22 82.5t42 73.5l-56 56ZM80-520q8-59 30-113t60-99l56 56q-26 34-42 73.5T162-520H80ZM438-82q-59-6-112.5-28.5T226-170l56-58q35 26 74 43t82 23v80ZM284-732l-58-58q47-37 101-59.5T440-878v80q-43 6-82.5 23T284-732ZM518-82v-80q44-6 83.5-22.5T676-228l58 58q-47 38-101.5 60T518-82Zm160-650q-35-26-75-43t-83-23v-80q59 6 113.5 28.5T734-790l-56 58Zm112 504-56-56q26-34 42-73.5t22-82.5h82q-8 59-30 113t-60 99Zm8-292q-6-43-22-82.5T734-676l56-56q38 45 61 99t29 113h-82ZM441-280v-247L337-423l-56-57 200-200 200 200-57 56-103-103v247h-80Z"/>
            </svg>
        </span>
     Apply for a Job
    </button>

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
