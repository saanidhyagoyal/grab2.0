import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function EmployeeSignupPage() {
  const [form, setForm] = useState({
    fullName: '', email: '', phone: '', password: '', confirmPassword: '',
    employeeId: '', department: '',
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
    if (!form.employeeId) {
      setError('Employee ID is required');
      return;
    }

    setLoading(true);
    try {
      await register({
        fullName: form.fullName,
        email: form.email,
        phone: form.phone,
        password: form.password,
        role: 'EMPLOYEE',
        employeeId: form.employeeId,
        department: form.department,
      });
      navigate('/employee/dashboard');
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
          <h1>Employee Portal</h1>
          <p className="auth-subtitle">Register as a GXS Bank employee</p>
          <span className="auth-role-badge employee">Employee</span>
        </div>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="emp-name">Full Name</label>
              <input id="emp-name" name="fullName" type="text" value={form.fullName}
                onChange={handleChange} placeholder="Full Name" required />
            </div>
            <div className="form-group">
              <label htmlFor="emp-id">Employee ID</label>
              <input id="emp-id" name="employeeId" type="text" value={form.employeeId}
                onChange={handleChange} placeholder="GXS-EMP-XXX" required />
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="emp-dept">Department</label>
            <select id="emp-dept" name="department" value={form.department} onChange={handleChange} required>
              <option value="">Select department</option>
              <option value="Customer Service">Customer Service</option>
              <option value="Risk & Compliance">Risk & Compliance</option>
              <option value="Engineering">Engineering</option>
              <option value="Product">Product</option>
              <option value="Marketing">Marketing</option>
              <option value="Operations">Operations</option>
              <option value="Finance">Finance</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="emp-email">Work Email</label>
            <input id="emp-email" name="email" type="email" value={form.email}
              onChange={handleChange} placeholder="name@gxs.com.sg" required />
          </div>
          <div className="form-group">
            <label htmlFor="emp-phone">Phone Number</label>
            <input id="emp-phone" name="phone" type="tel" value={form.phone}
              onChange={handleChange} placeholder="+65 9XXX XXXX" required />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="emp-password">Password</label>
              <input id="emp-password" name="password" type="password" value={form.password}
                onChange={handleChange} placeholder="Min 8 characters" required />
            </div>
            <div className="form-group">
              <label htmlFor="emp-confirm">Confirm Password</label>
              <input id="emp-confirm" name="confirmPassword" type="password" value={form.confirmPassword}
                onChange={handleChange} placeholder="Confirm password" required />
            </div>
          </div>
          <button type="submit" className="btn-auth-submit employee" disabled={loading}>
            {loading ? 'Creating Account...' : 'Register as Employee'}
          </button>
        </form>

        <div className="auth-links">
          <p>Already have an account? <Link to="/login" className="auth-link">Sign in</Link></p>
        </div>
      </div>
    </div>
  );
}
