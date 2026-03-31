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
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.message || 'Something went wrong');
    }

    return data;
  }

  // Auth
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

  // Accounts
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

  // Cards
  async applyCard(cardType) {
    return this.request('POST', '/cards/apply', { cardType });
  }

  async getCards() {
    return this.request('GET', '/cards');
  }

  async toggleFreezeCard(cardId) {
    return this.request('PUT', `/cards/${cardId}/freeze`);
  }

  // Loans
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

  // Promotions
  async getPromotions() {
    return this.request('GET', '/promotions');
  }

  // Contact
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
