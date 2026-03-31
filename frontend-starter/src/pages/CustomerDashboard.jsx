import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api';

export default function CustomerDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState([]);
  const [cards, setCards] = useState([]);
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showDeposit, setShowDeposit] = useState(false);
  const [depositAmount, setDepositAmount] = useState('');
  const [selectedAccount, setSelectedAccount] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accRes, cardRes, loanRes] = await Promise.all([
        api.getAccounts(), api.getCards(), api.getLoans()
      ]);
      setAccounts(accRes.data || []);
      setCards(cardRes.data || []);
      setLoans(loanRes.data || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAccount = async () => {
    try {
      await api.createAccount();
      loadData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeposit = async (e) => {
    e.preventDefault();
    try {
      await api.deposit(selectedAccount, parseFloat(depositAmount), 'Online deposit');
      setShowDeposit(false);
      setDepositAmount('');
      loadData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleApplyCard = async (type) => {
    try {
      await api.applyCard(type);
      loadData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const totalBalance = accounts.reduce((sum, a) => sum + parseFloat(a.balance || 0), 0);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="dashboard-header-inner">
          <Link to="/" className="auth-logo">
            <span className="logo-g">G</span><span className="logo-x" style={{fontSize:'18px'}}>x</span><span className="logo-s">S</span>
          </Link>
          <nav className="dashboard-nav">
            <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>Overview</button>
            <button className={activeTab === 'accounts' ? 'active' : ''} onClick={() => setActiveTab('accounts')}>Accounts</button>
            <button className={activeTab === 'cards' ? 'active' : ''} onClick={() => setActiveTab('cards')}>Cards</button>
            <button className={activeTab === 'loans' ? 'active' : ''} onClick={() => setActiveTab('loans')}>Loans</button>
          </nav>
          <div className="dashboard-user">
            <span className="user-greeting">Hi, {user?.fullName?.split(' ')[0]}</span>
            <button onClick={handleLogout} className="btn-logout">Sign out</button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        {activeTab === 'overview' && (
          <div className="dash-overview">
            <div className="dash-welcome">
              <h1>Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'}, {user?.fullName?.split(' ')[0]} 👋</h1>
              <p>Here's your financial overview</p>
            </div>

            <div className="dash-stats-grid">
              <div className="dash-stat-card primary">
                <span className="stat-label">Total Balance</span>
                <span className="stat-value">S${totalBalance.toLocaleString('en-SG', { minimumFractionDigits: 2 })}</span>
                <span className="stat-sub">{accounts.length} account(s)</span>
              </div>
              <div className="dash-stat-card">
                <span className="stat-label">Active Cards</span>
                <span className="stat-value">{cards.filter(c => c.status === 'ACTIVE').length}</span>
                <span className="stat-sub">{cards.length} total</span>
              </div>
              <div className="dash-stat-card">
                <span className="stat-label">Active Loans</span>
                <span className="stat-value">{loans.filter(l => l.status === 'ACTIVE').length}</span>
                <span className="stat-sub">{loans.length} total</span>
              </div>
              <div className="dash-stat-card accent">
                <span className="stat-label">Cashback Earned</span>
                <span className="stat-value">S${cards.reduce((s, c) => s + parseFloat(c.cashbackEarned || 0), 0).toFixed(2)}</span>
                <span className="stat-sub">All time</span>
              </div>
            </div>

            <div className="dash-quick-actions">
              <h3>Quick Actions</h3>
              <div className="quick-action-grid">
                <button onClick={handleCreateAccount} className="quick-action-btn">
                  <span className="qa-icon">🏦</span>
                  <span>Open Account</span>
                </button>
                <button onClick={() => handleApplyCard('FLEXI')} className="quick-action-btn">
                  <span className="qa-icon">💳</span>
                  <span>Apply FlexiCard</span>
                </button>
                <button onClick={() => setActiveTab('loans')} className="quick-action-btn">
                  <span className="qa-icon">💰</span>
                  <span>Apply Loan</span>
                </button>
                <button onClick={() => { if(accounts.length) { setSelectedAccount(accounts[0].id); setShowDeposit(true); } else { alert('Open an account first'); }}} className="quick-action-btn">
                  <span className="qa-icon">📥</span>
                  <span>Deposit</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'accounts' && (
          <div className="dash-section">
            <div className="dash-section-header">
              <h2>Savings Accounts</h2>
              <button onClick={handleCreateAccount} className="btn-dash-action">+ Open New Account</button>
            </div>
            {accounts.length === 0 ? (
              <div className="dash-empty">
                <p>No accounts yet. Open your first GXS Savings Account!</p>
                <button onClick={handleCreateAccount} className="btn-dash-action">Open Account</button>
              </div>
            ) : (
              <div className="dash-cards-grid">
                {accounts.map(acc => (
                  <div key={acc.id} className="dash-account-card">
                    <div className="account-card-top">
                      <span className="account-type">GXS Savings</span>
                      <span className={`account-status ${acc.status.toLowerCase()}`}>{acc.status}</span>
                    </div>
                    <div className="account-number">{acc.accountNumber}</div>
                    <div className="account-balance">
                      <span className="balance-label">Available Balance</span>
                      <span className="balance-amount">S${parseFloat(acc.balance).toLocaleString('en-SG', { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="account-interest">Interest Rate: {acc.interestRate}% p.a.</div>
                    <div className="account-actions">
                      <button onClick={() => { setSelectedAccount(acc.id); setShowDeposit(true); }} className="btn-sm">Deposit</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'cards' && (
          <div className="dash-section">
            <div className="dash-section-header">
              <h2>My Cards</h2>
              <button onClick={() => handleApplyCard('FLEXI')} className="btn-dash-action">+ Apply for FlexiCard</button>
            </div>
            {cards.length === 0 ? (
              <div className="dash-empty">
                <p>No cards yet. Apply for a GXS FlexiCard!</p>
                <button onClick={() => handleApplyCard('FLEXI')} className="btn-dash-action">Apply Now</button>
              </div>
            ) : (
              <div className="dash-cards-grid">
                {cards.map(card => (
                  <div key={card.id} className="dash-card-item">
                    <div className="card-visual">
                      <span className="card-brand">GXS</span>
                      <span className="card-number">•••• •••• •••• {card.cardNumberLast4}</span>
                      <span className="card-type-badge">{card.cardType}</span>
                    </div>
                    <div className="card-details">
                      <div className="card-detail-row">
                        <span>Status</span>
                        <span className={`status-badge ${card.status.toLowerCase()}`}>{card.status}</span>
                      </div>
                      {card.cardType === 'FLEXI' && (
                        <>
                          <div className="card-detail-row">
                            <span>Credit Limit</span>
                            <span>S${parseFloat(card.creditLimit).toFixed(2)}</span>
                          </div>
                          <div className="card-detail-row">
                            <span>Cashback Earned</span>
                            <span className="cashback">S${parseFloat(card.cashbackEarned).toFixed(2)}</span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'loans' && (
          <div className="dash-section">
            <div className="dash-section-header">
              <h2>My Loans</h2>
            </div>
            {loans.length === 0 ? (
              <div className="dash-empty">
                <p>No active loans. Need a cash boost?</p>
              </div>
            ) : (
              <div className="dash-cards-grid">
                {loans.map(loan => (
                  <div key={loan.id} className="dash-loan-card">
                    <div className="loan-card-top">
                      <span className="loan-type">{loan.loanType.replace('_', ' ')}</span>
                      <span className={`loan-status ${loan.status.toLowerCase()}`}>{loan.status}</span>
                    </div>
                    {loan.loanName && <div className="loan-name">"{loan.loanName}"</div>}
                    <div className="loan-amount">S${parseFloat(loan.amount).toLocaleString('en-SG', { minimumFractionDigits: 2 })}</div>
                    <div className="loan-details">
                      <div className="loan-detail-row">
                        <span>Outstanding</span>
                        <span>S${parseFloat(loan.outstandingAmount).toLocaleString('en-SG', { minimumFractionDigits: 2 })}</span>
                      </div>
                      <div className="loan-detail-row">
                        <span>Interest Rate</span>
                        <span>{loan.interestRate}% p.a.</span>
                      </div>
                      <div className="loan-detail-row">
                        <span>Monthly Payment</span>
                        <span>S${parseFloat(loan.monthlyPayment).toFixed(2)}</span>
                      </div>
                      <div className="loan-detail-row">
                        <span>Tenure</span>
                        <span>{loan.tenureMonths} months</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {showDeposit && (
        <div className="modal-overlay" onClick={() => setShowDeposit(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h3>Make a Deposit</h3>
            <form onSubmit={handleDeposit}>
              <div className="form-group">
                <label>Amount (S$)</label>
                <input type="number" step="0.01" min="0.01" value={depositAmount}
                  onChange={e => setDepositAmount(e.target.value)} placeholder="0.00" required />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowDeposit(false)} className="btn-modal-cancel">Cancel</button>
                <button type="submit" className="btn-modal-confirm">Deposit</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
