# GXS Bank — Test Credentials

When the backend starts up with a fresh database, it uses the `DataSeeder` to automatically populate the database with these realistic mock users.

**The password for ALL accounts below is `password`.**

## 🏢 Employee / Admin Logins
_Used to verify and approve features like KYC, Loans, and Cards through the Maker-Checker workflow._

| Name | Email | Role | Access Level |
|---|---|---|---|
| Admin GXS | `admin@gxs.com` | `EMPLOYEE` | `ADMIN` (Full oversight privileges) |
| Jane Maker | `maker@gxs.com` | `EMPLOYEE` | `MAKER` (Can initiate workflows and applications) |
| John Checker | `checker@gxs.com` | `EMPLOYEE` | `CHECKER` (Approves pending applications for loans and cards) |

## 👥 Customer Logins
_Used to simulate everyday banking operations as a standard retail user._

| Name | Email | Role | KYC Status | Pre-seeded Assets |
|---|---|---|---|---|
| Rahul Sharma | `rahul@gxs.com` | `CUSTOMER` | `VERIFIED` | Active Savings Account (S$ 500,000 balance), Active Debit & Credit Cards |
| Unverified User | `unverified@gxs.com` | `CUSTOMER` | `UNVERIFIED` | Account Created but needs KYC Verification submission |
| Pending Review User | `pending@gxs.com` | `CUSTOMER` | `PENDING_REVIEW` | KYC Submitted, awaiting Employee checker approval |
| Rejected KYC User | `rejected@gxs.com` | `CUSTOMER` | `REJECTED` | KYC was rejected, needs to resubmit documents |
| Loan Pending User | `loanpending@gxs.com` | `CUSTOMER` | `VERIFIED` | Active Savings Account (S$ 10,000 balance) |
| Card Frozen User | `frozen@gxs.com` | `CUSTOMER` | `VERIFIED` | Active Savings Account (S$ 25,000 balance), Frozen Debit Card |
| New User | `new@gxs.com` | `CUSTOMER` | `VERIFIED` | Active Savings Account (S$ 0.00 balance) |
