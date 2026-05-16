import React, { useState, useEffect, useCallback, useRef } from 'react';
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

  // AI Insights state
  const [agentInsights, setAgentInsights] = useState({});
  const [agentLoading, setAgentLoading] = useState({});
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Fraud check suspect amount
  const [fraudAmount, setFraudAmount] = useState('');

  // OTP & Account Lock state
  const [lockStatus, setLockStatus] = useState({ locked: false, otp_pending: false });
  const [otpPhone, setOtpPhone] = useState('');
  const [otpSending, setOtpSending] = useState(false);
  const [otpSendResult, setOtpSendResult] = useState(null); // result of send-otp call
  const [otpInput, setOtpInput] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);
  const [otpResult, setOtpResult] = useState(null);

  // Audit log & memory
  const [auditLog, setAuditLog] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);

  // Action execution state
  const [executingAction, setExecutingAction] = useState(null); // action_id being executed
  const [executedResults, setExecutedResults] = useState({});   // action_id → result

  // Real-time Fraud Stream state
  const [fraudEvents, setFraudEvents] = useState([]);
  const [fraudStreamActive, setFraudStreamActive] = useState(false);
  const [fraudStreamError, setFraudStreamError] = useState(null);
  const sseRef = useRef(null);

  // Micro-repayment engine
  const [repaymentConfig, setRepaymentConfig] = useState(null);
  const [repaymentLoading, setRepaymentLoading] = useState(false);

  // Floating chatbot popup state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatThinkingStep, setChatThinkingStep] = useState('');



  // Peak Hours Optimiser state
  const [peakTarget, setPeakTarget] = useState('');
  const [peakLoading, setPeakLoading] = useState(false);
  const [peakResult, setPeakResult] = useState(null);

  // Vehicle / Equipment Loan state
  const [assetType, setAssetType] = useState('bike');
  const [assetPrice, setAssetPrice] = useState('');
  const [assetLoading, setAssetLoading] = useState(false);
  const [assetResult, setAssetResult] = useState(null);

  // Dynamic Rate Review state
  const [rateReviewLoanId, setRateReviewLoanId] = useState('');
  const [rateReviewBase, setRateReviewBase] = useState('');
  const [rateReviewLoading, setRateReviewLoading] = useState(false);
  const [rateReviewResult, setRateReviewResult] = useState(null);
  const [rateApplyLoading, setRateApplyLoading] = useState(false);
  const [rateApplyResult, setRateApplyResult] = useState(null);

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
    } catch (err) { console.error('Failed to load:', err); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const loadTabData = async (tab) => {
    setActiveTab(tab);
    try {
      if (tab === 'transfers') { const r = await api.getBeneficiaries(); setBeneficiaries(r.data || []); }
      if (tab === 'notifications') { const r = await api.getNotifications(); setNotifications(r.data || []); }
      if (tab === 'deposits') { const r = await api.getFDs(); setFds(r.data || []); }
      if (tab === 'billpay') { const r = await api.getBillHistory(); setBillHistory(r.data || []); }
      if (tab === 'insights') {
        // Always refresh core data when entering AI insights for latest balances
        loadData();
        setAgentLoading(prev => ({ ...prev, health: true, nudges: true }));
        try {
          const [hr, nr] = await Promise.all([api.getHealthScore(), api.getNudges()]);
          setAgentInsights(prev => ({ ...prev, health: hr.data, nudges: nr.data }));
        } catch (err) { console.error(err); }
        finally { setAgentLoading(prev => ({ ...prev, health: false, nudges: false })); }
        fetchLockStatus();
        fetchAuditLog();
      }
      if (tab === 'accounts' && accounts.length > 0) {
        const r = await api.getMiniStatement(accounts[0].id); setTransactions(r.data?.content || r.data || []);
      }
    } catch (err) { console.error(err); }
  };

  const handleAction = async (action, ...args) => {
    try {
      switch (action) {
        case 'createAccount': await api.createAccount(); break;
        case 'deposit': {
          const depRes = await api.deposit(args[0], parseFloat(args[1]), args[2]);
          const txn = depRes.data;
          if (txn && txn.type === 'GRAB_PAYOUT') {
            alert(`✅ Grab Payout processed!\n\n💰 Net credited: S$${parseFloat(txn.amount).toFixed(2)}\n🏧 ${txn.description}\n📊 New balance: S$${parseFloat(txn.balanceAfter).toLocaleString()}`);
          } else {
            alert(`✅ Deposit of S$${parseFloat(args[1]).toFixed(2)} successful!`);
          }
          break;
        }
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

  const loadAgent = async (key, apiCall) => {
    setAgentLoading(prev => ({ ...prev, [key]: true }));
    try {
      const res = await apiCall();
      setAgentInsights(prev => ({ ...prev, [key]: res.data }));
      fetchAuditLog(); // Auto-refresh logs after any agent call
    } catch (err) { alert(err.message); }
    finally { setAgentLoading(prev => ({ ...prev, [key]: false })); }
  };

  const fetchAuditLog = async () => {
    setAuditLoading(true);
    try {
      const r = await api.getAgentAuditLog(30);
      setAuditLog(r.data || []);
    } catch (_) {}
    finally { setAuditLoading(false); }
  };

  const fetchLockStatus = async () => {
    try {
      const r = await api.getLockStatus();
      setLockStatus(r.data || { locked: false, otp_pending: false });
    } catch (_) {}
  };


  const runPeakHours = async () => {
    setPeakLoading(true); setPeakResult(null);
    try {
      const token = api.getToken();
      const target = parseFloat(peakTarget) || 0;
      const res = await fetch(`/api/agents/peak-hours?weekly_target=${target}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      setPeakResult(json.data || json);
      fetchAuditLog();
    } catch (e) { alert('Peak hours failed: ' + e.message); }
    finally { setPeakLoading(false); }
  };

  const runAssetLoan = async () => {
    if (!assetPrice || parseFloat(assetPrice) <= 0) { alert('Enter a valid asset price'); return; }
    setAssetLoading(true); setAssetResult(null);
    try {
      const token = api.getToken();
      const res = await fetch('/api/agents/asset-loan-eligibility', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset_type: assetType, asset_price: parseFloat(assetPrice) }),
      });
      const json = await res.json();
      setAssetResult(json.data || json);
    } catch (e) { alert('Asset loan check failed: ' + e.message); }
    finally { setAssetLoading(false); }
  };

  const runRateReview = async (applyIt) => {
    const baseRate = parseFloat(rateReviewBase);
    if (!baseRate && !rateReviewLoanId) { alert('Enter a loan ID or a base rate'); return; }
    if (applyIt) { setRateApplyLoading(true); } else { setRateReviewLoading(true); setRateReviewResult(null); }
    try {
      const token = api.getToken();
      const body = {
        loan_id: rateReviewLoanId || '',
        base_rate: baseRate || 0,
        asset_type: assetType,
        apply_adjustment: applyIt,
      };
      const res = await fetch('/api/agents/asset-loan-rate-review', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      if (applyIt) { setRateApplyResult(json.data || json); loadData(); }
      else { setRateReviewResult(json.data || json); }
    } catch (e) { alert('Rate review failed: ' + e.message); }
    finally { setRateReviewLoading(false); setRateApplyLoading(false); }
  };

  const connectFraudStream = useCallback(() => {
    if (sseRef.current) return; // already connected
    const token = api.getToken();
    if (!token) return;

    const url = `http://127.0.0.1:8081/api/agents/fraud-stream?token=${encodeURIComponent(token)}`;
    const sse = new EventSource(url);
    sseRef.current = sse;
    setFraudStreamActive(true);
    setFraudStreamError(null);

    sse.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data);
        if (evt.type === 'fraud_result') {
          setFraudEvents(prev => [evt, ...prev].slice(0, 20)); // keep last 20
          fetchAuditLog();
        }
      } catch (_) {}
    };

    sse.onerror = () => {
      setFraudStreamError('Stream disconnected. Click Connect to retry.');
      setFraudStreamActive(false);
      sse.close();
      sseRef.current = null;
    };
  }, []);

  const disconnectFraudStream = useCallback(() => {
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
    }
    setFraudStreamActive(false);
  }, []);

  // Cleanup SSE on unmount
  useEffect(() => {
    return () => { if (sseRef.current) sseRef.current.close(); };
  }, []);

  const sendOtpToPhone = async () => {
    if (!otpPhone.trim()) return;
    setOtpSending(true);
    try {
      const r = await api.sendOtp(otpPhone.trim());
      setOtpSendResult(r.data);
      await fetchLockStatus();
    } catch (err) {
      setOtpSendResult({ sent: false, message: err.message });
    } finally { setOtpSending(false); }
  };

  const submitOtp = async () => {
    if (!otpInput.trim()) return;
    setOtpLoading(true);
    try {
      const r = await api.verifyOtp(otpInput.trim());
      setOtpResult(r.data);
      setOtpInput('');
      await fetchLockStatus();
    } catch (err) {
      setOtpResult({ verified: false, reason: err.message });
    } finally { setOtpLoading(false); }
  };

  const acceptAction = async (action) => {
    setExecutingAction(action.id);
    try {
      const res = await api.executeAgentAction(action.id, action.amount);
      setExecutedResults(prev => ({ ...prev, [action.id]: { success: true, data: res.data } }));
    } catch (err) {
      setExecutedResults(prev => ({ ...prev, [action.id]: { success: false, error: err.message } }));
    } finally {
      setExecutingAction(null);
    }
  };

  const sendChat = async () => {
    const msg = chatInput.trim();
    if (!msg) return;
    const updatedMessages = [...chatMessages, { role: 'user', text: msg }];
    setChatMessages(updatedMessages);
    setChatInput('');
    setChatLoading(true);
    setChatThinkingStep('🔍 Analyzing your question...');
    try {
      setTimeout(() => setChatThinkingStep('🧠 Routing to the right agent...'), 800);
      setTimeout(() => setChatThinkingStep('📊 Gathering your financial data...'), 1600);
      setTimeout(() => setChatThinkingStep('✍️ Generating personalized response...'), 2400);
      
      const res = await api.sendAdvisorChat(msg, updatedMessages);
      const d = res.data || {};

      setChatMessages(prev => [...prev, {
        role: 'ai',
        text: d.answer || 'No response.',
        tip: d.action_tip || '',
        mode: d.mode,
        intent: d.intent,
        agentsCalled: d.agents_called || [],
        routingChain: d.routing_chain || [],
        guardrails: d.guardrails,
        blocked: d.blocked,
        blockReason: d.block_reason,
      }]);
      fetchAuditLog();
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'ai', text: 'Sorry, I could not process that right now. ' + (err.message || ''), tip: '', mode: 'error' }]);
    } finally { setChatLoading(false); setChatThinkingStep(''); }
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
            <button className={activeTab === 'insights' ? 'active' : ''} onClick={() => {loadTabData('insights'); setActiveSubTab('');}} style={{ background: activeTab === 'insights' ? 'linear-gradient(135deg,#771fff,#f66f87)' : '', WebkitBackgroundClip: activeTab === 'insights' ? 'text' : '', WebkitTextFillColor: activeTab === 'insights' ? 'transparent' : '' }}>AI Insights ✨</button>

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
      {/* Account Lock Banner */}
      {lockStatus.locked && (
        <div style={{ background: 'linear-gradient(90deg, #b71c1c, #d32f2f)', color: '#fff', padding: '14px 24px', textAlign: 'center', fontWeight: 600 }}>
          🔒 Your account has been locked due to suspicious activity: {lockStatus.lock_reason}
          <button onClick={() => setModal('otpVerify')} style={{ marginLeft: 12, padding: '6px 16px', background: '#fff', color: '#b71c1c', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 700 }}>Unlock Now</button>
        </div>
      )}
      {!lockStatus.locked && lockStatus.otp_pending && (
        <div style={{ background: 'linear-gradient(90deg, #e65100, #f57c00)', color: '#fff', padding: '14px 24px', textAlign: 'center', fontWeight: 600 }}>
          🔔 Security OTP sent: {lockStatus.otp_reason}. Verify within {lockStatus.otp_expires_in}s or account will be locked.
          <button onClick={() => setModal('otpVerify')} style={{ marginLeft: 12, padding: '6px 16px', background: '#fff', color: '#e65100', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 700 }}>Enter OTP</button>
        </div>
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
                    <button onClick={async () => { const r = await api.getMiniStatement(acc.id); setTransactions(r.data?.content || r.data || []); setSelectedAccount(acc.id); setModal('statement'); }} className="btn-sm">Statement</button>
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
        {/* ===== AI INSIGHTS ===== */}
        {activeTab === 'insights' && (
          <div className="dash-section">
            <div className="dash-section-header">
              <h2>AI Financial Insights ✨</h2>
              <span className="ai-mode-badge">Powered by GXS AI Agents</span>
            </div>

            {/* ── Row 0: Real-time Fraud Stream ── */}
            <div className="ai-section" style={{ border: '1px solid rgba(246,111,135,0.3)', background: 'rgba(246,111,135,0.04)', borderRadius: 12, marginBottom: 24 }}>
              <div className="ai-section-header">
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: fraudStreamActive ? '#75f9aa' : '#555', boxShadow: fraudStreamActive ? '0 0 6px #75f9aa' : 'none', transition: 'all 0.4s' }} />
                  Real-time Fraud Monitor
                  {fraudStreamActive && <span style={{ fontSize: 11, background: 'rgba(117,249,170,0.15)', color: '#75f9aa', border: '1px solid rgba(117,249,170,0.3)', borderRadius: 20, padding: '2px 10px' }}>LIVE</span>}
                </h3>
                <div style={{ display: 'flex', gap: 8 }}>
                  {!fraudStreamActive
                    ? <button className="btn-ai-load" onClick={connectFraudStream} style={{ background: 'linear-gradient(135deg,#771fff,#f66f87)', color: '#fff', border: 'none' }}>Connect Stream</button>
                    : <button className="btn-ai-refresh" onClick={disconnectFraudStream}>Disconnect</button>
                  }
                  {fraudEvents.length > 0 && <button className="btn-ai-refresh" onClick={() => setFraudEvents([])}>Clear</button>}
                </div>
              </div>

              {fraudStreamError && (
                <div style={{ color: 'var(--color-pink)', fontSize: 13, marginBottom: 10 }}>{fraudStreamError}</div>
              )}

              {fraudStreamActive && fraudEvents.length === 0 && (
                <div className="ai-loading">
                  <div className="spinner" style={{ width: 18, height: 18 }} />
                  <span style={{ fontSize: 13 }}>Monitoring transactions in real-time… Make a transfer or withdrawal to see fraud analysis appear here.</span>
                </div>
              )}

              {!fraudStreamActive && fraudEvents.length === 0 && !fraudStreamError && (
                <div style={{ color: 'var(--color-text-muted)', fontSize: 13, padding: '12px 0' }}>
                  Click <strong>Connect Stream</strong> to start monitoring. Every transfer or withdrawal will be instantly analysed for fraud.
                </div>
              )}

              {fraudEvents.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 340, overflowY: 'auto' }}>
                  {fraudEvents.map((evt, i) => {
                    const riskColor = evt.risk_level === 'CRITICAL' ? '#f66f87' : evt.risk_level === 'HIGH' ? '#ffb300' : evt.risk_level === 'MEDIUM' ? '#00bcd4' : '#75f9aa';
                    const bgColor   = evt.risk_level === 'CRITICAL' ? 'rgba(246,111,135,0.08)' : evt.risk_level === 'HIGH' ? 'rgba(255,179,0,0.08)' : 'rgba(117,249,170,0.05)';
                    return (
                      <div key={i} style={{ background: bgColor, border: `1px solid ${riskColor}40`, borderRadius: 10, padding: '12px 16px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: 13, fontWeight: 700, color: riskColor }}>{evt.risk_level}</span>
                            <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{evt.txn_type}</span>
                            {evt.held && <span style={{ fontSize: 11, background: 'rgba(246,111,135,0.2)', color: '#f66f87', borderRadius: 20, padding: '1px 8px' }}>HELD</span>}
                            {evt.needs_otp && !evt.held && <span style={{ fontSize: 11, background: 'rgba(255,179,0,0.2)', color: '#ffb300', borderRadius: 20, padding: '1px 8px' }}>OTP Required</span>}
                          </div>
                          <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{new Date(evt.timestamp * 1000).toLocaleTimeString()}</span>
                        </div>
                        <div style={{ display: 'flex', gap: 20, fontSize: 13, marginBottom: 4 }}>
                          <span>Amount: <strong style={{ color: riskColor }}>S${(evt.amount || 0).toLocaleString()}</strong></span>
                          <span>Risk Score: <strong>{evt.risk_score}/100</strong></span>
                          <span>OTP Threshold: S${(evt.threshold || 0).toLocaleString()}</span>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>txn: {evt.txn_id?.slice(0, 16)}…</div>
                        {evt.description && <div style={{ fontSize: 12, marginTop: 4 }}>{evt.description}</div>}
                        {(evt.anomalies || []).length > 0 && (
                          <div style={{ marginTop: 8, fontSize: 12 }}>
                            <strong>Anomalies:</strong>
                            {evt.anomalies.slice(0, 2).map((a, j) => (
                              <div key={j} style={{ color: 'var(--color-text-muted)', paddingLeft: 8 }}>• {a.reason} (confidence: {Math.round((a.confidence || 0) * 100)}%)</div>
                            ))}
                          </div>
                        )}
                        {evt.held && (
                          <div style={{ marginTop: 8, padding: '8px 12px', background: 'rgba(246,111,135,0.12)', borderRadius: 6, fontSize: 12 }}>
                            Transaction auto-held. Verify via OTP in the Security section to release it.
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* ── Row 1: Health Score + GigScore ── */}
            <div className="ai-cards-row">
              {/* Health Score */}
              <div className="ai-card ai-card-health">
                <div className="ai-card-label">Financial Health Score</div>
                {agentLoading.health ? (
                  <div className="ai-loading"><div className="spinner" style={{ width: 32, height: 32 }}></div></div>
                ) : agentInsights.health ? (
                  <>
                    <div className="ai-score-big" style={{ color: agentInsights.health.grade === 'A' ? 'var(--color-green-mint)' : agentInsights.health.grade === 'B' ? 'var(--color-cyan)' : agentInsights.health.grade === 'C' ? '#ffb300' : 'var(--color-pink)' }}>
                      {agentInsights.health.health_score}<span style={{ fontSize: 20, fontWeight: 400, marginLeft: 4 }}>/100</span>
                    </div>
                    <div className="ai-grade-badge">{agentInsights.health.grade}</div>
                    <div className="ai-verdict">{agentInsights.health.verdict}</div>
                    <div className="ai-components">
                      {Object.entries(agentInsights.health.components || {}).map(([k, v]) => (
                        <div key={k} className="ai-component-row">
                          <span>{k.replace(/_\d+$/, '').replace(/_/g, ' ')}</span>
                          <div className="ai-progress-bar"><div className="ai-progress-fill" style={{ width: `${(v / 20) * 100}%` }}></div></div>
                          <span>{v}/20</span>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <button className="btn-ai-load" onClick={() => loadAgent('health', api.getHealthScore.bind(api))}>Compute Score</button>
                )}
              </div>

              {/* GigScore */}
              <div className="ai-card ai-card-credit">
                <div className="ai-card-label">GigScore (Credit)</div>
                {agentLoading.credit ? (
                  <div className="ai-loading"><div className="spinner" style={{ width: 32, height: 32 }}></div></div>
                ) : agentInsights.credit ? (
                  <>
                    <div className="ai-score-big" style={{ color: agentInsights.credit.credit_score?.score_grade === 'Excellent' ? 'var(--color-green-mint)' : agentInsights.credit.credit_score?.score_grade === 'Good' ? 'var(--color-cyan)' : agentInsights.credit.credit_score?.score_grade === 'Fair' ? '#ffb300' : 'var(--color-pink)' }}>
                      {agentInsights.credit.credit_score?.gig_score}<span style={{ fontSize: 20, fontWeight: 400, marginLeft: 4 }}>/850</span>
                    </div>
                    <div className="ai-grade-badge">{agentInsights.credit.credit_score?.score_grade}</div>
                    <div className="ai-verdict" style={{ marginBottom: 12 }}>{agentInsights.credit.income_verification?.verification_notes}</div>
                    {agentInsights.credit.loan_eligibility && (
                      <div className="ai-info-box" style={{ background: agentInsights.credit.loan_eligibility.is_eligible ? 'rgba(117,249,170,0.08)' : 'rgba(246,111,135,0.08)', borderColor: agentInsights.credit.loan_eligibility.is_eligible ? 'rgba(117,249,170,0.3)' : 'rgba(246,111,135,0.3)' }}>
                        <div style={{ fontWeight: 600, marginBottom: 6 }}>{agentInsights.credit.loan_eligibility.is_eligible ? '✅ Loan Eligible' : '❌ Not Eligible'}</div>
                        <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>{agentInsights.credit.loan_eligibility.eligibility_reason}</div>
                        {agentInsights.credit.loan_eligibility.is_eligible && (
                          <div style={{ fontSize: 13, marginTop: 8 }}>Max: S${parseFloat(agentInsights.credit.loan_eligibility.max_loan_amount_inr || 0).toLocaleString()} · Rate: {agentInsights.credit.loan_eligibility.interest_rate_pct}%</div>
                        )}
                      </div>
                    )}
                    {(agentInsights.credit.loan_eligibility?.improvement_tips || []).map((tip, i) => (
                      <div key={i} className="ai-tip-row">💡 {tip}</div>
                    ))}
                  </>
                ) : (
                  <button className="btn-ai-load" onClick={() => loadAgent('credit', api.getCreditScore.bind(api))}>Compute GigScore</button>
                )}
              </div>
            </div>

            {/* ── Spending Categories (Embeddings) ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>Spending Breakdown <span style={{ fontSize: 12, color: 'var(--color-text-muted)', fontWeight: 400 }}>— semantic categories via embeddings</span></h3>
                <button className="btn-ai-refresh" onClick={() => loadAgent('nudges', api.getNudges.bind(api))}>↻ Refresh</button>
              </div>
              {(() => {
                const cats = agentInsights.nudges?.expense_by_category;
                if (agentLoading.nudges) return <div className="ai-loading"><div className="spinner" style={{ width: 24, height: 24 }}></div><span>Categorising transactions…</span></div>;
                if (!cats || Object.keys(cats).length === 0) return <button className="btn-ai-load" onClick={() => loadAgent('nudges', api.getNudges.bind(api))}>Analyse Spending</button>;
                return (
                  <div className="ai-nudges-grid">
                    {Object.entries(cats).sort((a, b) => b[1] - a[1]).map(([cat, amt]) => (
                      <div key={cat} className="ai-nudge-card" style={{ flexDirection: 'column', gap: 6, alignItems: 'flex-start' }}>
                        <div style={{ fontWeight: 600, fontSize: 13 }}>{cat}</div>
                        <div style={{ color: 'var(--color-pink)', fontWeight: 700, fontSize: 18 }}>S${parseFloat(amt).toLocaleString()}</div>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>

            {/* ── Row 2: Nudges ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>Today's Nudges</h3>
                <button className="btn-ai-refresh" onClick={() => loadAgent('nudges', api.getNudges.bind(api))}>↻ Refresh</button>
              </div>
              {agentLoading.nudges ? (
                <div className="ai-loading"><div className="spinner" style={{ width: 24, height: 24 }}></div><span>Generating nudges…</span></div>
              ) : agentInsights.nudges ? (
                <div className="ai-nudges-grid">
                  {(agentInsights.nudges.nudges || []).map((nudge, i) => (
                    <div key={i} className="ai-nudge-card">
                      <span className="ai-nudge-icon">{['💡', '🎯', '💰', '📈', '🛡️'][i % 5]}</span>
                      <span>{nudge}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <button className="btn-ai-load" onClick={() => loadAgent('nudges', api.getNudges.bind(api))}>Generate Nudges</button>
              )}
            </div>

            {/* ── Row 3: Financial Wellness ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>Financial Wellness Analysis</h3>
                <button className="btn-ai-refresh" onClick={() => loadAgent('wellness', api.getFinancialWellness.bind(api))}>
                  {agentLoading.wellness ? '…' : agentInsights.wellness ? '↻ Refresh' : 'Analyse'}
                </button>
              </div>
              {agentLoading.wellness && (
                <div className="ai-loading"><div className="spinner" style={{ width: 24, height: 24 }}></div><span>Running wellness crew…</span></div>
              )}
              {agentInsights.wellness && !agentLoading.wellness && (
                <div className="ai-wellness-grid">
                  {/* Income Analysis */}
                  <div className="ai-info-box">
                    <div className="ai-info-title">📊 Income Analysis</div>
                    <div className="ai-info-row"><span>Avg Daily Income</span><span>S${(agentInsights.wellness.income_analysis?.avg_daily_income || 0).toLocaleString()}</span></div>
                    <div className="ai-info-row"><span>Trend</span><span className={`ai-badge ${agentInsights.wellness.income_analysis?.trend}`}>{agentInsights.wellness.income_analysis?.trend}</span></div>
                    <div className="ai-info-row"><span>Volatility</span><span>{agentInsights.wellness.income_analysis?.volatility_level}</span></div>
                    <div className="ai-insight-text">{agentInsights.wellness.income_analysis?.insight_summary}</div>
                  </div>
                  {/* Savings Plan */}
                  <div className="ai-info-box">
                    <div className="ai-info-title">💰 Savings Plan</div>
                    <div className="ai-info-row"><span>Monthly Target</span><span>S${(agentInsights.wellness.savings_plan?.monthly_target_inr || 0).toLocaleString()} ({agentInsights.wellness.savings_plan?.monthly_target_pct}%)</span></div>
                    <div className="ai-info-row"><span>Weekly Milestone</span><span>S${(agentInsights.wellness.savings_plan?.weekly_milestone_inr || 0).toLocaleString()}</span></div>
                    <div className="ai-info-row"><span>Emergency Fund Goal</span><span>S${(agentInsights.wellness.savings_plan?.emergency_fund_goal_inr || 0).toLocaleString()}</span></div>
                    <div className="ai-insight-text">{agentInsights.wellness.savings_plan?.savings_advice}</div>
                  </div>
                  {/* Budget Plan */}
                  <div className="ai-info-box" style={{ gridColumn: '1 / -1' }}>
                    <div className="ai-info-title">📋 Budget Allocation</div>
                    <div className="ai-budget-grid">
                      {Object.entries(agentInsights.wellness.budget_plan?.allocations || {}).map(([cat, amt]) => (
                        <div key={cat} className="ai-budget-item">
                          <div className="ai-budget-cat">{cat}</div>
                          <div className="ai-budget-amt">S${parseFloat(amt).toLocaleString()}</div>
                        </div>
                      ))}
                    </div>
                    <div className="ai-insight-text" style={{ marginTop: 12 }}>{agentInsights.wellness.budget_plan?.overall_advice}</div>
                  </div>
                </div>
              )}
            </div>

            {/* ── Row 4: Income Prediction ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>Income Prediction (4-Week Forecast)</h3>
                <button className="btn-ai-refresh" onClick={() => loadAgent('prediction', api.getIncomePrediction.bind(api))}>
                  {agentLoading.prediction ? '…' : agentInsights.prediction ? '↻ Refresh' : 'Predict'}
                </button>
              </div>
              {agentLoading.prediction && (
                <div className="ai-loading"><div className="spinner" style={{ width: 24, height: 24 }}></div><span>Running prediction crew…</span></div>
              )}
              {agentInsights.prediction && !agentLoading.prediction && (
                <div className="ai-wellness-grid">
                  <div className="ai-info-box">
                    <div className="ai-info-title">📈 Trend Analysis</div>
                    <div className="ai-info-row"><span>Direction</span><span className={`ai-badge ${agentInsights.prediction.trend_analysis?.trend_direction}`}>{agentInsights.prediction.trend_analysis?.trend_direction}</span></div>
                    <div className="ai-info-row"><span>Weekly Average</span><span>S${(agentInsights.prediction.trend_analysis?.avg_weekly_income || 0).toLocaleString()}</span></div>
                    <div className="ai-info-row"><span>Risk Level</span><span>{agentInsights.prediction.trend_analysis?.low_income_weeks_risk}</span></div>
                    <div className="ai-insight-text">{agentInsights.prediction.trend_analysis?.trend_summary}</div>
                  </div>
                  <div className="ai-info-box">
                    <div className="ai-info-title">🔮 4-Week Forecast</div>
                    {(agentInsights.prediction.income_forecast?.weekly_predictions || []).map((wk, i) => (
                      <div key={i} className="ai-info-row">
                        <span>Week {wk.week || i + 1}</span>
                        <span>S${parseFloat(wk.predicted_inr || wk.predicted_income || wk || 0).toLocaleString()} <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>(S${parseFloat(wk.low_inr || 0).toLocaleString()}–S${parseFloat(wk.high_inr || 0).toLocaleString()})</span></span>
                      </div>
                    ))}
                    <div className="ai-info-row"><span>Monthly Forecast</span><span>S${(agentInsights.prediction.income_forecast?.monthly_forecast_inr || 0).toLocaleString()}</span></div>
                    <div className="ai-info-row"><span>Confidence</span><span>{agentInsights.prediction.income_forecast?.confidence_pct}%</span></div>
                    {agentInsights.prediction.income_forecast?.forecast_notes && (
                      <div className="ai-insight-text">{agentInsights.prediction.income_forecast.forecast_notes}</div>
                    )}
                  </div>
                  {agentInsights.prediction.debt_management && (
                    <div className="ai-info-box">
                      <div className="ai-info-title">🏦 Debt Management</div>
                      <div className="ai-info-row"><span>Sustainable EMI?</span><span style={{ color: agentInsights.prediction.debt_management.emi_is_sustainable ? 'var(--color-green-mint)' : 'var(--color-pink)', fontWeight: 600 }}>{agentInsights.prediction.debt_management.emi_is_sustainable ? 'Yes ✅' : 'At Risk ⚠️'}</span></div>
                      <div className="ai-info-row"><span>Suggested Pre-payment</span><span>S${(agentInsights.prediction.debt_management.recommended_prepayment_inr || 0).toLocaleString()}</span></div>
                      <div className="ai-info-row"><span>Debt-free In</span><span>{agentInsights.prediction.debt_management.debt_free_in_months || 0} months</span></div>
                      {(agentInsights.prediction.debt_management?.actionable_steps || []).map((s, i) => (
                        <div key={i} className="ai-tip-row">• {s}</div>
                      ))}
                      {agentInsights.prediction.debt_management?.bad_week_strategy && (
                        <div className="ai-insight-text">{agentInsights.prediction.debt_management.bad_week_strategy}</div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* ── Row 5: Fraud Check ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>Fraud & Risk Analysis</h3>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <input
                    type="number"
                    placeholder="Suspect amount (S$) — optional"
                    value={fraudAmount}
                    onChange={e => setFraudAmount(e.target.value)}
                    style={{ padding: '6px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.05)', color: 'var(--color-text)', fontSize: 13, width: 220 }}
                  />
                  <button className="btn-ai-refresh" onClick={() => loadAgent('fraud', () => api.getFraudCheck(parseFloat(fraudAmount) || 0))}>
                    {agentLoading.fraud ? '…' : agentInsights.fraud ? '↻ Re-scan' : 'Scan Account'}
                  </button>
                </div>
              </div>
              {agentLoading.fraud && (
                <div className="ai-loading"><div className="spinner" style={{ width: 24, height: 24 }}></div><span>Running fraud detection crew…</span></div>
              )}
              {agentInsights.fraud && !agentLoading.fraud && (
                <div className="ai-wellness-grid">
                  <div className="ai-info-box">
                    <div className="ai-info-title">🔍 Anomaly Detection</div>
                    {(agentInsights.fraud.anomaly_detection?.anomalies || []).length === 0 ? (
                      <div style={{ color: 'var(--color-green-mint)', fontWeight: 600 }}>✅ No anomalies detected</div>
                    ) : (agentInsights.fraud.anomaly_detection?.anomalies || []).map((a, i) => (
                      <div key={i} className="ai-alert-row">
                        <div style={{ fontWeight: 600 }}>⚠️ S${parseFloat(a.amount || 0).toLocaleString()} — {a.type}</div>
                        {a.reason && <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginLeft: 8, marginTop: 4 }}>{a.reason}</div>}
                        {a.date && <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 8 }}>{a.date} · confidence {Math.round((a.confidence || 0) * 100)}%</div>}
                      </div>
                    ))}
                  </div>
                  <div className="ai-info-box">
                    <div className="ai-info-title">🎯 Risk Assessment</div>
                    <div className="ai-info-row">
                      <span>Risk Score</span>
                      <span style={{ fontWeight: 700, color: (agentInsights.fraud.risk_assessment?.risk_score || 0) > 60 ? 'var(--color-pink)' : (agentInsights.fraud.risk_assessment?.risk_score || 0) > 30 ? '#ffb300' : 'var(--color-green-mint)' }}>
                        {agentInsights.fraud.risk_assessment?.risk_score || 0}/100
                      </span>
                    </div>
                    <div className="ai-info-row"><span>Level</span><span>{agentInsights.fraud.risk_assessment?.risk_level}</span></div>
                    {agentInsights.fraud.risk_assessment?.primary_risk_factor && (
                      <div className="ai-insight-text">Primary risk: {agentInsights.fraud.risk_assessment.primary_risk_factor}</div>
                    )}
                  </div>
                  {agentInsights.fraud.mitigation && (
                    <div className="ai-info-box">
                      <div className="ai-info-title">🛡️ Recommended Actions</div>
                      {(agentInsights.fraud.mitigation.recommended_actions || agentInsights.fraud.mitigation.immediate_actions || []).map((a, i) => (
                        <div key={i} className="ai-tip-row">• {a}</div>
                      ))}
                      {agentInsights.fraud.mitigation.user_message && (
                        <div className="ai-insight-text" style={{ marginTop: 8 }}>{agentInsights.fraud.mitigation.user_message}</div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* ── Row 5b: Security Alert (after fraud) ── */}
            {agentInsights.fraud?.security_alert?.triggered && (
              <div className="ai-section" style={{ border: '1px solid rgba(246,111,135,0.4)', background: 'rgba(246,111,135,0.06)', borderRadius: 12, padding: 20 }}>
                <div className="ai-section-header">
                  <h3 style={{ color: 'var(--color-pink)' }}>🚨 Security Alert — OTP Verification Required</h3>
                  <button className="btn-ai-refresh" onClick={fetchLockStatus}>↻ Check Status</button>
                </div>
                <div style={{ fontSize: 14, color: 'var(--color-text-muted)', marginBottom: 16 }}>
                  {agentInsights.fraud.security_alert.message}
                </div>
                {/* Step 1: Enter mobile number */}
                {!otpSendResult && (
                  <div className="ai-info-box" style={{ marginTop: 12 }}>
                    <div style={{ fontWeight: 600, marginBottom: 10 }}>Enter your mobile number to receive OTP</div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <input
                        type="tel"
                        placeholder="e.g. 9876543210"
                        value={otpPhone}
                        maxLength={15}
                        onChange={e => setOtpPhone(e.target.value.replace(/[^0-9+\- ]/g, ''))}
                        onKeyDown={e => { if (e.key === 'Enter') sendOtpToPhone(); }}
                        style={{ flex: 1, padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(255,255,255,0.05)', color: 'var(--color-text)', fontSize: 15, letterSpacing: 2 }}
                      />
                      <button className="btn-ai-load" style={{ margin: 0 }} onClick={sendOtpToPhone} disabled={otpSending || otpPhone.length < 10}>
                        {otpSending ? 'Sending…' : 'Send OTP'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Step 2: OTP sent — show status + verify button */}
                {otpSendResult && (
                  <div className="ai-info-box" style={{ background: otpSendResult.sms?.sent ? 'rgba(117,249,170,0.08)' : 'rgba(255,183,0,0.08)', borderColor: otpSendResult.sms?.sent ? 'rgba(117,249,170,0.3)' : 'rgba(255,183,0,0.3)', marginTop: 12 }}>
                    {otpSendResult.sms?.sent ? (
                      <>
                        <div style={{ fontWeight: 700, marginBottom: 6 }}>✅ OTP sent via {otpSendResult.sms.provider}</div>
                        <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
                          Check your mobile {otpSendResult.phone_masked}. Expires in {otpSendResult.expires_in_seconds}s.
                        </div>
                      </>
                    ) : (
                      <>
                        <div style={{ fontWeight: 700, marginBottom: 6 }}>
                          OTP (demo — configure .env for real SMS)
                        </div>
                        <div style={{ fontSize: 32, fontWeight: 800, letterSpacing: 8, color: '#ffb300', marginBottom: 6 }}>
                          {otpSendResult.otp}
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                          Sent to: {otpSendResult.phone_masked} · Expires in {otpSendResult.expires_in_seconds}s
                        </div>
                      </>
                    )}
                    <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                      <button className="btn-ai-load" style={{ margin: 0 }} onClick={() => { setModal('otpVerify'); setOtpResult(null); }}>
                        Enter OTP to Verify
                      </button>
                      <button style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', fontSize: 12, cursor: 'pointer', textDecoration: 'underline' }}
                        onClick={() => { setOtpSendResult(null); setOtpPhone(''); }}>
                        Change number
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── Row 6: Autonomous Action Agent ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>Autonomous Financial Actions <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)' }}>— AI operates your finances</span></h3>
                <button className="btn-ai-refresh" onClick={() => loadAgent('executor', api.getAutoExecutor.bind(api))}>
                  {agentLoading.executor ? '…' : agentInsights.executor ? '↻ Re-run' : 'Run Agent'}
                </button>
              </div>
              {agentLoading.executor && (
                <div className="ai-loading"><div className="spinner" style={{ width: 24, height: 24 }}></div><span>Autonomous agent analysing finances…</span></div>
              )}
              {agentInsights.executor && !agentLoading.executor && (
                <>
                  <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
                    {[
                      { label: 'Actions Taken',  val: agentInsights.executor.summary?.total_actions, color: 'var(--color-cyan)' },
                      { label: 'Executed',        val: agentInsights.executor.summary?.executed,      color: 'var(--color-green-mint)' },
                      { label: 'Scheduled',       val: agentInsights.executor.summary?.scheduled,     color: '#ffb300' },
                      { label: 'Alerts',          val: agentInsights.executor.summary?.alerts,        color: 'var(--color-pink)' },
                    ].map(({ label, val, color }) => (
                      <div key={label} className="ai-info-box" style={{ minWidth: 120, flex: 1, textAlign: 'center' }}>
                        <div style={{ fontSize: 28, fontWeight: 800, color }}>{val ?? 0}</div>
                        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>{label}</div>
                      </div>
                    ))}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {(agentInsights.executor.actions || []).map((action) => (
                      <div key={action.id} className="ai-info-box" style={{
                        borderLeft: `4px solid ${action.status === 'executed' ? 'var(--color-green-mint)' : action.status === 'scheduled' ? '#ffb300' : action.status === 'alert_raised' ? 'var(--color-pink)' : 'var(--color-cyan)'}`,
                        display: 'flex', gap: 16, alignItems: 'flex-start',
                      }}>
                        <div style={{ fontSize: 28, lineHeight: 1 }}>{action.icon}</div>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                            <div style={{ fontWeight: 700 }}>{action.title}</div>
                            <span style={{
                              fontSize: 11, padding: '2px 8px', borderRadius: 20, fontWeight: 600,
                              background: action.status === 'executed' ? 'rgba(117,249,170,0.15)' : action.status === 'scheduled' ? 'rgba(255,183,0,0.15)' : action.status === 'alert_raised' ? 'rgba(246,111,135,0.15)' : 'rgba(80,220,240,0.15)',
                              color: action.status === 'executed' ? 'var(--color-green-mint)' : action.status === 'scheduled' ? '#ffb300' : action.status === 'alert_raised' ? 'var(--color-pink)' : 'var(--color-cyan)',
                            }}>{action.status.replace('_', ' ').toUpperCase()}</span>
                          </div>
                          <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>{action.description}</div>
                          {action.amount > 0 && (
                            <div style={{ marginTop: 6, fontSize: 14, fontWeight: 600, color: 'var(--color-cyan)' }}>S${parseFloat(action.amount).toLocaleString()}</div>
                          )}

                          {/* Accept button for RECOMMENDED actions */}
                          {action.status === 'recommended' && action.id === 'AUTO_FD' && !executedResults[action.id] && (
                            <button
                              onClick={() => acceptAction(action)}
                              disabled={executingAction === action.id}
                              style={{
                                marginTop: 10, padding: '6px 18px', borderRadius: 20,
                                background: executingAction === action.id ? 'rgba(80,220,240,0.2)' : 'linear-gradient(135deg,var(--color-cyan),#771fff)',
                                color: '#fff', border: 'none', cursor: executingAction === action.id ? 'not-allowed' : 'pointer',
                                fontWeight: 600, fontSize: 13,
                              }}
                            >
                              {executingAction === action.id ? '⏳ Processing…' : '✅ Accept & Transfer to FD'}
                            </button>
                          )}

                          {/* Result after execution */}
                          {executedResults[action.id] && (
                            <div style={{
                              marginTop: 10, padding: '10px 14px', borderRadius: 8,
                              background: executedResults[action.id].success ? 'rgba(117,249,170,0.08)' : 'rgba(246,111,135,0.08)',
                              border: `1px solid ${executedResults[action.id].success ? 'rgba(117,249,170,0.3)' : 'rgba(246,111,135,0.3)'}`,
                              fontSize: 13,
                            }}>
                              {executedResults[action.id].success ? (
                                <>
                                  <div style={{ fontWeight: 700, color: 'var(--color-green-mint)', marginBottom: 4 }}>✅ FD Created!</div>
                                  <div style={{ color: 'var(--color-text-muted)' }}>{executedResults[action.id].data?.message}</div>
                                  <div style={{ marginTop: 6, fontSize: 12, color: 'var(--color-text-muted)' }}>
                                    FD# {executedResults[action.id].data?.fd_number} · Matures {executedResults[action.id].data?.maturity_date} · S${parseFloat(executedResults[action.id].data?.maturity_amount || 0).toLocaleString()} at maturity
                                  </div>
                                  <div style={{ marginTop: 4, fontSize: 12, color: 'var(--color-text-muted)' }}>
                                    New balance: S${parseFloat(executedResults[action.id].data?.new_balance || 0).toLocaleString()}
                                  </div>
                                </>
                              ) : (
                                <div style={{ color: 'var(--color-pink)' }}>❌ {executedResults[action.id].error}</div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  {(agentInsights.executor.actions || []).length === 0 && (
                    <div style={{ color: 'var(--color-green-mint)', fontWeight: 600, textAlign: 'center', padding: 20 }}>✅ No actions required — your finances look healthy!</div>
                  )}
                </>
              )}
            </div>



            {/* ── Row 7a: Vehicle / Equipment Loan Eligibility ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>Vehicle & Equipment Loan <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)' }}>— Asset-backed gig loan eligibility</span></h3>
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 14 }}>
                {['bike', 'phone', 'laptop', 'equipment'].map(t => (
                  <button key={t} onClick={() => { setAssetType(t); setAssetResult(null); }}
                    style={{ padding: '6px 16px', borderRadius: 20, border: '1px solid', cursor: 'pointer', fontSize: 13, fontWeight: 600,
                      background: assetType === t ? 'var(--color-cyan)' : 'transparent',
                      color: assetType === t ? '#0a0f1e' : 'var(--color-cyan)',
                      borderColor: 'var(--color-cyan)' }}>
                    {t === 'bike' ? '🛵 Bike' : t === 'phone' ? '📱 Phone' : t === 'laptop' ? '💻 Laptop' : '🔧 Equipment'}
                  </button>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14 }}>
                <input type="number" placeholder={`Asset price (S$) — e.g. ${assetType === 'bike' ? '80000' : assetType === 'phone' ? '25000' : '50000'}`}
                  value={assetPrice} onChange={e => setAssetPrice(e.target.value)}
                  style={{ flex: 1, padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.05)', color: 'var(--color-text-primary)', fontSize: 14 }} />
                <button className="btn-ai-load" onClick={runAssetLoan} disabled={assetLoading}
                  style={{ whiteSpace: 'nowrap' }}>{assetLoading ? 'Checking...' : 'Check Eligibility'}</button>
              </div>
              {assetResult && (() => {
                const loan = assetResult.asset_loan || {};
                const credit = assetResult.base_credit || {};
                const eligible = loan.is_eligible;
                return (
                  <div>
                    <div style={{ display: 'flex', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
                      <div style={{ padding: '10px 18px', borderRadius: 10, background: eligible ? 'rgba(117,249,170,0.12)' : 'rgba(255,77,106,0.12)', border: `1px solid ${eligible ? 'rgba(117,249,170,0.35)' : 'rgba(255,77,106,0.35)'}`, flex: 1, minWidth: 140, textAlign: 'center' }}>
                        <div style={{ fontSize: 22, fontWeight: 800, color: eligible ? '#75f9aa' : '#ff4d6a' }}>{eligible ? 'Eligible' : 'Not Eligible'}</div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>GigScore {credit.gig_score || assetResult.gig_score_used || '—'} · {credit.score_grade || '—'}</div>
                      </div>
                      {eligible && <>
                        <div style={{ padding: '10px 18px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', flex: 1, minWidth: 120, textAlign: 'center' }}>
                          <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-cyan)' }}>S${(loan.loan_amount_inr || 0).toLocaleString()}</div>
                          <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Loan Amount</div>
                        </div>
                        <div style={{ padding: '10px 18px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', flex: 1, minWidth: 120, textAlign: 'center' }}>
                          <div style={{ fontSize: 20, fontWeight: 700, color: '#75f9aa' }}>{loan.interest_rate_pct}%</div>
                          <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>p.a. · {loan.tenure_months}m</div>
                        </div>
                        <div style={{ padding: '10px 18px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', flex: 1, minWidth: 120, textAlign: 'center' }}>
                          <div style={{ fontSize: 20, fontWeight: 700, color: '#ffb300' }}>S${(loan.monthly_emi_inr || 0).toLocaleString()}</div>
                          <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>EMI / month</div>
                        </div>
                      </>}
                    </div>
                    {eligible && (
                      <div style={{ display: 'flex', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
                        <div className="ai-info-row" style={{ flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: '8px 12px' }}>
                          <span style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>Down Payment</span>
                          <span style={{ fontWeight: 600 }}>S${(loan.down_payment_inr || 0).toLocaleString()}</span>
                        </div>
                        <div className="ai-info-row" style={{ flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: '8px 12px' }}>
                          <span style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>Income Boost</span>
                          <span style={{ fontWeight: 600, color: '#75f9aa' }}>+S${(loan.monthly_income_boost_inr || 0).toLocaleString()}/mo</span>
                        </div>
                        <div className="ai-info-row" style={{ flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: '8px 12px' }}>
                          <span style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>Pays for Itself</span>
                          <span style={{ fontWeight: 600, color: 'var(--color-cyan)' }}>{loan.payback_months} months</span>
                        </div>
                      </div>
                    )}
                    <div style={{ fontSize: 13, color: eligible ? '#75f9aa' : '#ff4d6a', marginBottom: 8 }}>{loan.eligibility_reason}</div>
                    {(loan.improvement_tips || []).map((tip, i) => (
                      <div key={i} style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '4px 0', borderTop: i === 0 ? '1px solid rgba(255,255,255,0.07)' : 'none', paddingTop: 6 }}>
                        {i === 0 ? '💡' : '→'} {tip}
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>

            {/* ── Row 7b: Dynamic Loan Rate Review ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>Dynamic Loan Rate Review <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)' }}>— Weekly rate that moves with your behaviour</span></h3>
              </div>
              <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 12 }}>
                Score your financial behaviour this week across 5 dimensions. Good weeks earn a rate cut. Bad weeks raise a warning.
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
                <input placeholder="Loan ID (from Loans tab) — optional" value={rateReviewLoanId} onChange={e => setRateReviewLoanId(e.target.value)}
                  style={{ flex: 2, minWidth: 180, padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.05)', color: 'var(--color-text-primary)', fontSize: 13 }} />
                <input type="number" placeholder="Base rate % (e.g. 10.5)" value={rateReviewBase} onChange={e => setRateReviewBase(e.target.value)}
                  style={{ flex: 1, minWidth: 130, padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.05)', color: 'var(--color-text-primary)', fontSize: 13 }} />
                <button className="btn-ai-load" onClick={() => runRateReview(false)} disabled={rateReviewLoading} style={{ whiteSpace: 'nowrap' }}>
                  {rateReviewLoading ? 'Reviewing...' : 'Run Review'}
                </button>
              </div>
              {rateReviewResult && (() => {
                const rev = rateReviewResult.review || rateReviewResult;
                const delta = rev.rate_delta_pct || 0;
                const band = rev.band || '';
                const colour = rev.colour === 'green' ? '#75f9aa' : rev.colour === 'teal' ? '#00b4d8' : rev.colour === 'amber' ? '#ffb300' : rev.colour === 'red' ? '#ff4d6a' : '#aaa';
                const dims = rev.dimension_breakdown || {};
                return (
                  <div>
                    <div style={{ display: 'flex', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
                      <div style={{ padding: '10px 18px', borderRadius: 10, background: `rgba(${rev.colour === 'green' ? '117,249,170' : rev.colour === 'red' ? '255,77,106' : '255,179,0'},0.12)`, border: `1px solid ${colour}44`, flex: 1, textAlign: 'center', minWidth: 120 }}>
                        <div style={{ fontSize: 28, fontWeight: 900, color: colour }}>{rev.behaviour_score}/100</div>
                        <div style={{ fontSize: 12, color: colour, fontWeight: 600 }}>{band}</div>
                      </div>
                      <div style={{ padding: '10px 18px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', flex: 1, textAlign: 'center', minWidth: 120 }}>
                        <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-text-muted)', textDecoration: 'line-through' }}>{rev.current_rate_pct}%</div>
                        <div style={{ fontSize: 24, fontWeight: 800, color: delta < 0 ? '#75f9aa' : delta > 0 ? '#ff4d6a' : '#aaa' }}>{rev.new_rate_pct}%</div>
                        <div style={{ fontSize: 12, color: delta < 0 ? '#75f9aa' : delta > 0 ? '#ff4d6a' : '#aaa' }}>{delta > 0 ? '+' : ''}{delta}% this week</div>
                      </div>
                      {rev.projected_savings_inr != null && (
                        <div style={{ padding: '10px 18px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', flex: 1, textAlign: 'center', minWidth: 120 }}>
                          <div style={{ fontSize: 20, fontWeight: 700, color: rev.projected_savings_inr >= 0 ? '#75f9aa' : '#ff4d6a' }}>
                            {rev.projected_savings_inr >= 0 ? '−' : '+'}S${Math.abs(rev.projected_savings_inr).toLocaleString()}
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Interest over tenure</div>
                        </div>
                      )}
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--color-text-primary)', marginBottom: 10, lineHeight: 1.6 }}>{rev.adjustment_narrative}</div>
                    {Object.entries(dims).length > 0 && (
                      <div style={{ marginBottom: 12 }}>
                        {Object.entries(dims).map(([key, d]) => {
                          const pct = (d.score / 20) * 100;
                          const label = key.replace(/_20$/, '').replace(/_/g, ' ');
                          return (
                            <div key={key} style={{ marginBottom: 6 }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 2 }}>
                                <span style={{ textTransform: 'capitalize' }}>{label}</span>
                                <span style={{ fontWeight: 600, color: pct >= 75 ? '#75f9aa' : pct >= 50 ? '#ffb300' : '#ff4d6a' }}>{d.score}/20</span>
                              </div>
                              <div style={{ height: 5, borderRadius: 3, background: 'rgba(255,255,255,0.08)' }}>
                                <div style={{ height: '100%', borderRadius: 3, width: `${pct}%`, background: pct >= 75 ? '#75f9aa' : pct >= 50 ? '#ffb300' : '#ff4d6a', transition: 'width 0.6s ease' }} />
                              </div>
                              <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', marginTop: 1 }}>{d.detail}</div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                    {rev.next_week_tip && (
                      <div style={{ padding: '8px 12px', borderRadius: 8, background: 'rgba(0,180,216,0.1)', border: '1px solid rgba(0,180,216,0.25)', fontSize: 12, color: '#00b4d8', marginBottom: 10 }}>
                        💡 Next week: {rev.next_week_tip}
                      </div>
                    )}
                    {!rateApplyResult && (
                      <button className="btn-ai-load" onClick={() => runRateReview(true)} disabled={rateApplyLoading || !rateReviewLoanId}
                        style={{ background: 'rgba(117,249,170,0.15)', color: '#75f9aa', borderColor: 'rgba(117,249,170,0.4)' }}
                        title={!rateReviewLoanId ? 'Enter a Loan ID to apply the rate to the loan record' : ''}>
                        {rateApplyLoading ? 'Applying...' : 'Apply Rate to Loan'}
                      </button>
                    )}
                    {rateApplyResult?.rate_applied_to_db?.applied && (
                      <div style={{ marginTop: 8, padding: '8px 12px', borderRadius: 8, background: 'rgba(117,249,170,0.1)', border: '1px solid rgba(117,249,170,0.3)', fontSize: 12, color: '#75f9aa' }}>
                        Rate updated on loan — new EMI: S${(rateApplyResult.rate_applied_to_db.new_monthly_emi_inr || 0).toLocaleString()}/month
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>

            {/* ── Row 7c: Peak Hours Earnings Optimiser ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>Peak Hours Optimiser <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)' }}>— Specific slots to hit your weekly target</span></h3>
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14 }}>
                <input type="number" placeholder="Weekly income target (S$) — leave blank for 20% above your avg"
                  value={peakTarget} onChange={e => setPeakTarget(e.target.value)}
                  style={{ flex: 1, padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.05)', color: 'var(--color-text-primary)', fontSize: 14 }} />
                <button className="btn-ai-load" onClick={runPeakHours} disabled={peakLoading} style={{ whiteSpace: 'nowrap' }}>
                  {peakLoading ? 'Analysing...' : 'Get Schedule'}
                </button>
              </div>
              {peakResult && (() => {
                const sched = peakResult.peak_hours_schedule || peakResult;
                const ach = sched.achievability || '';
                const achColour = ach === 'easy' ? '#75f9aa' : ach === 'moderate' ? '#ffb300' : '#ff4d6a';
                return (
                  <div>
                    <div style={{ display: 'flex', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
                      <div style={{ padding: '10px 16px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', flex: 1, textAlign: 'center', minWidth: 110 }}>
                        <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-cyan)' }}>S${(sched.weekly_target_inr || 0).toLocaleString()}</div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Weekly Target</div>
                      </div>
                      <div style={{ padding: '10px 16px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', flex: 1, textAlign: 'center', minWidth: 110 }}>
                        <div style={{ fontSize: 18, fontWeight: 700, color: '#aaa' }}>S${(sched.current_weekly_avg_inr || 0).toLocaleString()}</div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Current Avg</div>
                      </div>
                      <div style={{ padding: '10px 16px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', flex: 1, textAlign: 'center', minWidth: 110 }}>
                        <div style={{ fontSize: 18, fontWeight: 700, color: achColour, textTransform: 'capitalize' }}>{ach}</div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Achievability</div>
                      </div>
                      <div style={{ padding: '10px 16px', borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', flex: 1, textAlign: 'center', minWidth: 110 }}>
                        <div style={{ fontSize: 18, fontWeight: 700, color: '#75f9aa' }}>{sched.total_hours_needed}h</div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Hours/week needed</div>
                      </div>
                    </div>
                    {sched.peak_earning_insight && (
                      <div style={{ padding: '8px 12px', borderRadius: 8, background: 'rgba(0,180,216,0.1)', border: '1px solid rgba(0,180,216,0.25)', fontSize: 13, color: '#00b4d8', marginBottom: 12, lineHeight: 1.5 }}>
                        {sched.peak_earning_insight}
                      </div>
                    )}
                    {sched.data_source && (
                      <div style={{ padding: '8px 12px', borderRadius: 8, background: 'rgba(255,179,0,0.06)', border: '1px solid rgba(255,179,0,0.15)', fontSize: 11, color: '#ffb300', marginBottom: 12, lineHeight: 1.5 }}>
                        <span style={{ fontWeight: 700 }}>📊 Data source:</span>{' '}
                        <span style={{ padding: '1px 6px', borderRadius: 8, background: sched.data_source.hourly_data === 'real_transaction_timestamps' ? 'rgba(117,249,170,0.12)' : 'rgba(255,179,0,0.12)', fontSize: 10, fontWeight: 600 }}>
                          {sched.data_source.hourly_data === 'real_transaction_timestamps' ? '✅ Real data' : '⚠️ Industry defaults'}
                        </span>
                        {sched.data_source.note && <div style={{ marginTop: 4, color: 'var(--color-text-muted)', fontSize: 11 }}>{sched.data_source.note}</div>}
                      </div>
                    )}
                    {(sched.top_slots || []).length > 0 && (
                      <div style={{ marginBottom: 12 }}>
                        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 6, fontWeight: 600 }}>TOP EARNING SLOTS</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                          {(sched.top_slots || []).slice(0, 6).map((slot, i) => (
                            <div key={i} style={{ padding: '6px 12px', borderRadius: 20, background: i === 0 ? 'rgba(117,249,170,0.15)' : 'rgba(255,255,255,0.05)', border: `1px solid ${i === 0 ? 'rgba(117,249,170,0.4)' : 'rgba(255,255,255,0.12)'}`, fontSize: 12 }}>
                              <span style={{ fontWeight: 600, color: i === 0 ? '#75f9aa' : 'var(--color-text-primary)' }}>#{slot.rank} {slot.slot_name}</span>
                              <span style={{ color: 'var(--color-text-muted)', marginLeft: 6 }}>S${(slot.avg_income_inr || 0).toLocaleString()}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {(sched.recommended_schedule || []).length > 0 && (
                      <div>
                        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 6, fontWeight: 600 }}>YOUR MINIMUM SCHEDULE TO HIT TARGET</div>
                        {(sched.recommended_schedule || []).map((s, i) => (
                          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', borderRadius: 6, background: 'rgba(255,255,255,0.03)', marginBottom: 4, fontSize: 13 }}>
                            <span style={{ fontWeight: 600 }}>{s.day}</span>
                            <span style={{ color: 'var(--color-text-muted)' }}>{s.time_range}</span>
                            <span style={{ color: '#75f9aa', fontWeight: 600 }}>+S${(s.expected_income_inr || 0).toLocaleString()}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {(sched.days_off_recommendation || []).length > 0 && (
                      <div style={{ marginTop: 10, fontSize: 12, color: 'var(--color-text-muted)' }}>
                        Rest days: <strong>{sched.days_off_recommendation.join(', ')}</strong>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>



            {/* ── Micro-Repayment Engine ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>🏧 Micro-Repayment Engine <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)' }}>— income-linked loan deductions</span></h3>
                <button className="btn-ai-load" onClick={async () => {
                  setRepaymentLoading(true);
                  try {
                    const r = await api.getRepaymentConfig();
                    setRepaymentConfig(r.data || r);
                    fetchAuditLog();
                  } catch (e) { console.error(e); }
                  setRepaymentLoading(false);
                }}>{repaymentLoading ? '…' : 'Load Config'}</button>
              </div>
              {repaymentConfig ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  {/* Left: Rate & Band */}
                  <div style={{ background: 'var(--color-card-bg)', border: '1px solid var(--color-border)', borderRadius: 12, padding: 16 }}>
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>Current Deduction Rate</div>
                    <div style={{ fontSize: 32, fontWeight: 800, color: repaymentConfig.band === 'RISK_PREMIUM' ? 'var(--color-pink)' : repaymentConfig.band === 'FLOOR_PAUSED' ? '#ff6b6b' : 'var(--color-cyan)' }}>
                      {repaymentConfig.enabled ? `${repaymentConfig.current_rate_pct}%` : '—'}
                    </div>
                    <div style={{ fontSize: 12, fontWeight: 600, marginTop: 4, padding: '2px 8px', display: 'inline-block', borderRadius: 999, background: repaymentConfig.band === 'RISK_PREMIUM' ? 'rgba(255,100,130,0.15)' : repaymentConfig.band === 'NO_LOAN' ? 'rgba(128,128,128,0.15)' : 'rgba(80,220,240,0.15)', color: repaymentConfig.band === 'RISK_PREMIUM' ? 'var(--color-pink)' : 'var(--color-cyan)' }}>
                      {repaymentConfig.band === 'BASE' ? '🟢 Good Standing' : repaymentConfig.band === 'RISK_PREMIUM' ? '🔴 Risk Premium' : repaymentConfig.band === 'FLOOR_PAUSED' ? '⛔ Floor Paused' : '— No Loan'}
                    </div>
                    {repaymentConfig.gig_score > 0 && (
                      <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 8 }}>GigScore: <strong style={{ color: 'var(--color-cyan)' }}>{repaymentConfig.gig_score}</strong></div>
                    )}
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>⚡ Floor: S${repaymentConfig.floor_threshold_sgd || 50}/day — deductions pause below this</div>
                  </div>
                  {/* Right: Loan & Today */}
                  <div style={{ background: 'var(--color-card-bg)', border: '1px solid var(--color-border)', borderRadius: 12, padding: 16 }}>
                    {repaymentConfig.active_loan ? (
                      <>
                        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>Active Loan</div>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>{repaymentConfig.active_loan.type}</div>
                        <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Outstanding: <strong>S${(repaymentConfig.active_loan.outstanding || 0).toLocaleString()}</strong></div>
                        <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>EMI: S${(repaymentConfig.active_loan.monthly_emi || 0).toLocaleString()}/mo @ {repaymentConfig.active_loan.interest_rate}%</div>
                        <div style={{ borderTop: '1px solid var(--color-border)', marginTop: 8, paddingTop: 8 }}>
                          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>Today</div>
                          <div style={{ fontSize: 12 }}>Earnings: <strong>S${(repaymentConfig.today_summary?.total_earnings || 0).toLocaleString()}</strong></div>
                          {repaymentConfig.today_summary?.floor_triggered && (
                            <div style={{ fontSize: 11, color: '#ff6b6b', marginTop: 4 }}>⛔ Below floor — deductions paused today</div>
                          )}
                        </div>
                        {repaymentConfig.last_7_days && (
                          <div style={{ borderTop: '1px solid var(--color-border)', marginTop: 8, paddingTop: 8 }}>
                            <div style={{ fontSize: 11, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>Last 7 Days</div>
                            <div style={{ fontSize: 12 }}>Payouts: S${(repaymentConfig.last_7_days.total_payouts || 0).toLocaleString()}</div>
                            <div style={{ fontSize: 12 }}>Deducted: <strong style={{ color: 'var(--color-pink)' }}>S${(repaymentConfig.last_7_days.estimated_deductions || 0).toLocaleString()}</strong> → Loan reduced</div>
                          </div>
                        )}
                      </>
                    ) : (
                      <div style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>No active loans. Micro-repayment is inactive.</div>
                    )}
                  </div>
                </div>
              ) : (
                <div style={{ color: 'var(--color-text-muted)', fontSize: 13, padding: '12px 0' }}>
                  Click "Load Config" to view your micro-repayment settings.
                </div>
              )}
            </div>

            {/* ── Row 8: Agent Reasoning Audit Log ── */}
            <div className="ai-section">
              <div className="ai-section-header">
                <h3>Agent Reasoning Log <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)' }}>— full audit trail</span></h3>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn-ai-refresh" onClick={() => setAuditLog([])} disabled={auditLoading || auditLog.length === 0}>Clear</button>
                  <button className="btn-ai-refresh" onClick={fetchAuditLog}>{auditLoading ? '…' : '↻ Refresh'}</button>
                </div>
              </div>
              {auditLoading ? (
                <div className="ai-loading"><div className="spinner" style={{ width: 24, height: 24 }}></div><span>Loading audit log…</span></div>
              ) : auditLog.length === 0 ? (
                <div style={{ color: 'var(--color-text-muted)', fontSize: 13, padding: '12px 0' }}>
                  No agent calls logged yet. Use chat or run an agent to populate the log.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {auditLog.map((entry, i) => (
                    <div key={entry.id || i} style={{
                      background: 'var(--color-card-bg)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 10,
                      padding: '10px 14px',
                      fontSize: 12,
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <span style={{ fontWeight: 700, color: 'var(--color-cyan)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                          {entry.agent_name}
                        </span>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: 11 }}>
                          {entry.created_at ? new Date(entry.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : ''} · {Math.round(entry.duration_ms || 0)}ms
                        </span>
                      </div>
                      <div style={{ marginBottom: 4 }}>
                        <span style={{ color: 'var(--color-text-muted)' }}>Intent: </span>
                        <span style={{ color: 'var(--color-pink)', fontWeight: 600 }}>{entry.intent || 'chat'}</span>
                        {entry.agents_called?.length > 0 && (
                          <span style={{ color: 'var(--color-text-muted)', marginLeft: 8 }}>→ {entry.agents_called.join(' → ')}</span>
                        )}
                        {entry.graph_mode && (
                          <span style={{ color: 'var(--color-text-muted)', marginLeft: 8 }}>· {entry.graph_mode}</span>
                        )}
                      </div>
                      {entry.input_message && (
                        <div style={{ marginBottom: 4, color: 'var(--color-text-muted)', fontSize: 11 }}>
                          <span style={{ fontWeight: 600 }}>User:</span> {entry.input_message}
                        </div>
                      )}
                      {entry.output_summary && (
                        <div style={{ color: 'var(--color-text-muted)', fontSize: 11, fontStyle: 'italic' }}>{entry.output_summary}</div>
                      )}
                      {(entry.policy_route || entry.chat_error) && (
                        <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                          {entry.policy_route && (
                            <span style={{ padding: '2px 8px', borderRadius: 999, background: 'rgba(80,220,240,0.1)', border: '1px solid rgba(80,220,240,0.2)', color: 'var(--color-cyan)', fontSize: 10, fontWeight: 700 }}>
                              {entry.policy_route}
                            </span>
                          )}
                          {entry.chat_error && (
                            <span style={{ padding: '2px 8px', borderRadius: 999, background: 'rgba(255,103,138,0.08)', border: '1px solid rgba(255,103,138,0.2)', color: '#ff678a', fontSize: 10, fontWeight: 700 }}>
                              chat_error
                            </span>
                          )}
                        </div>
                      )}
                      {entry.routing_chain?.length > 0 && (
                        <details style={{ marginTop: 6 }}>
                          <summary style={{ cursor: 'pointer', color: 'var(--color-text-muted)', fontSize: 11 }}>
                            Routing chain ({entry.routing_chain.length} steps)
                          </summary>
                          <div style={{ marginTop: 4, display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {entry.routing_chain.map((step, j) => (
                              <div key={j} style={{ fontSize: 10, color: 'var(--color-text-muted)', paddingLeft: 8 }}>• {step}</div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* ===== MODALS ===== */}
      {modal && (
        <div className="modal-overlay" onClick={() => { setModal(null); setFormData({}); }}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            {modal === 'otpVerify' && (<>
              <h3>🔐 Verify Your Identity</h3>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: 16, fontSize: 14 }}>
                {lockStatus.locked
                  ? `Your account is locked: ${lockStatus.lock_reason}`
                  : otpSendResult?.sms?.sent
                  ? `OTP sent to your mobile ${otpSendResult.phone_masked}. Enter it below.`
                  : otpSendResult?.otp
                  ? `Your OTP is shown in the fraud alert section. Enter it below.`
                  : 'Enter the OTP sent to your mobile number.'}
              </p>
              {otpResult && (
                <div style={{
                  padding: 12, borderRadius: 8, marginBottom: 16, fontWeight: 600,
                  background: otpResult.verified ? 'rgba(117,249,170,0.1)' : 'rgba(246,111,135,0.1)',
                  color: otpResult.verified ? 'var(--color-green-mint)' : 'var(--color-pink)',
                  border: `1px solid ${otpResult.verified ? 'rgba(117,249,170,0.3)' : 'rgba(246,111,135,0.3)'}`,
                }}>
                  {otpResult.verified ? '✅' : '❌'} {otpResult.reason}
                </div>
              )}
              <div className="form-group">
                <label>Enter OTP</label>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="6-digit OTP"
                  value={otpInput}
                  onChange={e => setOtpInput(e.target.value.replace(/\D/g, ''))}
                  onKeyDown={e => { if (e.key === 'Enter') submitOtp(); }}
                  style={{ letterSpacing: 8, fontSize: 22, textAlign: 'center', fontWeight: 700 }}
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => { setModal(null); setOtpResult(null); }} className="btn-modal-cancel">Cancel</button>
                <button type="button" onClick={submitOtp} disabled={otpLoading || otpInput.length !== 6} className="btn-modal-confirm">
                  {otpLoading ? 'Verifying…' : 'Verify OTP'}
                </button>
              </div>
              {lockStatus.locked && (
                <div style={{ marginTop: 16, textAlign: 'center' }}>
                  <button style={{ fontSize: 12, color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                    onClick={async () => { await api.unlockAccount(); await fetchLockStatus(); setModal(null); }}>
                    Contact Support — Unlock Account
                  </button>
                </div>
              )}
            </>)}
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
              <form onSubmit={e => { e.preventDefault(); handleAction('deposit', selectedAccount || accounts[0]?.id, formData.amount, formData.depositDesc || 'Deposit'); }}>
                <div className="form-group"><label>Description</label>
                  <select value={formData.depositDesc || ''} onChange={e => setFormData({ ...formData, depositDesc: e.target.value })} required>
                    <option value="">— Select type —</option>
                    <optgroup label="🚗 Grab Payouts (triggers micro-repayment)">
                      <option value="GrabFood Delivery - Tampines Hub">GrabFood Delivery - Tampines Hub</option>
                      <option value="GrabFood Delivery - Orchard Road">GrabFood Delivery - Orchard Road</option>
                      <option value="GrabFood Delivery - Marina Bay">GrabFood Delivery - Marina Bay</option>
                      <option value="GrabExpress Parcel - Bedok North">GrabExpress Parcel - Bedok North</option>
                      <option value="GrabMart Grocery Run - Clementi">GrabMart Grocery Run - Clementi</option>
                    </optgroup>
                    <optgroup label="Other">
                      <option value="Deposit">Regular Deposit</option>
                      <option value="Salary Credit">Salary Credit</option>
                      <option value="Refund">Refund</option>
                    </optgroup>
                  </select>
                </div>
                <div className="form-group"><label>Amount (S$)</label><input type="number" step="0.01" min="0.01" value={formData.amount || ''} onChange={e => setFormData({ ...formData, amount: e.target.value })} required /></div>
                {(formData.depositDesc || '').toLowerCase().includes('grab') && (
                  <div style={{ background: 'rgba(80,220,240,0.08)', border: '1px solid rgba(80,220,240,0.2)', borderRadius: 8, padding: '8px 12px', fontSize: 12, color: 'var(--color-cyan)', marginBottom: 12 }}>
                    🏧 Micro-repayment will auto-deduct a portion of this payout towards your active loan.
                  </div>
                )}
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

      {/* ===== FLOATING CHATBOT POPUP ===== */}
      {!chatOpen && (
        <button
          id="floating-chat-btn"
          onClick={() => setChatOpen(true)}
          style={{
            position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
            width: 60, height: 60, borderRadius: '50%',
            background: 'linear-gradient(135deg, #50dcf0, #771fff)',
            border: 'none', cursor: 'pointer',
            boxShadow: '0 4px 20px rgba(80,220,240,0.4), 0 0 40px rgba(119,31,255,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 28, color: '#fff',
            transition: 'transform 0.2s, box-shadow 0.2s',
          }}
          onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.1)'; }}
          onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          💬
        </button>
      )}

      {chatOpen && (
        <div id="floating-chat-popup" style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
          width: 400, maxWidth: 'calc(100vw - 48px)',
          height: 540, maxHeight: 'calc(100vh - 100px)',
          borderRadius: 16,
          background: 'var(--color-bg-dark, #0a0f1e)',
          border: '1px solid rgba(80,220,240,0.3)',
          boxShadow: '0 8px 40px rgba(0,0,0,0.5), 0 0 60px rgba(80,220,240,0.1)',
          display: 'flex', flexDirection: 'column',
          overflow: 'hidden',
          animation: 'chatPopupSlide 0.3s ease-out',
        }}>
          {/* Header */}
          <div style={{
            padding: '12px 16px',
            background: 'linear-gradient(135deg, rgba(80,220,240,0.1), rgba(119,31,255,0.1))',
            borderBottom: '1px solid rgba(80,220,240,0.2)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--color-text-primary, #fff)' }}>
                🤖 AI Financial Advisor
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-muted, #888)', marginTop: 2 }}>
                Ask about savings, loans, income, fraud
              </div>
            </div>
            <button
              onClick={() => setChatOpen(false)}
              style={{
                background: 'rgba(255,255,255,0.08)', border: 'none',
                borderRadius: '50%', width: 28, height: 28,
                cursor: 'pointer', fontSize: 14, color: 'var(--color-text-muted, #888)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >✕</button>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1, overflowY: 'auto', padding: '12px 16px',
            display: 'flex', flexDirection: 'column', gap: 10,
          }}>
            {chatMessages.length === 0 && (
              <div style={{ textAlign: 'center', padding: '30px 10px' }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>💰</div>
                <div style={{ fontSize: 14, color: 'var(--color-text-muted, #888)', marginBottom: 16 }}>
                  Your personal financial AI assistant. Ask me anything!
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center' }}>
                  {['Why is my balance low?', 'Am I saving enough?', 'Can I afford a loan?', 'Check for fraud'].map(q => (
                    <button key={q} onClick={() => { setChatInput(q); }}
                      style={{
                        padding: '5px 12px', borderRadius: 16, fontSize: 11, fontWeight: 500,
                        background: 'rgba(80,220,240,0.08)', border: '1px solid rgba(80,220,240,0.2)',
                        color: 'var(--color-cyan, #50dcf0)', cursor: 'pointer',
                      }}
                    >{q}</button>
                  ))}
                </div>
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div key={i} style={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '85%',
              }}>
                <div style={{
                  padding: '8px 12px', borderRadius: 12, fontSize: 13, lineHeight: 1.5,
                  background: msg.role === 'user'
                    ? 'linear-gradient(135deg, rgba(80,220,240,0.2), rgba(119,31,255,0.2))'
                    : 'rgba(255,255,255,0.05)',
                  border: `1px solid ${msg.role === 'user' ? 'rgba(80,220,240,0.3)' : 'rgba(255,255,255,0.08)'}`,
                  color: 'var(--color-text-primary, #fff)',
                }}>
                  <div>{msg.text}</div>
                  {msg.tip && (
                    <div style={{ marginTop: 6, padding: '4px 8px', borderRadius: 6, background: 'rgba(117,249,170,0.08)', border: '1px solid rgba(117,249,170,0.2)', fontSize: 11, color: '#75f9aa' }}>
                      💡 {msg.tip}
                    </div>
                  )}
                  {/* Traceability badges & Thinking Process */}
                  {msg.role === 'ai' && (msg.routingChain && msg.routingChain.length > 0) && (
                    <div style={{ marginTop: 8, paddingTop: 6, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                      {/* Step-by-step Routing Chain (ChatGPT style) */}
                      <details style={{ fontSize: 11, color: 'var(--color-text-muted)', background: 'rgba(0,0,0,0.2)', padding: '6px 10px', borderRadius: 8, marginTop: 4 }}>
                        <summary style={{ cursor: 'pointer', fontWeight: 600, userSelect: 'none', outline: 'none' }}>🧠 View Thinking Process</summary>
                        <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
                          {msg.routingChain.map((step, idx) => (
                            <div key={idx} style={{ paddingLeft: 8, borderLeft: '2px solid rgba(80,220,240,0.3)' }}>{step}</div>
                          ))}
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div style={{ alignSelf: 'flex-start', maxWidth: '85%' }}>
                <div style={{ padding: '8px 12px', borderRadius: 12, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }}></div>
                  <span style={{ fontSize: 12, color: 'var(--color-cyan, #50dcf0)' }}>{chatThinkingStep || 'Thinking...'}</span>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div style={{
            padding: '10px 12px',
            borderTop: '1px solid rgba(80,220,240,0.15)',
            display: 'flex', gap: 8,
          }}>
            <input
              type="text"
              placeholder="Ask about your finances…"
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !chatLoading) sendChat(); }}
              style={{
                flex: 1, padding: '8px 12px', borderRadius: 10,
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.12)',
                color: 'var(--color-text-primary, #fff)', fontSize: 13,
                outline: 'none',
              }}
            />
            <button
              onClick={sendChat}
              disabled={chatLoading || !chatInput.trim()}
              style={{
                padding: '8px 16px', borderRadius: 10,
                background: chatLoading || !chatInput.trim()
                  ? 'rgba(80,220,240,0.1)' : 'linear-gradient(135deg, #50dcf0, #771fff)',
                border: 'none', color: '#fff', fontWeight: 600, fontSize: 13,
                cursor: chatLoading || !chatInput.trim() ? 'not-allowed' : 'pointer',
              }}
            >Send</button>
          </div>
        </div>
      )}
    </div>
  );
}
