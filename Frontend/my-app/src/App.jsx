import { Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/login';
import Register from './pages/register';  
import CandidateDashboard from './pages/candidatedashboard';
import Profile from './pages/profile';
import JobUpload from './pages/jobupload';
import RecruiterDashboard from './pages/recruiterdashboard';
import JobDetails from './pages/cvfetch';

export default function App() {
  return (
    <Routes>
      <Route index element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/candidate-dashboard" element={<CandidateDashboard />} />
      <Route path="/candidate/profile" element={<Profile />} />
      <Route path="/upload-job" element={<JobUpload />} />
      <Route path="/recruiter-dashboard" element={<RecruiterDashboard />} />
      <Route path="/recruiter/job/:jobId" element={<JobDetails />} />
    </Routes>
  );
}
