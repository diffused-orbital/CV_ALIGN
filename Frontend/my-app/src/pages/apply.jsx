import './apply.css';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function CandidateUpload() {
  const navigate = useNavigate();
  const [name, setName] = useState(''); // fetched from backend
  const [jobOptions, setJobOptions] = useState([]);
  const [formData, setFormData] = useState({
    cgpa: '',
    degree: '',
    institute: '',
    job: '',
    resume: null,
  });

  useEffect(() => {
    // Fetch user name and job list from backend (mocked here)
    setName('John Doe');

    // Replace with API call
    setJobOptions(['Frontend Developer', 'Backend Engineer', 'AI Researcher']);
  }, []);

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: files ? files[0] : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // You can send formData and formData.resume to backend
    console.log(formData);
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
        <input
          type="text"
          name="cgpa"
          value={formData.cgpa}
          onChange={handleChange}
          required
        />

        <label>Degree</label>
        <input
          type="text"
          name="degree"
          value={formData.degree}
          onChange={handleChange}
          required
        />

        <label>Institute</label>
        <input
          type="text"
          name="institute"
          value={formData.institute}
          onChange={handleChange}
          required
        />

        <label>Job Title</label>
        <select
          name="job"
          value={formData.job}
          onChange={handleChange}
          required
        >
          <option value="" disabled>Select a job</option>
          {jobOptions.map((job, idx) => (
            <option key={idx} value={job}>{job}</option>
          ))}
        </select>

        <label>Upload Resume</label>
        <input
          type="file"
          name="resume"
          accept=".pdf,.doc,.docx"
          onChange={handleChange}
          required
        />

        <button type="submit" className="submit-btn">Upload</button>
      </form>
    </div>
  );
}
