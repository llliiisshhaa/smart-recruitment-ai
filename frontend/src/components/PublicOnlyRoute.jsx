import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/useAuth.js';
import { LoadingSpinner } from './LoadingSpinner.jsx';

export function PublicOnlyRoute() {
  const { user, loading } = useAuth();

  // Wait for session restore
  if (loading) {
    return <LoadingSpinner text="Checking authentication..." fullScreen />;
  }

  if (user) {
    if (user.role === 'recruiter') {
      return <Navigate to="/recruiter" replace />;
    }
    if (user.role === 'candidate') {
      return <Navigate to="/candidate" replace />;
    }
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
