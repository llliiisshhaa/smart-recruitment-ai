import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext.jsx';
import { ProtectedRoute } from './components/ProtectedRoute.jsx';
import { PublicOnlyRoute } from './components/PublicOnlyRoute.jsx';
import { AppLayout } from './components/AppLayout.jsx';

import { HomePage } from './pages/HomePage.jsx';
import { LoginPage } from './pages/LoginPage.jsx';
import { RegisterPage } from './pages/RegisterPage.jsx';
import { CandidateDashboard } from './pages/CandidateDashboard.jsx';
import { CandidateProfile } from './pages/CandidateProfile.jsx';
import { CandidateResumes } from './pages/CandidateResumes.jsx';
import { CandidateJobs } from './pages/CandidateJobs.jsx';
import { CandidateJobDetail } from './pages/CandidateJobDetail.jsx';
import { CandidateApplications } from './pages/CandidateApplications.jsx';
import { RecruiterDashboard } from './pages/RecruiterDashboard.jsx';
import { RecruiterJobs } from './pages/RecruiterJobs.jsx';
import { NotFoundPage } from './pages/NotFoundPage.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Home Route */}
          <Route path="/" element={<HomePage />} />

          {/* Public Auth Routes (accessible when logged out) */}
          <Route element={<PublicOnlyRoute />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>

          {/* Protected Candidate Routes */}
          <Route element={<ProtectedRoute allowedRoles={['candidate']} />}>
            <Route path="/candidate" element={<AppLayout />}>
              <Route index element={<CandidateDashboard />} />
              <Route path="jobs" element={<CandidateJobs />} />
              <Route path="jobs/:jobId" element={<CandidateJobDetail />} />
              <Route path="applications" element={<CandidateApplications />} />
              <Route path="profile" element={<CandidateProfile />} />
              <Route path="resumes" element={<CandidateResumes />} />
            </Route>
          </Route>

          {/* Protected Recruiter Routes */}
          <Route element={<ProtectedRoute allowedRoles={['recruiter']} />}>
            <Route path="/recruiter" element={<AppLayout />}>
              <Route index element={<RecruiterDashboard />} />
              <Route path="jobs" element={<RecruiterJobs />} />
              <Route path="jobs/:jobId/applications" element={<div className="p-8 text-center text-slate-400">Applicant Listing coming in Phase 6</div>} />
            </Route>
          </Route>

          {/* Fallback 404 Route */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
