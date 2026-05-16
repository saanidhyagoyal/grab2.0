import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api';

export default function EmployeeDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [contacts, setContacts] = useState([]);
  const [promotions, setPromotions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [contactRes, promoRes] = await Promise.all([
        api.getContactSubmissions(),
        api.getPromotions(),
      ]);
      setContacts(contactRes.data || []);
      setPromotions(promoRes.data || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading employee portal...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-page employee-dashboard">
      <header className="dashboard-header employee">
        <div className="dashboard-header-inner">
          <Link to="/" className="auth-logo">
            <span className="logo-g">G</span><span className="logo-x" style={{fontSize:'18px'}}>x</span><span className="logo-s">S</span>
          </Link>
          <nav className="dashboard-nav">
            <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>Overview</button>
            <button className={activeTab === 'contacts' ? 'active' : ''} onClick={() => setActiveTab('contacts')}>Support Tickets</button>
            <button className={activeTab === 'promotions' ? 'active' : ''} onClick={() => setActiveTab('promotions')}>Promotions</button>
          </nav>
          <div className="dashboard-user">
            <span className="user-role-tag">Employee</span>
            <span className="user-greeting">{user?.fullName}</span>
            <button onClick={handleLogout} className="btn-logout">Sign out</button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        {activeTab === 'overview' && (
          <div className="dash-overview">
            <div className="dash-welcome">
              <h1>Employee Portal 🏢</h1>
              <p>Welcome back, {user?.fullName}. Department: {user?.department || 'N/A'}</p>
            </div>

            <div className="dash-stats-grid">
              <div className="dash-stat-card employee-primary">
                <span className="stat-label">Support Tickets</span>
                <span className="stat-value">{contacts.length}</span>
                <span className="stat-sub">{contacts.filter(c => c.status === 'NEW').length} new</span>
              </div>
              <div className="dash-stat-card">
                <span className="stat-label">Active Promotions</span>
                <span className="stat-value">{promotions.filter(p => p.isActive).length}</span>
                <span className="stat-sub">of {promotions.length} total</span>
              </div>
              <div className="dash-stat-card">
                <span className="stat-label">Employee ID</span>
                <span className="stat-value" style={{fontSize:'16px'}}>{user?.employeeId || 'N/A'}</span>
                <span className="stat-sub">{user?.department}</span>
              </div>
            </div>

            <div className="dash-section">
              <h3>Recent Support Tickets</h3>
              {contacts.slice(0, 5).map(contact => (
                <div key={contact.id} className="ticket-card">
                  <div className="ticket-header">
                    <span className="ticket-name">{contact.name}</span>
                    <span className={`ticket-status ${contact.status.toLowerCase().replace('_', '-')}`}>{contact.status}</span>
                  </div>
                  <div className="ticket-subject">{contact.subject || 'No subject'}</div>
                  <div className="ticket-preview">{contact.message.substring(0, 120)}...</div>
                  <div className="ticket-meta">
                    <span>{contact.email}</span>
                    <span>{new Date(contact.createdAt).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'contacts' && (
          <div className="dash-section">
            <div className="dash-section-header">
              <h2>All Support Tickets</h2>
              <span className="ticket-count">{contacts.length} total</span>
            </div>
            {contacts.length === 0 ? (
              <div className="dash-empty"><p>No support tickets yet.</p></div>
            ) : (
              <div className="tickets-list">
                {contacts.map(contact => (
                  <div key={contact.id} className="ticket-card">
                    <div className="ticket-header">
                      <span className="ticket-name">{contact.name}</span>
                      <span className={`ticket-status ${contact.status.toLowerCase().replace('_', '-')}`}>{contact.status}</span>
                    </div>
                    <div className="ticket-subject">{contact.subject || 'General Inquiry'}</div>
                    <div className="ticket-message">{contact.message}</div>
                    <div className="ticket-meta">
                      <span>📧 {contact.email}</span>
                      <span>📅 {new Date(contact.createdAt).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'promotions' && (
          <div className="dash-section">
            <div className="dash-section-header">
              <h2>Active Promotions</h2>
            </div>
            <div className="dash-cards-grid">
              {promotions.map(promo => (
                <div key={promo.id} className="promo-card">
                  <span className="promo-badge">{promo.badgeText}</span>
                  <h3>{promo.title}</h3>
                  <p>{promo.description}</p>
                  <div className="promo-meta">
                    <span>Valid: {promo.validFrom} → {promo.validTo}</span>
                    <span className={promo.isActive ? 'promo-active' : 'promo-inactive'}>
                      {promo.isActive ? '✅ Active' : '⏸ Inactive'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
