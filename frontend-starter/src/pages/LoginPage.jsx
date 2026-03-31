import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await login(email, password);
      if (res.data.role === 'EMPLOYEE') {
        navigate('/employee/dashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <Link to="/" className="auth-logo">
            <span className="logo-g">G</span><span className="logo-x" style={{fontSize:'22px'}}>x</span><span className="logo-s">S</span>
          </Link>
          <h1>Welcome back</h1>
          <p className="auth-subtitle">Sign in to your GXS account</p>
        </div>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>
          <button type="submit" className="btn-auth-submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="auth-links">
          <p>Don't have an account?</p>
          <div className="auth-links-row">
            <Link to="/signup/customer" className="auth-link">Sign up as Customer</Link>
            <span className="auth-divider">|</span>
            <Link to="/signup/employee" className="auth-link">Sign up as Employee</Link>
          </div>
        </div>

        <div className="auth-demo-creds">
          <p>Demo accounts:</p>
          <div className="demo-cred">
            <span>Customer:</span> alex@demo.com / demo1234
          </div>
          <div className="demo-cred">
            <span>Employee:</span> sarah@gxs.com.sg / admin1234
          </div>
        </div>
      </div>
    </div>
  );
}
