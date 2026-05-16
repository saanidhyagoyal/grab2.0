# 🏆 GrabHack 2.0 — Master Implementation Plan (Full Audit + Roadmap)

## Problem Statement

**GrabHack 2.0 Problem 9-11**: Build GenAI-powered, agentic financial tools for underserved segments.  
Two domains: **Driver & Partner Financial Wellness Coach** + **AI-Powered Fraud Mitigation Agent**.

### Required Deliverables (from PDF)
1. ✅ **Functional Prototype** — demo showing agent executing multi-step goals
2. ✅ **Agent Logic & Architecture Diagram** — brain, tools, memory breakdown  
3. ✅ **Reasoning Log** — step-by-step agent thinking visible in UI
4. ⬜ **README Documentation** — needs to be written/updated

---

## Part 1: Full Codebase Audit — What's Already Built

### 🔍 Backend Python (`backend-python/`)

| Component | File | Status | Notes |
|---|---|---|---|
| **FastAPI App** | `GxsBankApplication.py` | ✅ Done | All routers registered, data seeder runs on startup |
| **Agent Supervisor** | `agent/supervisor.py` | ✅ Done | Keyword-based intent routing to FinWell/FraudShield, cross-domain handling, proactive insights |
| **FinWell Agent** | `agent/finwell_agent.py` | ✅ Done | Handles: day off, savings, income, spending, balance, loan, overall advice. Rule-based (no LLM) |
| **FraudShield Agent** | `agent/fraudshield_agent.py` | ✅ Done | Handles: full scan, freeze cards, alerts, security status, recovery guide. Rule-based (no LLM) |
| **Agent Tools** | `agent/tools.py` | ✅ Done | 14 tools: balance, txn history, cards, freeze, notifications, loans, income/spending analytics, ML calls |
| **Reasoning Logger** | `agent/reasoning_logger.py` | ✅ Done | In-memory singleton. ReasoningStep + ReasoningSession with full audit trail |
| **Agent Controller** | `controller/AgentController.py` | ✅ Done | 8 endpoints: chat, reasoning-log, insights, fraud-alerts, income-forecast/summary, spending, day-off, savings |
| **Anomaly Detector** | `ml/anomaly_detector.py` | ✅ Done | Isolation Forest + rule-based fallback. Feature extraction: amount, time, channel, category |
| **Income Predictor** | `ml/income_predictor.py` | ✅ Done | Day-of-week averages, weekly trend via linear regression, day-off + savings recommendation |
| **Mock Data Generator** | `ml/mock_data_generator.py` | ✅ Done | Realistic Grab ride/food earnings, spending categories, 4 fraud scenarios, 60-day history |
| **Bank Services** | `service/*.py` | ✅ Done | Account, Auth, Card, Loan, FD, Bill, Notification, KYC, etc. — all functional |
| **Bank Controllers** | `controller/*.py` | ✅ Done | REST endpoints for all banking operations |
| **DB Models** | `model/*.py` | ✅ Done | Full SQLAlchemy models for all entities |
| **Data Seeder** | `config/DataSeeder.py` | ✅ Done | Seeds demo users, accounts, cards, loans, transactions |
| **Requirements** | `requirements.txt` | ⚠️ Partial | Has FastAPI + scikit-learn but **NO LangGraph, LangChain, Google Gemini, ChromaDB** |

> [!IMPORTANT]
> **LangGraph is NOT installed**. The agents are currently rule-based with keyword matching, not LLM-powered. **No Gemini/OpenAI API integration exists.** The comment in requirements.txt says "lightweight, no LangGraph for now."

### 🔍 Frontend (`frontend-starter/src/`)

| Component | File | Status | Notes |
|---|---|---|---|
| **Main Router** | `main.jsx` | ✅ Done | Routes for /, /login, /signup, /dashboard, /employee/dashboard. `GlobalAgentPanel` renders for authenticated customers |
| **Landing Page** | `App.jsx` | ✅ Done | Full GXS Bank marketing page with animations |
| **Login Page** | `LoginPage.jsx` | ✅ Done | Email/password + demo accounts listed |
| **Customer Dashboard** | `CustomerDashboard.jsx` | ✅ Done | Full banking dashboard with tabs: Overview, Accounts, Cards, Loans, Bills, FDs, Profile, Notifications |
| **AgentPanel** | `AgentPanel.jsx` | ✅ Done | Floating chat panel with 3 tabs: Chat, Reasoning, Insights. Quick action buttons. Works but... |
| **API Client** | `api.js` | ✅ Done | All agent endpoints integrated: sendAgentMessage, getReasoningLogs, getInsights, getFraudAlerts, etc. |
| **Styles** | `styles.css` | ✅ Done | 52KB of CSS including agent panel styles |

### 🔴 Critical UI Issue (User Feedback)

> [!WARNING]
> **Problem**: The AI features are integrated in TWO conflicting ways:
> 1. **Dashboard tabs** — "🧠 AI Coach" and "🛡️ Security" are nav items in the dashboard, rendering full-page sections with income charts, spending breakdowns, day-off analysis, and fraud alerts
> 2. **Floating chatbot** — `AgentPanel.jsx` renders as a floating bubble (bottom-right) with a chat interface
> 
> The user says: *"it was integrated as an option in dashboard that doesn't look good — as a chatbot it was good, what I believe it was far far better"*
> 
> **The dashboard tab approach makes the agent feel like a static dashboard page, not an intelligent conversational agent.** The floating chatbot IS the right pattern per the hackathon requirements.

### 🔍 What's Missing vs. Original Implementation Plan

| Objective | Status | Gap |
|---|---|---|
| LangGraph state machines | ❌ Not done | Using simple keyword routing instead |
| Gemini/OpenAI LLM integration | ❌ Not done | All responses are rule-based templates |
| ChromaDB vector memory | ❌ Not done | No agent memory/vector store |
| Human-in-the-loop approval gates | ❌ Not done | No confirmation before actions like card freeze |
| `memory.py` (agent memory layer) | ❌ Not done | File doesn't exist |
| Financial Goals API | ⚠️ Partial | Modal exists in UI but POST/GET goals endpoints not functional |
| Dedicated FinancialDashboard page | ⚠️ Wrong | Built as dashboard tab, not as standalone page |
| Dedicated FraudAlertPanel page | ⚠️ Wrong | Built as dashboard tab, not as standalone page |
| Gig worker user profiles in seeder | ⚠️ Partial | Demo users exist but no explicit gig worker profiles |
| 2-slide PPT | ❌ Not done | |
| 2-minute video | ❌ Not done | |
| README documentation | ⚠️ Basic | Exists but not hackathon-quality |
| Architecture diagram (clean) | ❌ Not done | Only ASCII art in plan |

---

## Part 2: Proposed Changes — What To Do Next

### Design Philosophy

> [!IMPORTANT]
> The chatbot-first approach is CORRECT. The hackathon explicitly says *"Priority is placed on the agent's reasoning and utility rather than a pixel-perfect UI."* The floating chatbot with reasoning log IS the hero feature. Dashboard tabs for AI Coach/Security should be removed — all agent interactions should go through the chat panel.

---

### Component 1: Fix Frontend Agent Experience

#### [MODIFY] `frontend-starter/src/pages/CustomerDashboard.jsx`
- **Remove** the `aicoach` tab and `security` tab from the dashboard navigation  
- **Remove** all the inline agent dashboard sections (income charts, spending breakdown, day-off analysis, fraud alerts)
- These features will ONLY be accessible through the chatbot — which is the correct UX for an "agentic" demo
- Keep the overview/accounts/cards/loans/bills/FD/profile tabs as-is (they're standard banking)

#### [MODIFY] `frontend-starter/src/pages/AgentPanel.jsx`
- **Enhance** the floating chatbot to be the PRIMARY agent interface
- Make it larger/more prominent when opened (not just a small floating panel)
- Add a "full-screen" toggle so it can expand to take a larger portion of the screen
- Improve the reasoning log visualization with better animations and step highlighting
- Add response card rendering — when the agent returns data (income charts, fraud alerts), render them as rich cards INSIDE the chat
- Add typing animation that shows each reasoning step as it happens (simulated streaming)

#### [MODIFY] `frontend-starter/src/main.jsx`
- No route changes needed — `GlobalAgentPanel` is already globally rendered for customers

#### [MODIFY] `frontend-starter/src/styles.css`
- Enhance agent panel styles for larger/fullscreen mode
- Add rich card styles for inline data visualization in chat
- Improve reasoning step animations

---

### Component 2: Add LLM Integration (Gemini)

> [!IMPORTANT]
> **Decision needed**: Do you have a Google Gemini API key or OpenAI API key? Without one, we keep rule-based agents (which still work for demo). With one, we can add natural language understanding.

#### [NEW] `backend-python/com/gxs/bank/agent/llm_client.py`
- Abstraction layer for LLM calls (Gemini or OpenAI)
- System prompts for FinWell and FraudShield personas
- Tool-use mode: LLM decides which tools to call, not keyword matching
- Fallback to rule-based if no API key is set

#### [MODIFY] `backend-python/com/gxs/bank/agent/supervisor.py`
- Replace keyword-based `_classify_intent()` with LLM-based intent classification (when API key available)
- Keep keyword fallback for offline demo

#### [MODIFY] `backend-python/com/gxs/bank/agent/finwell_agent.py`
- Add LLM-powered response generation alongside rule-based
- LLM uses tool results to generate personalized, conversational advice
- Keep rule-based as fallback

#### [MODIFY] `backend-python/com/gxs/bank/agent/fraudshield_agent.py`
- Same pattern: LLM generates natural language explanations of anomaly detection results

#### [MODIFY] `backend-python/requirements.txt`
- Add: `google-generativeai>=0.8.0` (or `openai>=1.40.0`)
- Add: `python-dotenv` (already present)
- Optionally: `langgraph>=0.2.0` if we want state machine orchestration

---

### Component 3: Enhance Demo Data & Seeder

#### [MODIFY] `backend-python/com/gxs/bank/config/DataSeeder.py`
- Add a dedicated **gig worker demo user** with:
  - Name: "Amir the Grab Driver" or similar
  - Pre-seeded transactions simulating 60 days of Grab ride/food earnings
  - Pre-seeded spending (fuel, meals, rent, phone bill)
  - At least 2 fraud scenario transactions already in history
  - A savings account with realistic balance (~S$3,000-5,000)
  - An active FlexiLoan
  - At least 1 active card
- This ensures the demo works immediately without needing mock data generation at runtime

---

### Component 4: Backend Refinements

#### [MODIFY] `backend-python/com/gxs/bank/controller/AgentController.py`
- Add WebSocket endpoint for streaming responses (optional but impressive for demo)
- Add POST `/api/agent/goal` and GET `/api/agent/goals` for financial goals tracking

#### [NEW] `backend-python/com/gxs/bank/agent/memory.py`
- Simple in-memory conversation history per user
- Store recent conversation context so the agent can reference previous interactions
- No ChromaDB needed for hackathon — in-memory dict is sufficient

---

### Component 5: Deliverables

#### [NEW] `README.md` (update existing)
- Proper hackathon README with:
  - Problem statement
  - Solution overview
  - Architecture diagram (Mermaid or image)
  - Setup & run instructions
  - Demo scenarios walkthrough
  - Tech stack justification

#### [NEW] Architecture diagram
- Clean diagram generated as image for PPT/README

---

## Part 3: Execution Roadmap

### Phase 1: Fix the Agent UX (Priority 1 — DO FIRST)
1. Remove AI Coach and Security dashboard tabs from `CustomerDashboard.jsx`
2. Enhance `AgentPanel.jsx` to be prominent, expandable, with rich cards
3. Update `styles.css` for improved chatbot styling
4. Test chatbot works end-to-end with existing rule-based agents

### Phase 2: Enhance Agent Intelligence (Priority 2)
5. Add LLM integration (if API key available) or polish rule-based responses
6. Add conversation memory (`memory.py`)
7. Improve reasoning logger to show more granular steps
8. Add financial goals endpoints

### Phase 3: Demo Polish (Priority 3)
9. Enhance data seeder with dedicated gig worker profiles
10. Add richer demo scenarios
11. End-to-end testing of all 3 demo flows:
    - "Can I take a day off?" → income prediction → advice
    - Fraud detection scan → card freeze → recovery guide  
    - "Give me your best financial advice" → comprehensive report
12. UI animations and micro-interactions

### Phase 4: Deliverables (Priority 4)
13. Update README with full documentation
14. Generate architecture diagram
15. Create 2-slide PPT
16. Record 2-minute demo video
17. Final submission

---

## Open Questions

> [!IMPORTANT]
> **1. LLM API Key**: Do you have a Google Gemini API key or OpenAI API key? This determines whether we add LLM intelligence or keep rule-based (both work for demo, but LLM is more impressive).

> [!IMPORTANT]
> **2. Scope Confirmation**: The plan above prioritizes fixing the chatbot experience (Phase 1) over adding new features. Is that the right priority, or do you want something else done first?

> [!WARNING]
> **3. Backend Status**: The frontend failed to load on `localhost:5173` during my check (ERR_CONNECTION_REFUSED). Is the dev server currently running? I'll need both the Python backend (port 8081) and the Vite dev server (port 5173) running to test.

> [!IMPORTANT]
> **4. Timeline**: How much time do you have remaining before submission? The original plan mentioned April 12, 2026. I'll adjust scope based on time available.

---

## Verification Plan

### Automated Tests
- Agent chat round-trip: send queries → verify structured response + reasoning log
- Each demo scenario end-to-end
- All existing bank endpoints still work (regression)

### Manual Verification  
- Visual check of chatbot UX (should feel like a real AI assistant, not a dashboard page)
- Reasoning log visibility and clarity
- Demo flow walkthrough for all 3 scenarios
- Screenshots/recording for submission
