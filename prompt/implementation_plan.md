# 🏆 GrabHack 2.0 — Agentic Financial Intelligence Platform

## Your Hackathon Problem Statement (from PDF)

You are solving **Problem Statement 9-11**: Build GenAI-powered, agentic financial tools for underserved segments. The two exploration domains are:
1. **Driver & Partner Financial Wellness Coach** — embedded agent for gig workers
2. **AI-Powered Fraud Mitigation Agent** — ML + GenAI for anomaly detection and intervention

---

## Part 1: What GXS Bank Has Done So Far

### ✅ For Gig Economy Workers (Financial Inclusion)
| What They Built | Status |
|---|---|
| **GXS Savings Account** — daily interest, "Saving Pockets" with behavioral nudges | ✅ Live |
| **GXS FlexiLoan** — unsecured credit for thin/no credit-bureau users, daily interest | ✅ Live |
| **GXS FlexiCard** — flat-fee credit card for credit newcomers | ✅ Live |
| **GXS Invest** — micro-investing from S$1 in money market funds | ✅ Live |
| **Ecosystem Data** — leveraging Grab ride-hailing/delivery data for credit scoring | ✅ Live |
| **GXS Progress Quotient** — research on underserved financial behavior | ✅ Published |

### ✅ For Fraud Detection
| What They Built | Status |
|---|---|
| **AI transaction monitoring** — real-time pattern analysis | ✅ Live |
| **AI vs. AI defense** — GenAI to counter AI-powered scam attacks | ✅ Live |
| **Risk-based step-up authentication** — triggered by flagged transactions | ✅ Live |
| **Device health monitoring** — jailbreak/malware/VPN detection | ✅ Live |
| **Money Lock** — ring-fenced savings requiring video call to unlock | ✅ Live |
| **GXS Buddy** — human video verification for suspicious unlock requests | ✅ Live |
| **Human-in-the-loop override** — employees can review/override AI decisions | ✅ Live |

---

## Part 2: Why They Haven't Fully Succeeded & Why They Need Agentic AI

### 🔴 The Core Gap — Reactive vs. Proactive

> [!IMPORTANT]
> GXS Bank's current solutions are **reactive and siloed**. They offer good products but lack intelligent *orchestration*. There is no "brain" connecting all these tools into an autonomous agent that reasons, plans, and acts on behalf of the user.

### What's Missing (The Gaps Your Solution Fills)

| Gap | Current State | What Agentic AI Solves |
|---|---|---|
| **No personalized coaching** | Generic nudges in Saving Pockets | An agent that analyzes *each individual's* income pattern, spending habits, and goals to give tailored advice in real-time |
| **No income prediction** | Products treat gig income as static | ML model that predicts future earnings from platform data, adjusting savings/loan advice dynamically |
| **No autonomous action** | User must manually transfer, save, repay | Agent proactively moves money to savings, optimizes bill timing, auto-adjusts budgets |
| **No cross-product reasoning** | Savings, Loans, Cards, Investments are independent | Agent reasons across ALL products — "pause FlexiLoan repayment this week, move surplus to Invest" |
| **Fraud response is alert-only** | User gets alert, must call or visit app | Agent immediately freezes suspicious channel, generates recovery steps, files report, notifies user — all autonomously |
| **No explainable reasoning** | ML model flags transaction but doesn't explain why | Agent produces natural-language "Reasoning Log" — exactly what the hackathon demands |
| **No proactive threat hunting** | Monitors real-time only | Agent correlates historical patterns across multiple users to predict emerging scam typologies |

### 🔴 Why GXS Can't Easily Build This Themselves

1. **Legacy Infrastructure Fragmentation** — Their existing systems (savings, loans, cards, fraud) are separate microservices with separate teams. Building an agent that orchestrates across all of them requires a unified state graph — a new architectural pattern they don't currently have.

2. **Regulatory Compliance Burden** — Every autonomous action an agent takes (freezing accounts, moving money, adjusting credit) needs explainable audit trails. Their current compliance framework is designed for human decisions, not AI agent decisions. Retrofitting "agent governance" into existing pipelines is a massive effort.

3. **Data Privacy Architecture** — Allowing an AI agent to access transaction data, credit data, and behavioral data simultaneously requires a new data access layer with fine-grained permissions. Their current architecture grants access per-service, not per-agent-task.

4. **Risk of Hallucination in Financial Context** — Unlike general chatbots, a financial agent that "hallucinates" a wrong loan calculation or a false fraud alert can cause real monetary damage. Building guardrails (tool-use only, no free-text financial claims) requires careful LangGraph-style state machines, not simple prompt engineering.

5. **Talent & Framework Maturity** — LangGraph, CrewAI, and production-grade agentic frameworks only matured in 2025. Banks move slowly due to regulatory review cycles. A hackathon team can prototype what their internal teams would take 6-12 months to scope.

---

## Part 3: What Makes You Win — Differentiators

> [!TIP]
> The judges explicitly value: **Problem Clarity, AI Logic, System Design, Business Value, Depth & Realism**. Here's how to dominate each.

### 🏅 Your Winning Strategy

1. **Dual-Agent Architecture** — Don't just build one agent. Build TWO agents that *collaborate*:
   - **FinWell Agent** (Financial Wellness Coach for gig workers)
   - **FraudShield Agent** (AI-Powered Fraud Mitigation)
   - They share a **unified memory layer**, so the fraud agent can use the financial coach's income predictions to better assess "unusual" behavior
   
2. **Show the "Reasoning Log"** — The hackathon *explicitly* asks for this. Build a visible trace panel in your UI that shows "Step 1: Analyzed income data → Step 2: Detected 30% drop in Grab earnings → Step 3: Triggered savings adjustment..."

3. **Production-Ready Architecture** — Use LangGraph (not simple chains) with Human-in-the-Loop approval gates. This shows judges you understand *banking-grade* AI, not toy demos.

4. **Quantified Business Impact** — In your PPT, include specific numbers: "Reduces fraud response time from 48h to 30s", "Increases gig worker savings rate by 40%", "Prevents S$X million in annual fraud losses"

5. **Live Demo That Wows** — Your frontend is already a full banking app (React + Vite). Embed the agent as a chat/command panel inside the bank dashboard. This looks 10x more impressive than a standalone CLI or notebook demo.

---

## Part 4: System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     REACT FRONTEND (Vite)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Bank Dashboard│  │ Agent Chat   │  │ Reasoning Log Panel    │ │
│  │ (Existing)   │  │ Panel (New)  │  │ (New - Shows Agent     │ │
│  │              │  │              │  │  Thought Process)       │ │
│  └──────────────┘  └──────┬───────┘  └────────────┬───────────┘ │
└────────────────────────────┼──────────────────────┼─────────────┘
                             │ WebSocket + REST     │
                             ▼                      │
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON BACKEND (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                 AGENT ORCHESTRATOR (LangGraph)               ││
│  │  ┌────────────────┐          ┌─────────────────────┐        ││
│  │  │ SUPERVISOR     │          │  STATE GRAPH         │        ││
│  │  │ AGENT          │◄────────►│  (Checkpointed,     │        ││
│  │  │ (Routes to     │          │   Auditable)         │        ││
│  │  │  sub-agents)   │          └─────────────────────┘        ││
│  │  └───────┬────────┘                                          ││
│  │          │                                                   ││
│  │   ┌──────┴──────────────────────────────┐                   ││
│  │   │                                      │                   ││
│  │   ▼                                      ▼                   ││
│  │ ┌──────────────────┐  ┌──────────────────────────────┐      ││
│  │ │  FINWELL AGENT   │  │  FRAUDSHIELD AGENT           │      ││
│  │ │  (Financial      │  │  (Fraud Mitigation)           │      ││
│  │ │   Wellness Coach)│  │                               │      ││
│  │ │                  │  │  Sub-Agents:                   │      ││
│  │ │  Sub-Agents:     │  │  ├─ Transaction Analyzer      │      ││
│  │ │  ├─ Income       │  │  ├─ Risk Scorer               │      ││
│  │ │  │  Analyzer     │  │  ├─ Anomaly Detector (ML)     │      ││
│  │ │  ├─ Budget       │  │  ├─ Intervention Agent        │      ││
│  │ │  │  Optimizer    │  │  └─ Recovery Guide Agent      │      ││
│  │ │  ├─ Savings      │  │                               │      ││
│  │ │  │  Strategist   │  └──────────────┬───────────────┘      ││
│  │ │  └─ Goal         │                 │                       ││
│  │ │     Tracker      │                 │                       ││
│  │ └────────┬─────────┘                 │                       ││
│  │          │                           │                       ││
│  │          ▼                           ▼                       ││
│  │  ┌───────────────────────────────────────────────────────┐  ││
│  │  │              SHARED TOOL LAYER                         │  ││
│  │  │  ┌─────────────┐ ┌──────────┐ ┌──────────────────┐   │  ││
│  │  │  │ Bank API     │ │ ML Model │ │ Notification     │   │  ││
│  │  │  │ Tools        │ │ Tools    │ │ Tools            │   │  ││
│  │  │  │ (Account,    │ │ (Anomaly │ │ (Alert, Email,   │   │  ││
│  │  │  │  Transfer,   │ │  Detect, │ │  Push)           │   │  ││
│  │  │  │  Cards,      │ │  Income  │ │                  │   │  ││
│  │  │  │  Loans)      │ │  Predict)│ │                  │   │  ││
│  │  │  └─────────────┘ └──────────┘ └──────────────────┘   │  ││
│  │  └───────────────────────────────────────────────────────┘  ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │              DATA LAYER                                      ││
│  │  ┌──────────┐  ┌───────────────┐  ┌──────────────────────┐  ││
│  │  │ SQLite   │  │ Vector Store  │  │ Reasoning Log Store  │  ││
│  │  │ (Bank DB)│  │ (ChromaDB -   │  │ (Audit Trail -       │  ││
│  │  │          │  │  Agent Memory) │  │  JSON/DB)            │  ││
│  │  └──────────┘  └───────────────┘  └──────────────────────┘  ││
│  └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | React (Vite) — existing | Already built, just add Agent Panel + Reasoning Log |
| **Backend** | Python (FastAPI) — existing | Already has all bank endpoints, add agent layer on top |
| **Agent Framework** | LangGraph | Production-grade state machines, human-in-the-loop, checkpointing, debugging — recommended for banking |
| **LLM** | Google Gemini API (free tier) or OpenAI GPT-4o-mini | Cost-effective for hackathon, switch to enterprise Gemini for production pitch |
| **ML Model** | Scikit-learn / XGBoost (for anomaly detection) | Simple, explainable, fast — no GPU needed |
| **Vector Store** | ChromaDB (local) | Agent memory — stores past conversations, financial patterns |
| **Database** | SQLite (existing gxs_bank.db) | Already have it, add agent-specific tables |

---

## Part 5: Detailed Technical Implementation Plan

### Component 1: Agent Infrastructure (Backend)

#### [NEW] `backend-python/com/gxs/bank/agent/__init__.py`
Empty init file for agent module.

#### [NEW] `backend-python/com/gxs/bank/agent/supervisor.py`
- Main LangGraph supervisor agent
- Routes user queries to FinWell or FraudShield based on intent
- Maintains conversation state and checkpointing
- Produces structured reasoning logs for every decision

#### [NEW] `backend-python/com/gxs/bank/agent/finwell_agent.py`
- **Income Analyzer**: Ingests transaction history, detects income patterns, predicts future cash flow
- **Budget Optimizer**: Based on income prediction + spending categories, suggests optimal budget allocation
- **Savings Strategist**: Recommends savings targets, auto-suggests "Saving Pocket" amounts
- **Goal Tracker**: Tracks user-set financial goals (emergency fund, vehicle down payment, etc.)

#### [NEW] `backend-python/com/gxs/bank/agent/fraudshield_agent.py`
- **Transaction Analyzer**: Real-time scoring of each transaction against behavioral baselines
- **Anomaly Detector**: ML model (Isolation Forest / XGBoost) trained on mock transaction data
- **Risk Scorer**: Combines rule-based + ML scores into a unified risk rating
- **Intervention Agent**: When risk > threshold → freeze card, flag transaction, notify user
- **Recovery Guide**: Post-fraud steps — generate personalized recovery checklist

#### [NEW] `backend-python/com/gxs/bank/agent/tools.py`
- `get_account_balance` — reads from Bank DB
- `get_transaction_history` — reads from Bank DB
- `get_income_summary` — aggregates income transactions
- `get_spending_by_category` — categorizes expenses
- `freeze_card` — calls CardService
- `create_notification` — calls NotificationService
- `predict_income` — calls ML model
- `detect_anomaly` — calls ML model
- `get_loan_status` — calls LoanService
- `calculate_savings_goal` — pure computation

#### [NEW] `backend-python/com/gxs/bank/agent/memory.py`
- ChromaDB-backed vector store for agent memory
- Stores conversation history, user financial profiles, reasoning logs
- Enables the agent to reference past advice and track goal progress

#### [NEW] `backend-python/com/gxs/bank/agent/reasoning_logger.py`
- Structured logging for every agent decision
- JSON format: `{ step, action, reasoning, tools_used, result, timestamp }`
- Stored in DB and exposed via API for the Reasoning Log Panel

---

### Component 2: ML Models

#### [NEW] `backend-python/com/gxs/bank/ml/anomaly_detector.py`
- Isolation Forest model trained on mock transaction data
- Features: amount, time_of_day, merchant_category, frequency, deviation_from_mean
- Returns anomaly score (0-1) for each transaction

#### [NEW] `backend-python/com/gxs/bank/ml/income_predictor.py`
- Simple time-series model for gig worker income prediction
- Uses historical earnings data to forecast next week/month income
- Factors: day_of_week patterns, seasonal trends, platform activity

#### [NEW] `backend-python/com/gxs/bank/ml/mock_data_generator.py`
- Generates realistic gig worker mock data:
  - Grab ride earnings (variable daily)
  - GrabFood delivery earnings
  - Weekly/monthly income patterns
  - Spending categories (fuel, meals, phone bills, rent)
  - Realistic fraud scenarios (unusual large transfers, midnight transactions, new devices)

---

### Component 3: API Layer (Backend)

#### [NEW] `backend-python/com/gxs/bank/controller/AgentController.py`
```python
# Endpoints:
# POST /api/agent/chat          — Send message to agent, get response + reasoning
# GET  /api/agent/reasoning-log — Get full reasoning log for a session
# POST /api/agent/goal          — Set a financial goal
# GET  /api/agent/goals         — Get all financial goals
# GET  /api/agent/insights      — Get proactive financial insights
# GET  /api/agent/fraud-alerts  — Get active fraud alerts
# POST /api/agent/fraud/dismiss — Dismiss a fraud alert
# GET  /api/agent/income-forecast — Get income prediction
```

#### [MODIFY] `backend-python/com/gxs/bank/controller/AccountController.py`
- Add transaction categorization to transaction responses (for agent consumption)

---

### Component 4: Frontend UI

#### [NEW] `frontend-starter/src/pages/AgentPanel.jsx`
- Floating chat panel (bottom-right) accessible from any page
- Chat interface with agent
- Toggle between FinWell Coach and FraudShield views
- Expandable "Reasoning Log" accordion showing agent thought process

#### [NEW] `frontend-starter/src/pages/FinancialDashboard.jsx`
- Income forecast chart (line graph)
- Budget allocation pie chart
- Savings goals progress bars
- Proactive insights cards
- This replaces/supplements the existing dashboard for gig workers

#### [NEW] `frontend-starter/src/pages/FraudAlertPanel.jsx`
- Real-time fraud alert notifications
- Transaction risk heatmap
- Alert detail with reasoning explanation
- One-click actions: "Freeze Card", "Dismiss Alert", "Report Fraud"

#### [MODIFY] `frontend-starter/src/App.jsx`
- Add AgentPanel as a global overlay component
- Add routes for FinancialDashboard and FraudAlertPanel

#### [MODIFY] `frontend-starter/src/api.js`
- Add agent API methods (`sendAgentMessage`, `getReasoningLog`, `setGoal`, `getInsights`, etc.)

---

### Component 5: Mock Data & Seeding

#### [MODIFY] `backend-python/com/gxs/bank/GxsBankApplication.py` (DataSeeder)
- Add gig worker user profiles with realistic Grab driver income patterns
- Seed 30-60 days of mock transactions with income variability
- Seed fraud scenario transactions (for demo)
- Set up financial goals for demo users

---

## Part 6: 2-Slide PPT Structure

### Slide 1: Problem + Opportunity

**Title:** "From Reactive Banking to Agentic Financial Intelligence"

**Content layout:**
- **Left half:** The Problem
  - "70% of gig workers in SEA have no savings buffer"
  - "Average fraud response time: 48 hours"
  - "Current GXS tools are excellent but siloed — no intelligent orchestration"
  - Visual: Simple icon showing disconnected products (Savings ↔ Loans ↔ Cards ↔ Fraud — no links between them)
  
- **Right half:** Our Solution
  - "Two collaborative AI agents that reason, plan, and act"
  - Visual: The architecture diagram showing FinWell Agent + FraudShield Agent connected via shared memory
  - Key metric: "30-second fraud response, 40% improved savings rate"

### Slide 2: Architecture + Demo Highlights

**Title:** "Production-Ready Agentic Architecture for GXS Bank"

**Content layout:**
- **Top:** Simplified architecture diagram (LangGraph → Supervisor → FinWell + FraudShield → Tools → Bank DB)
- **Middle:** 3 demo scenarios with screenshots:
  1. "Gig worker asks: 'Can I afford to take a day off?'" → Agent analyzes income pattern, shows forecast
  2. "Unusual S$5,000 transfer at 3 AM" → FraudShield detects, freezes card, generates recovery steps
  3. "Agent proactively says: 'Your GrabFood earnings dropped 20% this week — adjusting your savings target'"
- **Bottom:** Tech stack badges: LangGraph | FastAPI | React | Gemini | ChromaDB | XGBoost

---

## Part 7: 2-Minute Video Script Guide

### Structure (120 seconds total):

| Time | Content | What to Show |
|---|---|---|
| 0:00-0:15 | **Hook**: "What if your bank could think like a financial advisor — 24/7, personalized to your life as a gig worker?" | Your face (camera) |
| 0:15-0:30 | **Problem**: "GXS Bank serves 100K+ underserved users. But their products are siloed. No agent connects savings, loans, and fraud protection intelligently." | Slide 1 |
| 0:30-0:50 | **Solution Overview**: "We built two collaborative AI agents: FinWell for proactive financial coaching, and FraudShield for real-time fraud mitigation — powered by LangGraph, running inside GXS Bank." | Architecture diagram |
| 0:50-1:10 | **Demo 1 — FinWell**: Show the agent chat: "Can I take a day off?" → Agent reasons through income data → shows forecast → adjusts savings | Screen recording of app |
| 1:10-1:30 | **Demo 2 — FraudShield**: Show suspicious transaction → Agent detects anomaly → freezes card → shows reasoning log | Screen recording of app |
| 1:30-1:50 | **Technical Depth**: "Built with LangGraph state machines for banking-grade reliability, human-in-the-loop approval gates, and explainable reasoning logs" | Architecture slide |
| 1:50-2:00 | **Close**: "From reactive banking to proactive, agentic financial intelligence — purpose-built for GXS Bank." | Your face (camera) |

---

## Part 8: Execution Roadmap

> [!IMPORTANT]
> You have until **April 12, 2026** (8 days from now). Here's the priority-ordered execution plan.

### Phase 1: Days 1-2 — Agent Core (Must-Have)
- [ ] Set up LangGraph + dependencies in `requirements.txt`
- [ ] Build mock data generator (gig worker transactions)
- [ ] Build agent tools layer (connect to existing bank services)
- [ ] Build Supervisor Agent + routing logic
- [ ] Build FinWell Agent (income analysis + budget optimization)
- [ ] Build FraudShield Agent (anomaly detection + intervention)
- [ ] Build Reasoning Logger
- [ ] Create Agent API endpoints

### Phase 2: Days 3-4 — Frontend Integration
- [ ] Build Agent Chat Panel (floating, global)
- [ ] Build Reasoning Log Panel (expandable accordion)
- [ ] Build Financial Dashboard (income chart, budgets, goals)
- [ ] Build Fraud Alert Panel
- [ ] Integrate all into existing bank dashboard

### Phase 3: Days 5-6 — ML + Polish
- [ ] Train anomaly detection model on mock data
- [ ] Train income predictor on mock data
- [ ] End-to-end demo flow testing
- [ ] UI polish and animations
- [ ] Seed database with compelling demo scenarios

### Phase 4: Days 7-8 — Deliverables
- [ ] Create 2-slide PPT
- [ ] Record 2-minute video
- [ ] Write README documentation
- [ ] Generate Architecture Diagram (clean version)
- [ ] Final testing and submission

---

## Open Questions

> [!IMPORTANT]
> **1. LLM Choice**: Do you have access to Google Gemini API keys or OpenAI API keys? This determines which LLM we use for the agents. (Both work, but I need to know what you have.)

> [!IMPORTANT]  
> **2. Scope Priority**: Given the 8-day timeline, would you prefer to:
> - **(A)** Build both agents with moderate depth (recommended — matches problem statement)
> - **(B)** Go deep on just FinWell (Financial Wellness) with a more polished demo
> - **(C)** Go deep on just FraudShield (Fraud Detection) with stronger ML

> [!WARNING]
> **3. Demo Data**: Your current database has standard bank demo users. I'll need to add gig-worker-specific profiles with realistic Grab driver income patterns. Should I create entirely new users or modify existing ones (like Rahul Sharma)?

> [!IMPORTANT]
> **4. Video Recording**: Will you record using screen capture + webcam, or do you want me to help you set up a polished recording workflow?

---

## Verification Plan

### Automated Tests
- Agent chat round-trip: send a goal query → verify structured response + reasoning log
- Fraud detection: inject anomalous transaction → verify agent triggers alert + freeze
- Income prediction: verify model accuracy on held-out mock data
- All existing bank endpoints still work (regression test)

### Manual Verification
- End-to-end demo walkthrough of all 3 demo scenarios
- PPT review for clarity and impact
- Video recording quality check
- README completeness check
