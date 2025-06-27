import { Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/login';
import Register from './pages/register';  
import CandidateDashboard from './pages/candidatedashboard';


export default function App() {
  return (
    <Routes>
      <Route index element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard/candidate" element={<CandidateDashboard />} />
    </Routes>
  );
}
