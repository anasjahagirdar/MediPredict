import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';


function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="auth-loader">
        <div className="auth-loader__spinner" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}


export default ProtectedRoute;
