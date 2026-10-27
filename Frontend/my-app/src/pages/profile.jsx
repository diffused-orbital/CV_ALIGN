import './profile.css';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';

export default function Profile() {
  const navigate = useNavigate();
  const [hasResume, setHasResume] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    full_name: '',
    contact: '',
    cgpa: '',
    degree: '',
    institute: '',
    resume: null,
  });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    axios
      .get(`${API_URL}/candidate/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => {
        const p = res.data;
        if (p && p.complete) {
          setForm((prev) => ({
            ...prev,
            full_name: p.full_name || '',
            contact: p.contact || '',
            cgpa: p.cgpa ?? '',
            degree: p.degree || '',
            institute: p.institute || '',
          }));
          setHasResume(Boolean(p.resume_url));
        }
      })
      .catch((err) => {
        if (err.response?.status === 401) navigate('/login');
      });
  }, [navigate]);

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    setForm((prev) => ({ ...prev, [name]: files ? files[0] : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');
    const token = localStorage.getItem('token');

    const data = new FormData();
    data.append('full_name', form.full_name);
    data.append('contact', form.contact);
    data.append('cgpa', form.cgpa);
    data.append('degree', form.degree);
    data.append('institute', form.institute);
    if (form.resume) data.append('resume', form.resume);

    try {
      await axios.post(`${API_URL}/candidate/profile`, data, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      setHasResume(true);
      setMessage('✅ Profile saved! You can now apply to jobs from your dashboard.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save profile. Please try again.');
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
        <h2 className="form-title">My Profile</h2>

        <label>Full Name</label>
        <input type="text" name="full_name" value={form.full_name} onChange={handleChange} required />

        <label>Contact</label>
        <input type="text" name="contact" value={form.contact} onChange={handleChange} required />

        <label>CGPA</label>
        <input type="text" name="cgpa" value={form.cgpa} onChange={handleChange} required />

        <label>Degree</label>
        <input type="text" name="degree" value={form.degree} onChange={handleChange} required />

        <label>Institute</label>
        <input type="text" name="institute" value={form.institute} onChange={handleChange} required />

        <label>Resume (PDF){hasResume ? ' — a resume is already on file' : ''}</label>
        <input type="file" name="resume" accept=".pdf" onChange={handleChange} required={!hasResume} />

        <button type="submit" className="submit-btn">Save Profile</button>

        {message && <p className="upload-message success">{message}</p>}
        {error && <p className="upload-message error">{error}</p>}
      </form>
    </div>
  );
}
