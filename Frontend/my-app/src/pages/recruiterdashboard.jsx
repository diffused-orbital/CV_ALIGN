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
  const handlehome = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  useEffect(() => {
  const fakeSummary = {
    username: 'JohnDoe',
    totalJobs: 30,
    totalCVs: 400,
  };

  const fakeJobs = Array.from({ length: 30 }, (_, i) => ({
    id: i + 1,
    title: `Position ${i + 1}`,
    company: `Company ${i + 1}`,
    totalCVs: Math.floor(Math.random() * 20) + 1,
  }));

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
      <div className="brand" onClick={handlehome}>CV ALIGNER</div>

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
     <button className="apply-button" onClick={() => navigate('/recruiter/upload')}>
        <span className="apply-icon">
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3">
                <path d="M170-228q-38-45-61-99T80-440h82q6 43 22 82.5t42 73.5l-56 56ZM80-520q8-59 30-113t60-99l56 56q-26 34-42 73.5T162-520H80ZM438-82q-59-6-112.5-28.5T226-170l56-58q35 26 74 43t82 23v80ZM284-732l-58-58q47-37 101-59.5T440-878v80q-43 6-82.5 23T284-732ZM518-82v-80q44-6 83.5-22.5T676-228l58 58q-47 38-101.5 60T518-82Zm160-650q-35-26-75-43t-83-23v-80q59 6 113.5 28.5T734-790l-56 58Zm112 504-56-56q26-34 42-73.5t22-82.5h82q-8 59-30 113t-60 99Zm8-292q-6-43-22-82.5T734-676l56-56q38 45 61 99t29 113h-82ZM441-280v-247L337-423l-56-57 200-200 200 200-57 56-103-103v247h-80Z"/>
            </svg>
        </span>
     Upload a Job
    </button>
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
