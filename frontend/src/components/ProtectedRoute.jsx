import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/useAuth.js';
import { LoadingSpinner } from './LoadingSpinner.jsx';

export function ProtectedRoute({ allowedRoles = ['candidate'] }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Wait for session restore before deciding to redirect
  if (loading) {
    return <LoadingSpinner text="Checking authentication..." fullScreen />;
  }

  // Logged-out users go to /login
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Role mismatch handling
  if (!allowedRoles.includes(user.role)) {
    if (user.role === 'candidate') {
      return <Navigate to="/candidate" replace />;
    }
    if (user.role === 'recruiter') {
      return <Navigate to="/recruiter" replace />;
    }
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
