import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api';

export default function CustomerDashboard() {
  const { user, logout, refreshUser, kycStatus } = useAuth();
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState([]);
  const [cards, setCards] = useState([]);
  const [loans, setLoans] = useState([]);
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [fds, setFds] = useState([]);
  const [billHistory, setBillHistory] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [activeSubTab, setActiveSubTab] = useState('');
  const [showDeposit, setShowDeposit] = useState(false);

  // Modals
  const [modal, setModal] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [formData, setFormData] = useState({});

  const loadData = useCallback(async () => {
    try {
      const [accRes, cardRes, loanRes, notifCount] = await Promise.all([
        api.getAccounts(), api.getCards(), api.getLoans(), api.getUnreadCount()
      ]);
      setAccounts(accRes.data || []);
      setCards(cardRes.data || []);
      setLoans(loanRes.data || []);
      setUnreadCount(notifCount.data?.count || 0);
      refreshUser();
    } catch (err) { console.error('Failed to load:', err); }
    finally { setLoading(false); }
  }, [refreshUser]);

  useEffect(() => { loadData(); }, [loadData]);

  const loadTabData = async (tab) => {
    setActiveTab(tab);
    try {
      if (tab === 'transfers') { const r = await api.getBeneficiaries(); setBeneficiaries(r.data || []); }
      if (tab === 'notifications') { const r = await api.getNotifications(); setNotifications(r.data || []); }
      if (tab === 'deposits') { const r = await api.getFDs(); setFds(r.data || []); }
      if (tab === 'billpay') { const r = await api.getBillHistory(); setBillHistory(r.data || []); }
      if (tab === 'accounts' && accounts.length > 0) {
        const r = await api.getMiniStatement(accounts[0].id); setTransactions(r.data || []);
      }
    } catch (err) { console.error(err); }
  };

  const handleAction = async (action, ...args) => {
    try {
      switch (action) {
        case 'createAccount': await api.createAccount(); break;
        case 'deposit': await api.deposit(args[0], parseFloat(args[1]), args[2]); break;
        case 'transfer': await api.transfer(args[0], args[1], parseFloat(args[2]), args[3]); break;
        case 'applyCard': await api.applyCard(args[0]); alert('✅ Card application submitted for approval! Check back shortly.'); break;
        case 'applyLoan': await api.applyLoan(args[0]); alert('✅ Loan application submitted for review! You will be notified once approved.'); break;
        case 'freezeCard': await api.toggleFreezeCard(args[0]); break;
        case 'cardSettings': await api.updateCardSettings(args[0], args[1]); break;
        case 'repayLoan': await api.repayLoan(args[0], parseFloat(args[1])); break;
        case 'submitKyc': await api.submitKyc(args[0], args[1]); alert('KYC submitted for review!'); break;
        case 'addBeneficiary': await api.addBeneficiary(args[0]); break;
        case 'deleteBeneficiary': await api.deleteBeneficiary(args[0]); break;
        case 'payBill': await api.payBill(args[0]); alert('✅ Bill paid successfully! Transaction recorded.'); break;
        case 'createFD': {
          const fdAccountId = args[0].sourceAccountId || accounts[0]?.id;
          await api.createFD({ ...args[0], sourceAccountId: fdAccountId });
          alert('✅ Fixed Deposit created successfully! View it under the Deposits tab.');
          break;
        }
        case 'breakFD': await api.breakFD(args[0]); alert('FD broken, amount credited!'); break;
        case 'markRead': await api.markNotificationRead(args[0]); break;
        case 'markAllRead': await api.markAllNotificationsRead(); break;
        default: break;
      }
      setModal(null); setFormData({});
      loadData(); loadTabData(activeTab);
    } catch (err) { alert(err.message); }
  };

  const totalBalance = accounts.reduce((s, a) => s + parseFloat(a.balance || 0), 0);
  const kycOk = kycStatus === 'VERIFIED';

  if (loading) return <div className="dashboard-loading"><div className="spinner"></div><p>Loading your dashboard...</p></div>;

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="dashboard-header-inner">
          <Link to="/" className="auth-logo"><span className="logo-g">G</span><span className="logo-x" style={{ fontSize: '18px' }}>x</span><span className="logo-s">S</span></Link>
          <nav className="dashboard-nav">
            <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => {setActiveTab('overview'); setActiveSubTab('');}}>Overview</button>
            <div className={`nav-dropdown ${activeTab === 'accounts' || activeTab === 'transfers' || activeTab === 'billpay' ? 'active' : ''}`}>
              <button onClick={() => {loadTabData('accounts'); setActiveSubTab('');}}>Accounts & Transfers</button>
              <div className="dropdown-menu">
                <button onClick={() => { loadTabData('accounts'); }}>My Accounts</button>
                <button onClick={() => { if (accounts.length) { setModal('transfer'); } else { alert('Open an account first'); } }}>Send Money</button>
                <button onClick={() => { loadTabData('billpay'); }}>Pay Bills</button>
              </div>
            </div>
            
            <div className={`nav-dropdown ${activeTab === 'deposits' ? 'active' : ''}`}>
              <button onClick={() => {loadTabData('deposits'); setActiveSubTab('');}}>Deposits</button>
              <div className="dropdown-menu">
                <button onClick={() => { loadTabData('deposits'); }}>Fixed Deposits</button>
                <button onClick={() => { setModal('savingGoals'); }}>Saving Goals</button>
              </div>
            </div>

            <button className={activeTab === 'cards' ? 'active' : ''} onClick={() => {loadTabData('cards'); setActiveSubTab('');}}>Cards</button>
            <button className={activeTab === 'loans' ? 'active' : ''} onClick={() => {loadTabData('loans'); setActiveSubTab('');}}>Loans</button>
            
            <div className={`nav-dropdown ${activeTab === 'profile' || activeTab === 'notifications' ? 'active' : ''}`}>
              <button onClick={() => {loadTabData('profile'); setActiveSubTab('');}}>Profile</button>
              <div className="dropdown-menu">
                <button onClick={() => { loadTabData('profile'); }}>My Details</button>
                <button onClick={() => { loadTabData('profile'); setModal('kyc'); }}>KYC Verification</button>
                <button onClick={() => { loadTabData('notifications'); }}>Notifications</button>
              </div>
            </div>
          </nav>
          <div className="dashboard-user">
            <span className="user-greeting">Hi, {user?.fullName?.split(' ')[0]}</span>
            <button onClick={() => { logout(); navigate('/'); }} className="btn-logout">Sign out</button>
          </div>
        </div>
      </header>

      {/* KYC Banner */}
      {(kycStatus === 'UNVERIFIED' || kycStatus === 'REJECTED') && (
        <div style={{ background: 'linear-gradient(90deg, #ff5252, #c62828)', color: '#fff', padding: '14px 24px', textAlign: 'center', fontWeight: 600 }}>
          ⚠️ Verify your identity to unlock all features.
          <button onClick={() => setModal('kyc')} style={{ marginLeft: 12, padding: '6px 16px', background: '#fff', color: '#c62828', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 700 }}>Verify Now</button>
        </div>
      )}
      {kycStatus === 'PENDING_REVIEW' && (
        <div style={{ background: 'linear-gradient(90deg, #ff9800, #ef6c00)', color: '#fff', padding: '14px 24px', textAlign: 'center', fontWeight: 600 }}>⏳ KYC documents are under review. Check back soon.</div>
      )}

      <main className="dashboard-main">
        {/* ===== OVERVIEW ===== */}
        {activeTab === 'overview' && (
          <div className="dash-overview">
            <div className="dash-welcome">
              <h1>Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'}, {user?.fullName?.split(' ')[0]} 👋</h1>
              <p>Here's your financial snapshot</p>
            </div>
            <div className="dash-stats-grid">
              <div className="dash-stat-card primary"><span className="stat-label">Total Balance</span><span className="stat-value">S${totalBalance.toLocaleString('en-SG', { minimumFractionDigits: 2 })}</span><span className="stat-sub">{accounts.length} account(s)</span></div>
              <div className="dash-stat-card"><span className="stat-label">Active Cards</span><span className="stat-value">{cards.filter(c => c.status === 'ACTIVE').length}</span><span className="stat-sub">{cards.filter(c => c.status === 'PENDING').length} pending</span></div>
              <div className="dash-stat-card"><span className="stat-label">Active Loans</span><span className="stat-value">{loans.filter(l => l.status === 'ACTIVE').length}</span><span className="stat-sub">{loans.filter(l => l.status === 'PENDING').length} pending</span></div>
              <div className="dash-stat-card accent"><span className="stat-label">Cashback</span><span className="stat-value">S${cards.reduce((s, c) => s + parseFloat(c.cashbackEarned || 0), 0).toFixed(2)}</span><span className="stat-sub">Rewards</span></div>
            </div>
            <div className="dash-quick-actions"><h3>Quick Actions</h3>
              <div className="quick-action-grid">
                <button onClick={() => kycOk ? setModal('createAccount') : alert('Your account is pending KYC verification. Please wait for approval.')} className="quick-action-btn"><span className="qa-icon">🏦</span><span>Open Account</span></button>
                <button onClick={() => accounts.length ? setModal('transfer') : alert('Open an account first')} className="quick-action-btn"><span className="qa-icon">💸</span><span>Transfer</span></button>
                <button onClick={() => kycOk ? setModal('applyCard') : alert('Verify KYC first')} className="quick-action-btn"><span className="qa-icon">💳</span><span>Apply Card</span></button>
                <button onClick={() => kycOk ? setModal('applyLoan') : alert('Verify KYC first')} className="quick-action-btn"><span className="qa-icon">💰</span><span>Get Loan</span></button>
              </div>
            </div>
          </div>
        )}

        {/* ===== ACCOUNTS ===== */}
        {activeTab === 'accounts' && (
          <div className="dash-section">
            <div className="dash-section-header"><h2>My Accounts</h2>
              <button onClick={() => kycOk ? setModal('createAccount') : alert('Your account is pending KYC verification. Please wait for approval.')} className="btn-dash-action">+ Open New Account</button></div>
            <div className="dash-cards-grid">
              {accounts.map(acc => (
                <div key={acc.id} className="dash-account-card">
                  <div className="account-card-top"><span className="account-type">{acc.accountType || 'Savings'}</span><span className={`account-status ${(acc.status || '').toLowerCase()}`}>{acc.status}</span></div>
                  <div className="account-number">{acc.accountNumber}</div>
                  <div style={{ fontSize: '11px', color: '#888', marginTop: 4 }}>IFSC: {acc.ifscCode} · {acc.branchName}</div>
                  <div className="account-balance"><span className="balance-label">Balance</span><span className="balance-amount">S${parseFloat(acc.balance).toLocaleString('en-SG', { minimumFractionDigits: 2 })}</span></div>
                  <div className="account-actions">
                    <button onClick={() => { setSelectedAccount(acc.id); setModal('deposit'); }} className="btn-sm">Deposit</button>
                    <button onClick={() => { setSelectedAccount(acc.id); setModal('transfer'); }} className="btn-sm">Transfer</button>
                    <button onClick={async () => { const r = await api.getMiniStatement(acc.id); setTransactions(r.data || []); setSelectedAccount(acc.id); setModal('statement'); }} className="btn-sm">Statement</button>
                  </div>
                </div>
              ))}
              {accounts.length === 0 && <div className="profile-card" style={{ gridColumn: '1/-1', textAlign: 'center', color: 'var(--color-text-muted)', padding: 40 }}>No accounts found. Open a savings account to get started with GXS Bank!</div>}
            </div>
          </div>
        )}

        {/* ===== TRANSFERS ===== */}
        {activeTab === 'transfers' && (
          <div className="dash-section">
            <div className="dash-section-header"><h2>Transfers & Beneficiaries</h2>
              <button onClick={() => setModal('addBeneficiary')} className="btn-dash-action">+ Add Beneficiary</button></div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
              <button onClick={() => accounts.length ? setModal('transfer') : alert('Open an account first')} className="btn-dash-action">💸 Quick Transfer</button>
            </div>
            <h3 style={{ marginTop: 16 }}>Your Beneficiaries</h3>
            <div className="dash-cards-grid">
              {beneficiaries.map(b => (
                <div key={b.id} className="dash-account-card">
                  <div className="account-card-top"><span className="account-type">{b.beneficiaryName}</span></div>
                  <div className="account-number">{b.accountNumber}</div>
                  <div style={{ fontSize: '12px', color: '#888' }}>IFSC: {b.ifscCode} · {b.bankName || 'GXS Bank'}</div>
                  {b.nickname && <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>Alias: {b.nickname}</div>}
                  <div className="account-actions" style={{ marginTop: 12 }}>
                    <button className="btn-sm" onClick={() => { setSelectedAccount(accounts[0]?.id); setFormData({ toAccount: b.accountNumber }); setModal('transfer'); }}>Transfer</button>
                    <button className="btn-sm" onClick={() => handleAction('deleteBeneficiary', b.id)}>Remove</button>
                  </div>
                </div>
              ))}
              {beneficiaries.length === 0 && <p style={{ color: '#999' }}>No beneficiaries added yet.</p>}
            </div>
          </div>
        )}

        {/* ===== CARDS ===== */}
        {activeTab === 'cards' && (
          <div className="dash-section">
            <div className="dash-section-header"><h2>My Cards</h2><button onClick={() => kycOk ? setModal('applyCard') : alert('Verify KYC first')} className="btn-dash-action">+ Apply for Card</button></div>
            <div className="dash-cards-grid">
              {cards.map(card => (
                <div key={card.id} className="dash-card-item">
                  <div className="card-visual" style={{ background: card.cardNetwork === 'VISA' ? 'linear-gradient(135deg,#1a237e,#283593)' : card.cardNetwork === 'MASTERCARD' ? 'linear-gradient(135deg,#b71c1c,#e53935)' : 'linear-gradient(135deg,#004d40,#00695c)' }}>
                    <span className="card-brand">{card.cardNetwork || 'GXS'}</span>
                    <span className="card-number">•••• •••• •••• {card.cardNumberLast4}</span>
                    <span className="card-type-badge">{card.cardType}</span>
                    <span style={{ position: 'absolute', bottom: 8, right: 12, fontSize: 11, opacity: 0.8 }}>Exp: {card.expiryDate}</span>
                  </div>
                  <div className="card-details">
                    <div className="card-detail-row"><span>Status</span><span className={`status-badge ${(card.status || '').toLowerCase()}`}>{card.status}</span></div>
                    <div className="card-detail-row"><span>Holder</span><span>{card.cardHolderName}</span></div>
                    {(card.cardType === 'CREDIT' || card.cardType === 'FLEXI' || card.cardType === 'PREPAID') && <div className="card-detail-row"><span>Limit</span><span>S${parseFloat(card.creditLimit || 0).toLocaleString()}</span></div>}
                    <div className="card-detail-row"><span>International</span><span>{card.isInternationalEnabled ? '✅' : '❌'}</span></div>
                    <div className="card-detail-row"><span>Online</span><span>{card.isOnlineEnabled ? '✅' : '❌'}</span></div>
                    <div className="card-detail-row"><span>Contactless</span><span>{card.isContactlessEnabled ? '✅' : '❌'}</span></div>
                  </div>
                  <div className="account-actions" style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {card.status === 'ACTIVE' && <button className="btn-sm" onClick={() => handleAction('freezeCard', card.id)}>Freeze</button>}
                    {card.status === 'FROZEN' && <button className="btn-sm" onClick={() => handleAction('freezeCard', card.id)}>Unfreeze</button>}
                    {card.status === 'ACTIVE' && <>
                      <button className="btn-sm" onClick={() => handleAction('cardSettings', card.id, { isInternationalEnabled: !card.isInternationalEnabled })}>{card.isInternationalEnabled ? 'Disable' : 'Enable'} Intl</button>
                      <button className="btn-sm" onClick={() => handleAction('cardSettings', card.id, { isContactlessEnabled: !card.isContactlessEnabled })}>{card.isContactlessEnabled ? 'Disable' : 'Enable'} Tap</button>
                    </>}
                  </div>
                </div>
              ))}
              {cards.length === 0 && <div className="profile-card" style={{ gridColumn: '1/-1', textAlign: 'center', color: 'var(--color-text-muted)', padding: 40 }}>You don't have any cards yet. Apply for a Debit or Credit card to get started!</div>}
            </div>
          </div>
        )}

        {/* ===== LOANS ===== */}
        {activeTab === 'loans' && (
          <div className="dash-section">
            <div className="dash-section-header"><h2>My Loans</h2><button onClick={() => kycOk ? setModal('applyLoan') : alert('Verify KYC first')} className="btn-dash-action">+ Apply for Loan</button></div>
            <div className="dash-cards-grid">
              {loans.map(loan => (
                <div key={loan.id} className="dash-loan-card">
                  <div className="loan-card-top"><span className="loan-type">{loan.loanType}</span><span className={`loan-status ${(loan.status || '').toLowerCase()}`}>{loan.status}</span></div>
                  <div className="loan-amount">S${parseFloat(loan.amount).toLocaleString()}</div>
                  {loan.loanName && <div style={{ fontSize: 13, color: '#666', marginBottom: 8 }}>{loan.loanName}</div>}
                  <div className="loan-details">
                    <div className="loan-detail-row"><span>Outstanding</span><span>S${parseFloat(loan.outstandingAmount).toLocaleString()}</span></div>
                    <div className="loan-detail-row"><span>Monthly EMI</span><span>S${parseFloat(loan.monthlyPayment || 0).toFixed(2)}</span></div>
                    <div className="loan-detail-row"><span>Rate</span><span>{loan.interestRate}% p.a.</span></div>
                    <div className="loan-detail-row"><span>EMIs Paid</span><span>{loan.emisPaid}/{loan.totalEmis}</span></div>
                    {loan.nextEmiDate && <div className="loan-detail-row"><span>Next EMI</span><span>{loan.nextEmiDate}</span></div>}
                  </div>
                  {loan.status === 'ACTIVE' && <div className="account-actions" style={{ marginTop: 12 }}>
                    <button className="btn-sm" onClick={() => handleAction('repayLoan', loan.id, loan.monthlyPayment)}>Pay EMI (S${parseFloat(loan.monthlyPayment || 0).toFixed(2)})</button>
                  </div>}
                  {loan.status === 'PENDING' && <div style={{ marginTop: 12, fontSize: 13, color: '#ef6c00' }}>⏳ Awaiting approval</div>}
                </div>
              ))}
              {loans.length === 0 && <div className="profile-card" style={{ gridColumn: '1/-1', textAlign: 'center', color: 'var(--color-text-muted)', padding: 40 }}>You don't have any loans yet. Apply for a Personal or Home loan to get started!</div>}
            </div>
          </div>
        )}

        {/* ===== BILL PAY ===== */}
        {activeTab === 'billpay' && (
          <div className="dash-section">
            <div className="dash-section-header"><h2>Bill Payments</h2><button onClick={() => accounts.length ? setModal('payBill') : alert('Open an account first')} className="btn-dash-action">+ Pay a Bill</button></div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(140px,1fr))', gap: 12, marginBottom: 24 }}>
              {['ELECTRICITY', 'GAS', 'WATER', 'DTH', 'BROADBAND', 'MOBILE_POSTPAID', 'INSURANCE_PREMIUM', 'CREDIT_CARD'].map(cat => (
                <button key={cat} className="quick-action-btn" onClick={() => { setFormData({ billerCategory: cat }); setModal('payBill'); }}>
                  <span className="qa-icon">{cat === 'ELECTRICITY' ? '⚡' : cat === 'GAS' ? '🔥' : cat === 'WATER' ? '💧' : cat === 'DTH' ? '📺' : cat === 'BROADBAND' ? '📡' : cat === 'MOBILE_POSTPAID' ? '📱' : cat === 'INSURANCE_PREMIUM' ? '🛡️' : '💳'}</span>
                  <span style={{ fontSize: 11 }}>{cat.replace(/_/g, ' ')}</span>
                </button>
              ))}
            </div>
            <h3>Payment History</h3>
            {billHistory.length === 0 ? <p style={{ color: '#999' }}>No bills paid yet.</p> : (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}><thead><tr style={{ borderBottom: '2px solid #eee' }}><th style={{ textAlign: 'left', padding: 8 }}>Biller</th><th>Category</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
                <tbody>{billHistory.map(b => (<tr key={b.id} style={{ borderBottom: '1px solid #f5f5f5' }}><td style={{ padding: 8 }}>{b.billerName}</td><td style={{ textAlign: 'center' }}>{b.billerCategory}</td><td style={{ textAlign: 'center' }}>S${parseFloat(b.amount).toFixed(2)}</td><td style={{ textAlign: 'center' }}><span className={`status-badge ${(b.status || '').toLowerCase()}`}>{b.status}</span></td><td style={{ textAlign: 'center', fontSize: 12 }}>{new Date(b.createdAt).toLocaleDateString()}</td></tr>))}</tbody>
              </table>
            )}
          </div>
        )}

        {/* ===== FIXED DEPOSITS ===== */}
        {activeTab === 'deposits' && (
          <div className="dash-section">
            <div className="dash-section-header"><h2>Fixed Deposits</h2><button onClick={() => accounts.length ? setModal('createFD') : alert('Open an account first')} className="btn-dash-action">+ Open FD</button></div>

            <div style={{ marginBottom: 32 }}>
              <h3 style={{ marginBottom: 16 }}>Attractive Interest Rates</h3>
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                <div className="rate-card"><div style={{ color: 'var(--color-text-muted)' }}>3-6 months</div><div className="rate-val">5.50%</div></div>
                <div className="rate-card"><div style={{ color: 'var(--color-text-muted)' }}>12 months</div><div className="rate-val">6.50%</div></div>
                <div className="rate-card" style={{ borderColor: 'var(--color-pink)' }}><div style={{ color: 'var(--color-text-muted)' }}>24 months</div><div className="rate-val" style={{ color: 'var(--color-pink)' }}>7.00%</div></div>
                <div className="rate-card"><div style={{ color: 'var(--color-text-muted)' }}>36 months+</div><div className="rate-val">7.25%</div></div>
              </div>
            </div>

            <h3 style={{ marginBottom: 16 }}>Your Active FDs</h3>
            <div className="dash-cards-grid">
              {fds.map(fd => (
                <div key={fd.id} className="dash-account-card profile-card" style={{ padding: '24px' }}>
                  <div className="account-card-top"><span className="account-type">FD #{fd.fdNumber}</span><span className={`account-status ${(fd.status || '').toLowerCase()}`}>{fd.status}</span></div>
                  <div className="account-balance" style={{ marginTop: 12 }}><span className="balance-label">Principal Amount</span><span className="balance-amount">S${parseFloat(fd.principalAmount).toLocaleString()}</span></div>
                  <div className="loan-details" style={{ marginTop: 16, borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: 16 }}>
                    <div className="loan-detail-row"><span>Interest Rate</span><span style={{ color: 'var(--color-cyan)', fontWeight: 600 }}>{fd.interestRate}% p.a.</span></div>
                    <div className="loan-detail-row"><span>Tenure</span><span>{fd.tenureMonths} months</span></div>
                    <div className="loan-detail-row"><span>Maturity Amount</span><span>S${parseFloat(fd.maturityAmount).toLocaleString()}</span></div>
                    <div className="loan-detail-row"><span>Maturity Date</span><span>{fd.maturityDate}</span></div>
                    <div className="loan-detail-row"><span>Auto Renew</span><span>{fd.autoRenew ? 'Enabled' : 'Disabled'}</span></div>
                  </div>
                  {fd.status === 'ACTIVE' && <div className="account-actions" style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid rgba(255,255,255,0.05)' }}><button className="btn-sm" style={{ width: '100%', padding: '10px' }} onClick={() => { if (window.confirm('Break FD early? Penalty applies.')) handleAction('breakFD', fd.id); }}>Break Deposit</button></div>}
                </div>
              ))}
              {fds.length === 0 && <div className="profile-card" style={{ gridColumn: '1/-1', textAlign: 'center', color: 'var(--color-text-muted)' }}>No fixed deposits found. Open one today to earn higher interest on your idle cash!</div>}
            </div>
          </div>
        )}

        {/* ===== SERVICES ===== */}
        {activeTab === 'services' && (
          <div className="dash-section">
            <div className="dash-section-header"><h2>Banking Services</h2></div>
            <div className="services-grid">
              {[
                { title: 'Payments & Transfers', icon: '💸', items: ['Manage PayNow', 'Overseas Transfer', 'GIRO Arrangements', 'Scheduled Transfers', 'e-Wallet Top-up'] },
                { title: 'Wealth & Insurance', icon: '📈', items: ['Fixed Deposits', 'Investment Portfolios', 'Life Insurance', 'Travel Insurance', 'Motor Insurance'] },
                { title: 'Card Management', icon: '💳', items: ['Travel Activation', 'Change Card PIN', 'Report Lost/Stolen', 'Increase Credit Limit', 'Card Replacement'] },
                { title: 'Account Services', icon: '⚙️', items: ['Download e-Statements', 'Request Cheque Book', 'Update Mailing Address', 'Update Contact Details', 'Live Customer Support'] }
              ].map(section => (
                <div key={section.title} className="service-card">
                  <h3>{section.icon} {section.title}</h3>
                  <ul>
                    {section.items.map(i => <li key={i}>{i}</li>)}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===== NOTIFICATIONS ===== */}
        {activeTab === 'notifications' && (
          <div className="dash-section">
            <div className="dash-section-header">
              <h2>Alerts & Notifications</h2>
              {notifications.some(n => !n.isRead) && <button onClick={() => handleAction('markAllRead')} className="btn-dash-action">Mark All Read</button>}
            </div>
            <div style={{ marginTop: 24 }}>
              {notifications.length === 0 ? <p style={{ color: 'var(--color-text-muted)' }}>You have no recent notifications.</p> :
                notifications.map(n => (
                  <div key={n.id} className={`alert-item ${!n.isRead ? 'unread' : ''}`} onClick={() => !n.isRead && handleAction('markRead', n.id)}>
                    <div>
                      <div className="alert-title">{!n.isRead && <span className="unread-dot"></span>} {n.title}</div>
                      <div className="alert-msg">{n.message}</div>
                    </div>
                    <div className="alert-meta">
                      <div>{new Date(n.createdAt).toLocaleDateString()}</div>
                      <div style={{ marginTop: 4 }}>{new Date(n.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* ===== PROFILE & KYC ===== */}
        {activeTab === 'profile' && (
          <div className="dash-section">
            <div className="dash-section-header"><h2>Profile & Settings</h2></div>

            <div className="profile-card" style={{ marginBottom: 24, background: kycOk ? 'rgba(117, 249, 170, 0.1)' : 'rgba(255, 82, 82, 0.1)', borderColor: kycOk ? 'rgba(117, 249, 170, 0.3)' : 'rgba(255, 82, 82, 0.3)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ marginBottom: 8 }}>Identity Verification (KYC)</h3>
                  <p style={{ color: 'var(--color-text-muted)' }}>Current Status: <strong style={{ color: kycOk ? 'var(--color-green-mint)' : 'var(--color-pink)' }}>{kycStatus}</strong></p>
                </div>
                {(kycStatus === 'UNVERIFIED' || kycStatus === 'REJECTED') &&
                  <button onClick={() => setModal('kyc')} className="btn-dash-action">Submit KYC Documents</button>
                }
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 24 }}>
              <div className="profile-card">
                <div className="profile-header">
                  <div className="profile-avatar">{user?.fullName?.charAt(0) || 'U'}</div>
                  <div>
                    <h3 style={{ fontSize: 24 }}>{user?.fullName}</h3>
                    <p style={{ color: 'var(--color-text-muted)' }}>Joined {user?.createdAt ? new Date(user.createdAt).getFullYear() : '2026'}</p>
                  </div>
                </div>

                <h4 style={{ marginBottom: 16, color: 'var(--color-purple-primary)' }}>Contact Details</h4>
                <div className="profile-row"><span className="profile-label">Email Address</span><span className="profile-value">{user?.email}</span></div>
                <div className="profile-row"><span className="profile-label">Phone Number</span><span className="profile-value">{user?.phone}</span></div>

                <h4 style={{ marginTop: 32, marginBottom: 16, color: 'var(--color-purple-primary)' }}>Basic Info</h4>
                <div className="profile-row"><span className="profile-label">Date of Birth</span><span className="profile-value">{user?.dateOfBirth || '-'}</span></div>
                <div className="profile-row"><span className="profile-label">Gender</span><span className="profile-value">{user?.gender || '-'}</span></div>
              </div>

              <div className="profile-card">
                <h4 style={{ marginBottom: 16, color: 'var(--color-purple-primary)' }}>Address Information</h4>
                <div className="profile-row" style={{ borderBottom: 'none', paddingBottom: 0 }}><span className="profile-label">Address line</span><span className="profile-value">{user?.address || '-'}</span></div>
                <div className="profile-row" style={{ borderBottom: 'none', paddingTop: 8, paddingBottom: 0 }}><span className="profile-label">City</span><span className="profile-value">{user?.city || '-'}</span></div>
                <div className="profile-row" style={{ borderBottom: 'none', paddingTop: 8, paddingBottom: 0 }}><span className="profile-label">State</span><span className="profile-value">{user?.state || '-'}</span></div>
                <div className="profile-row" style={{ paddingTop: 8 }}><span className="profile-label">Pincode/ZIP</span><span className="profile-value">{user?.pincode || '-'}</span></div>

                <h4 style={{ marginTop: 32, marginBottom: 16, color: 'var(--color-purple-primary)' }}>Verification IDs</h4>
                <div className="profile-row"><span className="profile-label">PAN Number</span><span className="profile-value">{user?.panNumber || '-'}</span></div>
                <div className="profile-row"><span className="profile-label">Aadhaar Last 4</span><span className="profile-value">{user?.aadhaarLast4 ? `XXXX-XXXX-${user.aadhaarLast4}` : '-'}</span></div>

                <h4 style={{ marginTop: 32, marginBottom: 16, color: 'var(--color-purple-primary)' }}>Nominee</h4>
                <div className="profile-row" style={{ borderBottom: 'none', paddingBottom: 0 }}><span className="profile-label">Registrant</span><span className="profile-value">{user?.nomineeName || '-'}</span></div>
                <div className="profile-row" style={{ borderBottom: 'none', paddingTop: 8 }}><span className="profile-label">Relationship</span><span className="profile-value">{user?.nomineeRelation || '-'}</span></div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ===== MODALS ===== */}
      {modal && (
        <div className="modal-overlay" onClick={() => { setModal(null); setFormData({}); }}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            {modal === 'createAccount' && (<>
              <h3>Open New Account</h3>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: 16 }}>Please review the terms and verify your details before opening a new account.</p>
              <form onSubmit={e => { e.preventDefault(); handleAction('createAccount'); }}>
                <div className="form-group"><label>Account Type</label><select><option>GXS Savings Account</option><option>GXS Flexi Account</option></select></div>
                <div className="form-group"><label>Initial Deposit (S$)</label><input type="number" defaultValue="0" /></div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 16 }}>* By clicking 'Confirm', you agree to the GXS Terms of Service and prevailing interest rates.</div>
                <div className="modal-actions"><button type="button" onClick={() => setModal(null)} className="btn-modal-cancel">Cancel</button><button type="submit" className="btn-modal-confirm">Confirm & Open</button></div>
              </form>
            </>)}
            {modal === 'savingGoals' && (<>
              <h3>Create Saving Goal</h3>
              <form onSubmit={e => { e.preventDefault(); alert('Saving goal created! (Mock)'); setModal(null); }}>
                <div className="form-group"><label>Goal Name</label><input type="text" placeholder="e.g. New Car" required /></div>
                <div className="form-group"><label>Target Amount (S$)</label><input type="number" required /></div>
                <div className="form-group"><label>Target Date</label><input type="date" required /></div>
                <div className="modal-actions"><button type="button" onClick={() => setModal(null)} className="btn-modal-cancel">Cancel</button><button type="submit" className="btn-modal-confirm">Create Goal</button></div>
              </form>
            </>)}
            {modal === 'deposit' && (<>
              <h3>Make a Deposit</h3>
              <form onSubmit={e => { e.preventDefault(); handleAction('deposit', selectedAccount || accounts[0]?.id, formData.amount, 'Deposit'); }}>
                <div className="form-group"><label>Amount (S$)</label><input type="number" step="0.01" min="0.01" value={formData.amount || ''} onChange={e => setFormData({ ...formData, amount: e.target.value })} required /></div>
                <div className="modal-actions"><button type="button" onClick={() => setModal(null)} className="btn-modal-cancel">Cancel</button><button type="submit" className="btn-modal-confirm">Deposit</button></div>
              </form>
            </>)}
            {modal === 'transfer' && (<>
              <h3>Transfer Money</h3>
              <form onSubmit={e => { e.preventDefault(); handleAction('transfer', selectedAccount || accounts[0]?.id, formData.toAccount, formData.amount, formData.desc || ''); }}>
                <div className="form-group"><label>From Account</label><select value={selectedAccount || accounts[0]?.id || ''} onChange={e => setSelectedAccount(e.target.value)}>{accounts.map(a => <option key={a.id} value={a.id}>{a.accountNumber} (S${parseFloat(a.balance).toFixed(2)})</option>)}</select></div>
                <div className="form-group"><label>To Account Number</label><input type="text" value={formData.toAccount || ''} onChange={e => setFormData({ ...formData, toAccount: e.target.value })} required /></div>
                <div className="form-group"><label>Amount (S$)</label><input type="number" step="0.01" min="0.01" value={formData.amount || ''} onChange={e => setFormData({ ...formData, amount: e.target.value })} required /></div>
                <div className="form-group"><label>Reference</label><input type="text" value={formData.desc || ''} onChange={e => setFormData({ ...formData, desc: e.target.value })} /></div>
                <div className="modal-actions"><button type="button" onClick={() => setModal(null)} className="btn-modal-cancel">Cancel</button><button type="submit" className="btn-modal-confirm">Send</button></div>
              </form>
            </>)}
            {modal === 'applyCard' && (<>
              <h3>Apply for Card</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {['DEBIT', 'CREDIT', 'PREPAID'].map(t => <button key={t} className="btn-dash-action" onClick={() => handleAction('applyCard', t)}>{t} Card</button>)}
              </div>
              <div className="modal-actions" style={{ marginTop: 16 }}><button onClick={() => setModal(null)} className="btn-modal-cancel">Cancel</button></div>
            </>)}
            {modal === 'applyLoan' && (<>
              <h3>Apply for Loan</h3>
              <form onSubmit={e => { e.preventDefault(); handleAction('applyLoan', { loanType: formData.loanType || 'PERSONAL', amount: parseFloat(formData.amount), tenureMonths: parseInt(formData.tenure || 12), loanName: formData.loanName || '' }); }}>
                <div className="form-group"><label>Loan Type</label><select value={formData.loanType || 'PERSONAL'} onChange={e => setFormData({ ...formData, loanType: e.target.value })}>{['PERSONAL', 'HOME', 'VEHICLE', 'EDUCATION', 'GOLD', 'BUSINESS'].map(t => <option key={t} value={t}>{t}</option>)}</select></div>
                <div className="form-group"><label>Amount (S$)</label><input type="number" min="1000" value={formData.amount || ''} onChange={e => setFormData({ ...formData, amount: e.target.value })} required /></div>
                <div className="form-group"><label>Tenure (months)</label><input type="number" min="3" max="360" value={formData.tenure || '12'} onChange={e => setFormData({ ...formData, tenure: e.target.value })} required /></div>
                <div className="form-group"><label>Purpose</label><input type="text" value={formData.loanName || ''} onChange={e => setFormData({ ...formData, loanName: e.target.value })} /></div>
                <div className="modal-actions"><button type="button" onClick={() => setModal(null)} className="btn-modal-cancel">Cancel</button><button type="submit" className="btn-modal-confirm">Apply</button></div>
              </form>
            </>)}
            {modal === 'kyc' && (<>
              <h3>Verify Identity (KYC)</h3>
              <form onSubmit={e => { e.preventDefault(); handleAction('submitKyc', formData.docType || 'AADHAAR', formData.docNumber || 'XXXX1234'); }}>
                <div className="form-group"><label>Document Type</label><select value={formData.docType || 'AADHAAR'} onChange={e => setFormData({ ...formData, docType: e.target.value })}>{['AADHAAR', 'PAN', 'PASSPORT', 'VOTER_ID', 'DRIVING_LICENSE'].map(t => <option key={t} value={t}>{t}</option>)}</select></div>
                <div className="form-group"><label>Document Number</label><input type="text" value={formData.docNumber || ''} onChange={e => setFormData({ ...formData, docNumber: e.target.value })} placeholder="e.g. XXXX1234" /></div>
                <div style={{ border: '2px dashed #ccc', padding: 32, textAlign: 'center', borderRadius: 8, marginTop: 12 }}>📄 Drag & drop or click to upload (Mock)</div>
                <div className="modal-actions" style={{ marginTop: 16 }}><button type="button" onClick={() => setModal(null)} className="btn-modal-cancel">Cancel</button><button type="submit" className="btn-modal-confirm">Submit</button></div>
              </form>
            </>)}
            {modal === 'addBeneficiary' && (<>
              <h3>Add Beneficiary</h3>
              <form onSubmit={e => { e.preventDefault(); handleAction('addBeneficiary', formData); }}>
                <div className="form-group"><label>Name</label><input type="text" value={formData.beneficiaryName || ''} onChange={e => setFormData({ ...formData, beneficiaryName: e.target.value })} required /></div>
                <div className="form-group"><label>Account Number</label><input type="text" value={formData.accountNumber || ''} onChange={e => setFormData({ ...formData, accountNumber: e.target.value })} required /></div>
                <div className="form-group"><label>IFSC Code</label><input type="text" value={formData.ifscCode || ''} onChange={e => setFormData({ ...formData, ifscCode: e.target.value })} required /></div>
                <div className="form-group"><label>Bank Name</label><input type="text" value={formData.bankName || ''} onChange={e => setFormData({ ...formData, bankName: e.target.value })} /></div>
                <div className="form-group"><label>Nickname</label><input type="text" value={formData.nickname || ''} onChange={e => setFormData({ ...formData, nickname: e.target.value })} /></div>
                <div className="modal-actions"><button type="button" onClick={() => setModal(null)} className="btn-modal-cancel">Cancel</button><button type="submit" className="btn-modal-confirm">Add</button></div>
              </form>
            </>)}
            {modal === 'payBill' && (<>
              <h3>Pay Bill</h3>
              <form onSubmit={e => { e.preventDefault(); handleAction('payBill', { accountId: selectedAccount || accounts[0]?.id, ...formData }); }}>
                <div className="form-group"><label>Account</label><select value={selectedAccount || accounts[0]?.id || ''} onChange={e => setSelectedAccount(e.target.value)}>{accounts.map(a => <option key={a.id} value={a.id}>{a.accountNumber}</option>)}</select></div>
                <div className="form-group"><label>Category</label><select value={formData.billerCategory || 'ELECTRICITY'} onChange={e => setFormData({ ...formData, billerCategory: e.target.value })}>{['ELECTRICITY', 'GAS', 'WATER', 'DTH', 'BROADBAND', 'MOBILE_POSTPAID', 'INSURANCE_PREMIUM', 'CREDIT_CARD'].map(c => <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>)}</select></div>
                <div className="form-group"><label>Biller Name</label><input type="text" value={formData.billerName || ''} onChange={e => setFormData({ ...formData, billerName: e.target.value })} required /></div>
                <div className="form-group"><label>Consumer/Account No.</label><input type="text" value={formData.consumerNumber || ''} onChange={e => setFormData({ ...formData, consumerNumber: e.target.value })} required /></div>
                <div className="form-group"><label>Amount (S$)</label><input type="number" step="0.01" min="1" value={formData.amount || ''} onChange={e => setFormData({ ...formData, amount: e.target.value })} required /></div>
                <div className="modal-actions"><button type="button" onClick={() => setModal(null)} className="btn-modal-cancel">Cancel</button><button type="submit" className="btn-modal-confirm">Pay</button></div>
              </form>
            </>)}
            {modal === 'createFD' && (<>
              <h3>Open Fixed Deposit</h3>
              <form onSubmit={e => { e.preventDefault(); const acId = selectedAccount || accounts[0]?.id; handleAction('createFD', { sourceAccountId: acId, principalAmount: parseFloat(formData.principalAmount), tenureMonths: parseInt(formData.tenure || '12'), autoRenew: false }); }}>
                <div className="form-group"><label>From Account</label><select value={selectedAccount || accounts[0]?.id || ''} onChange={e => setSelectedAccount(e.target.value)}>{accounts.map(a => <option key={a.id} value={a.id}>{a.accountNumber} (S${parseFloat(a.balance).toFixed(2)})</option>)}</select></div>
                <div className="form-group"><label>Principal Amount (S$, min 1,000)</label><input type="number" min="1000" step="0.01" value={formData.principalAmount || ''} onChange={e => setFormData({ ...formData, principalAmount: e.target.value })} required /></div>
                <div className="form-group"><label>Tenure</label><select value={formData.tenure || '12'} onChange={e => setFormData({ ...formData, tenure: e.target.value })}><option value="3">3 months (5.50% p.a.)</option><option value="6">6 months (5.50% p.a.)</option><option value="12">12 months (6.50% p.a.)</option><option value="24">24 months (7.00% p.a.)</option><option value="36">36 months (7.25% p.a.)</option></select></div>
                {formData.principalAmount && <div style={{ background: 'rgba(117,249,170,0.08)', border: '1px solid rgba(117,249,170,0.2)', borderRadius: 8, padding: 12, marginBottom: 12, fontSize: 13 }}>
                  <div>Interest Rate: <strong>{formData.tenure >= 36 ? '7.25' : formData.tenure >= 24 ? '7.00' : formData.tenure >= 12 ? '6.50' : '5.50'}% p.a.</strong></div>
                  <div>Estimated Maturity: <strong>S${(parseFloat(formData.principalAmount) * (1 + (formData.tenure >= 36 ? 7.25 : formData.tenure >= 24 ? 7.00 : formData.tenure >= 12 ? 6.50 : 5.50) / 100 * parseInt(formData.tenure || 12) / 12)).toFixed(2)}</strong></div>
                </div>}
                <div className="modal-actions"><button type="button" onClick={() => setModal(null)} className="btn-modal-cancel">Cancel</button><button type="submit" className="btn-modal-confirm">Create FD</button></div>
              </form>
            </>)}
            {modal === 'statement' && (<>
              <h3>Mini Statement (Last 10)</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead><tr style={{ borderBottom: '2px solid #eee' }}><th style={{ textAlign: 'left', padding: 6 }}>Date</th><th>Type</th><th>Description</th><th>Amount</th><th>Channel</th></tr></thead>
                <tbody>{transactions.map(t => (<tr key={t.id} style={{ borderBottom: '1px solid #f5f5f5' }}><td style={{ padding: 6, fontSize: 11 }}>{new Date(t.createdAt).toLocaleDateString()}</td><td style={{ textAlign: 'center' }}><span className={`status-badge ${t.type.includes('CREDIT') || t.type.includes('IN') || t.type === 'SALARY_CREDIT' ? 'active' : 'pending'}`}>{t.type}</span></td><td>{t.description}</td><td style={{ textAlign: 'right', fontWeight: 600, color: t.type.includes('CREDIT') || t.type.includes('IN') || t.type === 'SALARY_CREDIT' ? '#2e7d32' : '#c62828' }}>S${parseFloat(t.amount).toFixed(2)}</td><td style={{ textAlign: 'center', fontSize: 11 }}>{t.channel}</td></tr>))}</tbody>
              </table>
              <div className="modal-actions" style={{ marginTop: 16 }}><button onClick={() => setModal(null)} className="btn-modal-cancel">Close</button></div>
            </>)}
          </div>
        </div>
      )}
    </div>
  );
}
