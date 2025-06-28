import './jobupload.css';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function JobUpload() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    jobTitle: '',
    companyName: '',
    jobDescription: null,
  });
  const [message, setMessage] = useState('');

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
      setMessage("❌ Unauthorized. Please login again.");
      navigate('/login');
      return;
    }

    const data = new FormData();
    data.append('title', formData.jobTitle);
    data.append('company', formData.companyName);
    data.append('jd_file', formData.jobDescription);

    try {
      const response = await axios.post('http://localhost:8000/job/upload', data, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      console.log(response.data);
      setMessage("✅ Job uploaded successfully!");
      setTimeout(() => navigate('/recruiter-dashboard'), 2000);

    } catch (error) {
      console.error("Upload error:", error);
      setMessage("❌ Failed to upload job. Try again.");
    }
  };

  return (
    <div className="job-upload-container">
      <button className="home-button" onClick={() => navigate('/recruiter-dashboard')}>
        <span className="home-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 960">
            <path d="M400,880 L0,480 L400,80 L471,151 L142,480 L471,809 L400,880 Z" />
          </svg>
        </span>
      </button>

      <form className="job-upload-box" onSubmit={handleSubmit}>
        <h2 className="form-title">Job Upload</h2>

        <label>Job Title</label>
        <input
          type="text"
          name="jobTitle"
          value={formData.jobTitle}
          onChange={handleChange}
          required
        />

        <label>Company Name</label>
        <input
          type="text"
          name="companyName"
          value={formData.companyName}
          onChange={handleChange}
          required
        />

        <label>Job Description (PDF)</label>
        <input
          type="file"
          name="jobDescription"
          accept=".pdf"
          onChange={handleChange}
          required
        />

        <button type="submit" className="submit-btn">Upload</button>
      </form>

      {message && <p className="upload-message">{message}</p>}
    </div>
  );
}
