import './candidatedashboard.css';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';

const statusLabel = (status) =>
  status === 1 ? 'Accepted' : status === 2 ? 'Rejected' : 'Pending';

export default function CandidateDashboard() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [profileComplete, setProfileComplete] = useState(true);
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

  const loadJobs = async () => {
    const res = await axios.get(`${API_URL}/jobs`, { headers: authHeader() });
    setJobs(res.data.jobs || []);
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    (async () => {
      try {
        const me = await axios.get(`${API_URL}/me`, { headers: authHeader() });
        setUsername(me.data.username);
        const prof = await axios.get(`${API_URL}/candidate/profile`, { headers: authHeader() });
        setProfileComplete(Boolean(prof.data.complete));
        await loadJobs();
      } catch (err) {
        if (err.response?.status === 401) navigate('/login');
        else setError(err.response?.data?.detail || 'Failed to load dashboard.');
      }
    })();
  }, [navigate]);

  const handleApply = async (job) => {
    setError('');
    setNotice('');
    if (!profileComplete) {
      setError('Please complete your profile before applying.');
      return;
    }
    try {
      await axios.post(`${API_URL}/apply`, { job_id: job.id }, { headers: authHeader() });
      setNotice(`✅ Applied to ${job.title} at ${job.company}.`);
      await loadJobs();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to apply. Please try again.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };
  const handleHome = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  // Show open roles, plus any role the candidate already applied to.
  const visibleJobs = jobs.filter((j) => j.applied || j.is_open !== false);

  return (
    <div className="dashboard-bg">
      <button className="logout-btn" onClick={handleLogout} title="Logout">
        <svg xmlns="http://www.w3.org/2000/svg" height="32px" viewBox="0 -960 960 960" width="32px" fill="#e3e3e3">
          <path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h280v80H200v560h280v80H200Zm440-160-55-58 102-102H360v-80h327L585-622l55-58 200 200-200 200Z" />
        </svg>
      </button>

      <div className="dashboard-header">
        <div className="company-title" onClick={handleHome}>CV ALIGNER</div>
        <div className="dashboard-greeting">Hello, {username}!</div>
      </div>

      <div className="profile-banner">
        {profileComplete ? (
          <span>
            Your profile is complete.{' '}
            <button className="link-btn" onClick={() => navigate('/candidate/profile')}>Edit profile</button>
          </span>
        ) : (
          <span>
            Complete your profile once to apply with a single click.{' '}
            <button className="link-btn" onClick={() => navigate('/candidate/profile')}>Complete profile</button>
          </span>
        )}
      </div>

      {notice && <div className="dashboard-notice success">{notice}</div>}
      {error && <div className="dashboard-notice error">{error}</div>}

      <div className="dashboard-table-scroll-wrap">
        <div className="dashboard-table-area">
          <div className="dashboard-table-header glass">
            <div>Job Title</div>
            <div>Company</div>
            <div>Action</div>
          </div>

          {visibleJobs.length === 0 ? (
            <div className="dashboard-empty glass">No open roles right now.</div>
          ) : (
            visibleJobs.map((job) => (
              <div key={job.id} className="dashboard-tile glass">
                <div>{job.title}</div>
                <div>{job.company}</div>
                <div>
                  {job.applied ? (
                    <span className={`status ${statusLabel(job.status).toLowerCase()}`}>
                      {statusLabel(job.status)}
                    </span>
                  ) : job.is_open === false ? (
                    <span className="status closed">No longer accepting</span>
                  ) : (
                    <button className="apply-inline-btn" onClick={() => handleApply(job)}>
                      Apply
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
