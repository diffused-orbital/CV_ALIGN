import './apply.css';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function CandidateUpload() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [jobOptions, setJobOptions] = useState([]);
  const [message, setMessage] = useState('');
  const [formData, setFormData] = useState({
    cgpa: '',
    degree: '',
    institute: '',
    job: '',
    resume: null,
  });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    // Fetch candidate info (name)
    axios.get('http://localhost:8000/me', {
      headers: { Authorization: `Bearer ${token}` }
    })
    .then(res => {
      setName(res.data.username);
    })
    .catch(err => {
      console.error("❌ Error fetching user info:", err);
      navigate('/login');
    });

    // Fetch list of available jobs
    axios.get('http://localhost:8000/jobs', {
      headers: { Authorization: `Bearer ${token}` }
    })
    .then(res => {
      setJobOptions(res.data.jobs || []);
    })
    .catch(err => {
      console.error("❌ Error fetching jobs:", err);
    });
  }, [navigate]);

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: files ? files[0] : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    if (!token) {
      setMessage("❌ Please login first.");
      return;
    }

    const selectedJob = jobOptions.find(j => j.title === formData.job);
    if (!selectedJob) {
      setMessage("❌ Invalid job selected.");
      return;
    }

    const data = new FormData();
    data.append('job_id', selectedJob.id);
    data.append('cgpa', formData.cgpa);
    data.append('degree', formData.degree);
    data.append('institute', formData.institute);
    data.append('file', formData.resume);

    try {
      const res = await axios.post('http://localhost:8000/apply', data, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      setMessage("✅ Application submitted successfully!");
      setTimeout(() => navigate('/candidate-dashboard'), 2000);
    } catch (err) {
      console.error("❌ Application failed:", err);
      setMessage("❌ Failed to apply. Please try again.");
    }
  };

  return (
    <div className="upload-container">
      <button className="home-button" onClick={() => navigate('/candidate-dashboard')}>
        <span className="home-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 960">
            <path d="M400,880 L0,480 L400,80 L471,151 L142,480 L471,809 L400,880 Z" />
          </svg>
        </span>
      </button>

      <form className="upload-box" onSubmit={handleSubmit}>
        <h2 className="form-title">Job Application</h2>

        <label>Name</label>
        <input type="text" value={name} disabled />

        <label>CGPA</label>
        <input type="text" name="cgpa" value={formData.cgpa} onChange={handleChange} required />

        <label>Degree</label>
        <input type="text" name="degree" value={formData.degree} onChange={handleChange} required />

        <label>Institute</label>
        <input type="text" name="institute" value={formData.institute} onChange={handleChange} required />

        <label>Job Title</label>
        <select name="job" value={formData.job} onChange={handleChange} required>
          <option value="" disabled>Select a job</option>
          {jobOptions.map((job) => (
            <option key={job.id} value={job.title}>{job.title} ({job.company})</option>
          ))}
        </select>

        <label>Upload Resume</label>
        <input type="file" name="resume" accept=".pdf,.doc,.docx" onChange={handleChange} required />

        <button type="submit" className="submit-btn">Upload</button>
        {message && <p className="upload-message">{message}</p>}
      </form>
    </div>
  );
}
