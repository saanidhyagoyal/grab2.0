import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function CustomerSignupPage() {
  const [form, setForm] = useState({
    fullName: '', email: '', phone: '', password: '', confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      await register({
        fullName: form.fullName,
        email: form.email,
        phone: form.phone,
        password: form.password,
        role: 'CUSTOMER',
      });
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Registration failed');
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
          <h1>Create Account</h1>
          <p className="auth-subtitle">Join GXS Bank as a customer</p>
          <span className="auth-role-badge customer">Customer</span>
        </div>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="signup-name">Full Name</label>
            <input id="signup-name" name="fullName" type="text" value={form.fullName}
              onChange={handleChange} placeholder="Enter your full name" required />
          </div>
          <div className="form-group">
            <label htmlFor="signup-email">Email</label>
            <input id="signup-email" name="email" type="email" value={form.email}
              onChange={handleChange} placeholder="Enter your email" required />
          </div>
          <div className="form-group">
            <label htmlFor="signup-phone">Phone Number</label>
            <input id="signup-phone" name="phone" type="tel" value={form.phone}
              onChange={handleChange} placeholder="+65 9XXX XXXX" required />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="signup-password">Password</label>
              <input id="signup-password" name="password" type="password" value={form.password}
                onChange={handleChange} placeholder="Min 8 characters" required />
            </div>
            <div className="form-group">
              <label htmlFor="signup-confirm">Confirm Password</label>
              <input id="signup-confirm" name="confirmPassword" type="password" value={form.confirmPassword}
                onChange={handleChange} placeholder="Confirm password" required />
            </div>
          </div>
          <button type="submit" className="btn-auth-submit" disabled={loading}>
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="auth-links">
          <p>Already have an account? <Link to="/login" className="auth-link">Sign in</Link></p>
        </div>
      </div>
    </div>
  );
}
