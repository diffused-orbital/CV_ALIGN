import React, { useEffect, useState } from 'react';
import './recruiterdashboard.css';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function RecruiterDashboard() {
  const [username, setUsername] = useState('');
  const [summary, setSummary] = useState({ jobs: 0, cvs: 0 });
  const [jobData, setJobData] = useState([]);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    axios
      .get('http://localhost:8000/recruiter/dashboard', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      .then((res) => {
        const data = res.data;

        // Calculate total CVs across all jobs
        const totalCVs = data.jobs.reduce((sum, job) => sum + job.resumes_applied, 0);

        // Update state with real data
        setUsername(data.recruiter);
        setSummary({
          jobs: data.total_jobs_posted,
          cvs: totalCVs,
        });

        // Adapt to your frontend format
        const formattedJobs = data.jobs.map((job) => ({
          id: job.job_id,
          title: job.position,
          company: job.company,
          totalCVs: job.resumes_applied,
        }));

        setJobData(formattedJobs);
      })
      .catch((err) => {
        console.error("Error loading recruiter dashboard:", err);
        navigate('/login');
      });
  }, [navigate]);

  return (
    <div className="recruiter-dashboard-bg">
      <div className="brand">CV ALIGNER</div>

      <button className="logout-btn" onClick={handleLogout} title="Logout">
        <svg xmlns="http://www.w3.org/2000/svg" height="32px" viewBox="0 -960 960 960" width="32px" fill="#e3e3e3">
          <path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h280v80H200v560h280v80H200Zm440-160-55-58 102-102H360v-80h327L585-622l55-58 200 200-200 200Z" />
        </svg>
      </button>

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
        <div className="post-job-btn-row">
          <button className="post-job-btn" onClick={() => navigate('/upload-job')}>
             + Post New Job
             </button>
        </div>
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
              {jobData.length === 0 ? (
                <tr>
                  <td colSpan="3" className="dashboard-empty">
                    You haven’t posted any jobs yet.
                  </td>
                </tr>
              ) : (
                jobData.map((job) => (
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
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
