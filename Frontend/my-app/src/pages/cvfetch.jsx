import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';
import './cvfetch.css';

const statusLabel = (status) =>
  status === 1 ? 'Accepted' : status === 0 ? 'Pending' : 'Rejected';

export default function JobDetails() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [candidates, setCandidates] = useState([]);
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    axios
      .get(`${API_URL}/recruiter/job/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => {
        const data = res.data;
        setJobTitle(data.job_title);
        setCompany(data.company);
        setCandidates(data.candidates || []);
      })
      .catch((err) => {
        console.error('Error loading job details:', err);
        setError('Failed to load job details.');
      });
  }, [jobId, navigate]);

  const toggleExpand = (index) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const updateStatus = async (applicationId, action, index) => {
    const token = localStorage.getItem('token');
    try {
      await axios.post(
        `${API_URL}/application/${applicationId}/${action}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCandidates((prev) =>
        prev.map((c, i) =>
          i === index ? { ...c, status: action === 'accept' ? 1 : 2 } : c
        )
      );
    } catch (err) {
      console.error(`Failed to ${action} application:`, err);
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

      {error && <p className="upload-message">{error}</p>}

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
                          disabled={c.status === -1 || c.status === 2}
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
                              {c.strengths || 'No feedback available yet.'}
                            </span>
                          </div>
                          <div>
                            <span className="feedback-title">Weaknesses: </span>
                            <span className="feedback-content">
                              {c.weaknesses || 'No feedback available yet.'}
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
