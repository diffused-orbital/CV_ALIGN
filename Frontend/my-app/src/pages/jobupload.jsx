import './jobupload.css';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function JobUpload() {
  const navigate=useNavigate();
  const [formData, setFormData] = useState({
    jobTitle: '',
    companyName: '',
    jobDescription: null,
  });

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: files ? files[0] : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you can send formData to your backend
    console.log(formData);
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
    </div>
  );
}
