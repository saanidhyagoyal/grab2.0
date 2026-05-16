# Python Backend Cutover Plan (No Functionality Loss)

## Current Connectivity Status
1. Frontend API base is relative `/api`, so React routes all backend calls through the same prefix.
2. Vite dev proxy forwards `/api` traffic to `http://localhost:8081`.
3. Python backend app is configured to run on port `8081`.
4. Route parity check confirms all frontend-used API paths are available in the Python backend.
5. Smoke tests passed for promotions, login, profile, accounts, and card settings updates.

## Goal
1. Replace Java backend runtime with Python backend runtime while preserving all existing behavior, responses, and user flows.

## Scope
1. Authentication and authorization behavior.
2. Customer dashboard flows: accounts, transfers, cards, loans, KYC, fixed deposits, bills, beneficiaries, notifications.
3. Employee dashboard flows: support tickets, promotions, admin workflows.
4. Seed data and role-based demo access.

## Implementation Phases

### Phase 1: Runtime Cutover Setup
1. Keep frontend unchanged and run only Python backend on port `8081`.
2. Ensure Java backend is stopped during validation to avoid mixed-runtime confusion.
3. Keep Vite proxy as-is (`/api -> http://localhost:8081`).

### Phase 2: Contract Validation
1. Validate each frontend API call from `frontend-starter/src/api.js` against Python routes.
2. Validate HTTP status codes and response wrapper shape: `success`, `message`, `data`.
3. Validate auth token flow: register, login, authenticated requests, employee-only access.

### Phase 3: Functional Regression Testing
1. Customer signup, login, and profile fetch.
2. Account creation, deposit, withdraw, transfer, transactions fetch.
3. Card apply, freeze/unfreeze, settings update.
4. Loan apply, calculate, repay.
5. KYC submit and KYC documents fetch.
6. Bill payment and history.
7. Fixed deposit create and break.
8. Beneficiary add/list/delete.
9. Notifications list, unread count, mark read.
10. Employee login, support ticket list, promotions list.

### Phase 4: Data and Seeder Validation
1. Confirm seeded users and roles are available.
2. Confirm seeded accounts/cards/loans/notifications match expected demo scenarios.
3. Confirm login works for seeded users and role routing in frontend works.

### Phase 5: Reliability and Guardrails
1. Add a repeatable backend startup script for Python.
2. Add a regression smoke script for key API endpoints.
3. Add a route-parity check script for frontend API client vs backend route table.
4. Add basic CI step: compile/import test + smoke test.

## Acceptance Criteria
1. All frontend pages function with Python backend only.
2. No frontend code changes required for endpoint paths.
3. All critical user journeys succeed end-to-end.
4. No loss of role-based behavior (CUSTOMER vs EMPLOYEE).
5. No loss of business validations and workflow rules.

## Immediate Execution Checklist
1. Start Python backend on port `8081`.
2. Start frontend (`npm run dev`) and test login for customer and employee users.
3. Run through full dashboard action matrix.
4. Record any response-shape mismatches and patch backend adapters if needed.
5. Freeze Java backend runtime and use Python backend as default.
