import React, { useEffect, useState } from 'react';
import './recruiterdashboard.css';
import { useNavigate } from 'react-router-dom';

export default function RecruiterDashboard() {
  const [username, setUsername] = useState('JohnDoe');
  const [summary, setSummary] = useState({ jobs: 0, cvs: 0 });
  const [jobData, setJobData] = useState([]);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  useEffect(() => {
    // Replace with mock data
    const fakeSummary = {
      username: 'JohnDoe',
      totalJobs: 4,
      totalCVs: 26,
    };

    const fakeJobs = [
      { id: 1, title: 'Frontend Developer', company: 'Google', totalCVs: 10 },
      { id: 2, title: 'Backend Engineer', company: 'Amazon', totalCVs: 6 },
      { id: 3, title: 'Data Analyst', company: 'Netflix', totalCVs: 5 },
      { id: 4, title: 'ML Engineer', company: 'OpenAI', totalCVs: 5 },
    ];

    setTimeout(() => {
      setUsername(fakeSummary.username);
      setSummary({
        jobs: fakeSummary.totalJobs,
        cvs: fakeSummary.totalCVs,
      });
      setJobData(fakeJobs);
    }, 300);
  }, []);

  // Table header and rows are rendered as a table for perfect alignment
  return (
    <div className="recruiter-dashboard-bg">
      {/* Brand top left */}
      <div className="brand">CV ALIGNER</div>

      {/* Logout top right */}
      <button className="logout-btn" onClick={handleLogout} title="Logout">
        <svg xmlns="http://www.w3.org/2000/svg" height="32px" viewBox="0 -960 960 960" width="32px" fill="#e3e3e3">
          <path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h280v80H200v560h280v80H200Zm440-160-55-58 102-102H360v-80h327L585-622l55-58 200 200-200 200Z" />
        </svg>
      </button>

      {/* Centered content */}
      <div className="dashboard-center-content">
        <div className="greeting">Hello, {username} !</div>
        <div className="summary-row">
          <div className="summary-box">
            <div className="summary-title">Total Jobs Posted</div>
            <div className="summary-value">{summary.jobs}</div>
          </div>
          <div className="summary-box">
            <div className="summary-title">Total CVs Received</div>
            <div className="summary-value">{summary.cvs}</div>
          </div>
        </div>

        {/* Table with sticky header and scrollable body */}
        <div className="table-outer-wrap">
          <table className="job-table">
            <thead>
              <tr>
                <th>Job Title</th>
                <th>Company</th>
                <th>CVs Received</th>
              </tr>
            </thead>
            <tbody>
              {jobData.map((job) => (
                <tr
                  key={job.id}
                  className="job-row"
                  onClick={() => navigate(`/recruiter/job/${job.id}`)}
                  tabIndex={0}
                  role="button"
                  aria-label={`View details for ${job.title} at ${job.company}`}
                >
                  <td>{job.title}</td>
                  <td>{job.company}</td>
                  <td>{job.totalCVs} CVs</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
