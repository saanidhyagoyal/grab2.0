import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import App from './App';
import LoginPage from './pages/LoginPage';
import CustomerSignupPage from './pages/CustomerSignupPage';
import EmployeeSignupPage from './pages/EmployeeSignupPage';
import CustomerDashboard from './pages/CustomerDashboard';
import EmployeeDashboard from './pages/EmployeeDashboard';
import './styles.css';

function ProtectedRoute({ children, role }) {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (role && user?.role !== role) return <Navigate to="/" replace />;
  return children;
}

function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup/customer" element={<CustomerSignupPage />} />
      <Route path="/signup/employee" element={<EmployeeSignupPage />} />
      <Route path="/dashboard" element={
        <ProtectedRoute role="CUSTOMER"><CustomerDashboard /></ProtectedRoute>
      } />
      <Route path="/employee/dashboard" element={
        <ProtectedRoute role="EMPLOYEE"><EmployeeDashboard /></ProtectedRoute>
      } />
    </Routes>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
