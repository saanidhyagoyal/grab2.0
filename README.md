# GXS Bank — GrabHack Hackathon

A production-grade retail digital banking clone featuring secure authentications, Maker-Checker employee workflows, KYC verifications, and comprehensive retail banking actions (Fixed Deposits, Bill Payments, Transfers).

## Tech Stack
- **Backend:** Java 17, Spring Boot 3.3.x, Spring Security, JWT Auth, Hibernate/JPA, PostgreSQL
- **Frontend:** React (Vite), React Router, Context API, Vanilla CSS (Hover Navigation, UI Design)

---

## 🚀 Running the Application Local Environment

### 1. Database Setup (PostgreSQL)
1. Ensure PostgreSQL is running on your machine (default port `5432`).
2. The core database should be manually created before starting the server. If `psql` is available, run:
   ```bash
   psql -U postgres -c "CREATE DATABASE gxs_bank;"
   ```
3. Update verify credentials in `backend/src/main/resources/application.properties`. Ensure `spring.datasource.password` matches your local Postgres password. The application will auto-generate the database schema on start.

### 2. Running the Backend
1. Open a terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Start the Spring Boot server using Maven:
   ```bash
   mvn clean spring-boot:run
   ```
*(Backend runs on `http://localhost:8080`)*

### 3. Running the Frontend
1. Open a new terminal and navigate to `frontend-starter`:
   ```bash
   cd frontend-starter
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite React development server:
   ```bash
   npm run dev
   ```
*(Frontend runs on `http://localhost:5173`)*



## Key Features Developed
- **Robust Role-Based Routing:** JWT payloads fully store KYC verification state, employee tier, and user hierarchy securely preventing unauthorized endpoint manipulation.
- **Micro-transaction Logging:** Every deposit, transfer, or withdrawal generates immutable `Transaction` receipts in PostgreSQL.
- **Hover-dropdown UI Design:** Premium customer dashboard aesthetics complete with modals, nested transaction pages, and micro-hover CSS variables to match actual premium banking interfaces.
