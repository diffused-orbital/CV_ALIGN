import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import './jobdetails.css';

export default function JobDetails() {
  const { jobId } = useParams();
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [candidates, setCandidates] = useState([]);
  const [expandedIndex, setExpandedIndex] = useState(null);

  useEffect(() => {
    // Simulated API response for now
    const fakeJob = {
      title: 'Frontend Developer',
      company: 'Google',
    };

    const fakeCandidates = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      name: `Candidate ${i + 1}`,
      institute: `Institute ${i + 1}`,
      degree: 'B.Tech',
      cgpa: (7 + Math.random() * 3).toFixed(2),
      score: (50 + Math.random() * 50).toFixed(2),
      resumeLink: `https://example.com/resume${i + 1}.pdf`,
      strengths: 'Strong communication, ReactJS, Clean code',
      weaknesses: 'Needs improvement in system design',
    }));

    setTimeout(() => {
      setJobTitle(fakeJob.title);
      setCompany(fakeJob.company);
      setCandidates(fakeCandidates);
    }, 300);
  }, [jobId]);

  const toggleExpand = (index) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  return (
    <div className="job-details-page">
      <h1 className="job-heading">
        {jobTitle} at {company}
      </h1>

      <div className="candidate-table-scroll-wrap">
        <table className="candidate-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Institute</th>
              <th>Degree</th>
              <th>CGPA</th>
              <th>Score</th>
              <th>Resume</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c, index) => (
              <React.Fragment key={c.id}>
                <tr className="candidate-row" onClick={() => toggleExpand(index)}>
                  <td>{c.name}</td>
                  <td>{c.institute}</td>
                  <td>{c.degree}</td>
                  <td>{c.cgpa}</td>
                  <td>{c.score}</td>
                  <td>
                    <a href={c.resumeLink} target="_blank" rel="noopener noreferrer">
                      Download
                    </a>
                  </td>
                  <td>
                    <button className="accept-btn">Accept</button>
                    <button className="reject-btn">Reject</button>
                  </td>
                </tr>
                {expandedIndex === index && (
                  <tr className="expanded-feedback">
                    <td colSpan="7">
                      <strong>Strengths:</strong> {c.strengths} <br />
                      <strong>Weaknesses:</strong> {c.weaknesses}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
