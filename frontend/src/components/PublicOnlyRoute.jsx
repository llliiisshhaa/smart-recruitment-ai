import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/useAuth.js';
import { LoadingSpinner } from './LoadingSpinner.jsx';

export function PublicOnlyRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner text="Checking authentication..." fullScreen />;
  }

  if (user && user.role === 'candidate') {
    return <Navigate to="/candidate" replace />;
  }

  return <Outlet />;
}
