import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';
import './cvfetch.css';

const statusLabel = (status) =>
  status === 1 ? 'Accepted' : status === 2 ? 'Rejected' : 'Pending';

export default function JobDetails() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [isOpen, setIsOpen] = useState(true);
  const [candidates, setCandidates] = useState([]);
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [generating, setGenerating] = useState(false);

  const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

  const loadDetails = async () => {
    const res = await axios.get(`${API_URL}/recruiter/job/${jobId}`, { headers: authHeader() });
    setJobTitle(res.data.job_title);
    setCompany(res.data.company);
    setIsOpen(res.data.is_open);
    setCandidates(res.data.candidates || []);
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    loadDetails().catch((err) => {
      if (err.response?.status === 401) navigate('/login');
      else setError(err.response?.data?.detail || 'Failed to load job details.');
    });
  }, [jobId, navigate]);

  const toggleExpand = (index) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const handleClose = async () => {
    setError('');
    setNotice('');
    try {
      await axios.post(`${API_URL}/recruiter/job/${jobId}/close`, {}, { headers: authHeader() });
      setIsOpen(false);
      setNotice('Applications closed. Click "Generate scores" to rank candidates.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to close applications.');
    }
  };

  const handleGenerate = async () => {
    setError('');
    setNotice('');
    setGenerating(true);
    try {
      const res = await axios.post(
        `${API_URL}/recruiter/job/${jobId}/generate`,
        {},
        { headers: authHeader() }
      );
      setCandidates(res.data.candidates || []);
      setNotice(res.data.message || 'Scores generated.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate scores.');
    } finally {
      setGenerating(false);
    }
  };

  const updateStatus = async (applicationId, action, index) => {
    setError('');
    try {
      await axios.post(
        `${API_URL}/application/${applicationId}/${action}`,
        {},
        { headers: authHeader() }
      );
      setCandidates((prev) =>
        prev.map((c, i) =>
          i === index ? { ...c, status: action === 'accept' ? 1 : 2 } : c
        )
      );
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to ${action} application.`);
    }
  };

  const resumeUrl = (link) =>
    link && link.startsWith('http') ? link : `${API_URL}/${link}`;

  return (
    <div className="job-details-container">
      <button className="home-button" onClick={() => navigate('/recruiter-dashboard')}>
        &larr; Back
      </button>

      <h1 className="job-heading">
        {jobTitle} {company && `at ${company}`}
      </h1>

      <div className="job-controls">
        <span className={`job-state ${isOpen ? 'open' : 'closed'}`}>
          {isOpen ? 'Open — accepting applications' : 'Closed'}
        </span>
        {isOpen ? (
          <button className="control-btn" onClick={handleClose}>
            Close applications
          </button>
        ) : (
          <button className="control-btn generate" onClick={handleGenerate} disabled={generating}>
            {generating ? 'Generating…' : 'Generate scores'}
          </button>
        )}
      </div>

      {notice && <p className="job-notice success">{notice}</p>}
      {error && <p className="job-notice error">{error}</p>}

      <div className="table-scroll-container">
        <table className="candidate-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Institute</th>
              <th>Degree</th>
              <th>CGPA</th>
              <th>Score</th>
              <th>Status</th>
              <th>Resume</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {candidates.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center' }}>
                  No candidates have applied yet.
                </td>
              </tr>
            ) : (
              candidates.map((c, index) => (
                <React.Fragment key={c.application_id}>
                  <tr onClick={() => toggleExpand(index)}>
                    <td>{c.candidate_name}</td>
                    <td>{c.institute}</td>
                    <td>{c.degree}</td>
                    <td>{c.cgpa}</td>
                    <td>{c.score != null ? Number(c.score).toFixed(2) : '—'}</td>
                    <td>{statusLabel(c.status)}</td>
                    <td>
                      <a
                        className="download-link"
                        href={resumeUrl(c.resume_link)}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Download
                      </a>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="accept-button"
                          disabled={c.status === 1}
                          onClick={(e) => {
                            e.stopPropagation();
                            updateStatus(c.application_id, 'accept', index);
                          }}
                        >
                          Accept
                        </button>
                        <button
                          className="reject-button"
                          disabled={c.status === 2}
                          onClick={(e) => {
                            e.stopPropagation();
                            updateStatus(c.application_id, 'reject', index);
                          }}
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                  {expandedIndex === index && (
                    <tr className="expanded-row">
                      <td colSpan="8">
                        <div className="feedback-box">
                          <div>
                            <span className="feedback-title">Strengths: </span>
                            <span className="feedback-content">
                              {c.strengths || 'No feedback yet — close the job and click Generate.'}
                            </span>
                          </div>
                          <div>
                            <span className="feedback-title">Weaknesses: </span>
                            <span className="feedback-content">
                              {c.weaknesses || 'No feedback yet — close the job and click Generate.'}
                            </span>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
