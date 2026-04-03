const API_BASE = '/api';

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE;
  }

  getToken() {
    return localStorage.getItem('gxs_token');
  }

  setToken(token) {
    localStorage.setItem('gxs_token', token);
  }

  clearToken() {
    localStorage.removeItem('gxs_token');
    localStorage.removeItem('gxs_user');
  }

  getUser() {
    const user = localStorage.getItem('gxs_user');
    return user ? JSON.parse(user) : null;
  }

  setUser(user) {
    localStorage.setItem('gxs_user', JSON.stringify(user));
  }

  async request(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = { method, headers };
    if (body) {
      config.body = JSON.stringify(body);
    }

    const res = await fetch(`${this.baseUrl}${path}`, config);
    let data = {};
    try {
      const text = await res.text();
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      data = { message: 'Invalid response format from server' };
    }

    if (!res.ok) {
      throw new Error(data.message || `Server error ${res.status}`);
    }

    return data;
  }

  // ─── Auth ───────────────────────────────────────────────────────────────────
  async register(userData) {
    const res = await this.request('POST', '/auth/register', userData);
    if (res.success && res.data) {
      this.setToken(res.data.token);
      this.setUser(res.data);
    }
    return res;
  }

  async login(email, password) {
    const res = await this.request('POST', '/auth/login', { email, password });
    if (res.success && res.data) {
      this.setToken(res.data.token);
      this.setUser(res.data);
    }
    return res;
  }

  async getProfile() {
    return this.request('GET', '/auth/me');
  }

  // ─── Accounts ───────────────────────────────────────────────────────────────
  async createAccount() {
    return this.request('POST', '/accounts');
  }

  async getAccounts() {
    return this.request('GET', '/accounts');
  }

  async getAccount(id) {
    return this.request('GET', `/accounts/${id}`);
  }

  async deposit(accountId, amount, description) {
    return this.request('POST', `/accounts/${accountId}/deposit`, { amount, description });
  }

  async withdraw(accountId, amount, description) {
    return this.request('POST', `/accounts/${accountId}/withdraw`, { amount, description });
  }

  async transfer(accountId, targetAccountNumber, amount, description) {
    return this.request('POST', `/accounts/${accountId}/transfer`, { targetAccountNumber, amount, description });
  }

  async getTransactions(accountId, page = 0, size = 20) {
    return this.request('GET', `/accounts/${accountId}/transactions?page=${page}&size=${size}`);
  }

  // getMiniStatement = last 10 txns (same endpoint, small size)
  async getMiniStatement(accountId) {
    return this.request('GET', `/accounts/${accountId}/transactions?page=0&size=10`);
  }

  // ─── Cards ─────────────────────────────────────────────────────────────────
  async applyCard(cardType) {
    return this.request('POST', '/cards/apply', { cardType });
  }

  async getCards() {
    return this.request('GET', '/cards');
  }

  async toggleFreezeCard(cardId) {
    return this.request('PUT', `/cards/${cardId}/freeze`);
  }

  async updateCardSettings(cardId, settings) {
    return this.request('PUT', `/cards/${cardId}/settings`, settings);
  }

  // ─── Loans ─────────────────────────────────────────────────────────────────
  async applyLoan(loanData) {
    return this.request('POST', '/loans/apply', loanData);
  }

  async getLoans() {
    return this.request('GET', '/loans');
  }

  async repayLoan(loanId, amount) {
    return this.request('POST', `/loans/${loanId}/repay`, { amount });
  }

  async calculateLoan(amount, rate, tenureMonths) {
    return this.request('GET', `/loans/calculate?amount=${amount}&rate=${rate}&tenureMonths=${tenureMonths}`);
  }

  // ─── KYC ───────────────────────────────────────────────────────────────────
  async submitKyc(documentType, documentNumber, fileUrl = 'mock-upload') {
    return this.request('POST', '/kyc/submit', { documentType, documentNumber, fileUrl });
  }

  async getKycDocuments() {
    return this.request('GET', '/kyc/documents');
  }

  // ─── Fixed Deposits ─────────────────────────────────────────────────────────
  async createFD(fdData) {
    // fdData: { sourceAccountId, principalAmount, interestRate, tenureMonths, autoRenew }
    return this.request('POST', '/fd/create', fdData);
  }

  async getFDs() {
    return this.request('GET', '/fd');
  }

  async breakFD(fdId) {
    return this.request('POST', `/fd/${fdId}/break`);
  }

  // ─── Bills ─────────────────────────────────────────────────────────────────
  async payBill(billData) {
    return this.request('POST', '/bills/pay', billData);
  }

  async getBillHistory() {
    return this.request('GET', '/bills/history');
  }

  async getBillers() {
    return this.request('GET', '/bills/billers');
  }

  // ─── Beneficiaries ──────────────────────────────────────────────────────────
  async addBeneficiary(beneficiary) {
    return this.request('POST', '/beneficiaries', beneficiary);
  }

  async getBeneficiaries() {
    return this.request('GET', '/beneficiaries');
  }

  async deleteBeneficiary(id) {
    return this.request('DELETE', `/beneficiaries/${id}`);
  }

  // ─── Notifications ──────────────────────────────────────────────────────────
  async getNotifications() {
    return this.request('GET', '/notifications');
  }

  async getUnreadCount() {
    return this.request('GET', '/notifications/unread-count');
  }

  async markNotificationRead(id) {
    return this.request('PUT', `/notifications/${id}/read`);
  }

  async markAllNotificationsRead() {
    // Mark all individually from the list — or use batch if available
    const res = await this.getNotifications();
    const unread = (res.data || []).filter(n => !n.isRead);
    await Promise.all(unread.map(n => this.markNotificationRead(n.id)));
    return { success: true };
  }

  // ─── Admin / Maker-Checker ──────────────────────────────────────────────────
  async getPendingCards() {
    return this.request('GET', '/admin/pending-cards');
  }

  async getPendingLoans() {
    return this.request('GET', '/admin/pending-loans');
  }

  async approveCard(id) {
    return this.request('POST', `/admin/cards/${id}/approve`);
  }

  async rejectCard(id) {
    return this.request('POST', `/admin/cards/${id}/reject`);
  }

  async approveLoan(id) {
    return this.request('POST', `/admin/loans/${id}/approve`);
  }

  async rejectLoan(id) {
    return this.request('POST', `/admin/loans/${id}/reject`);
  }

  async getAuditLogs() {
    return this.request('GET', '/admin/audit-logs');
  }

  // ─── Promotions / Contact ───────────────────────────────────────────────────
  async getPromotions() {
    return this.request('GET', '/promotions');
  }

  async submitContact(contactData) {
    return this.request('POST', '/contact', contactData);
  }

  async getContactSubmissions() {
    return this.request('GET', '/contact');
  }

  logout() {
    this.clearToken();
  }
}

const api = new ApiClient();
export default api;
