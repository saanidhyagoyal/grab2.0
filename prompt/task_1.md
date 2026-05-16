# GrabHack 2.0 — Execution Tasks

## Phase 1: Fix Agent UX (Priority 1 — DO FIRST) [COMPLETE ✅]

### 1.1 Remove Dashboard-Embedded Agent Tabs
- [x] Remove `aicoach` tab button from `CustomerDashboard.jsx` nav bar
- [x] Remove `security` tab button from `CustomerDashboard.jsx` nav bar  
- [x] Remove entire `{activeTab === 'aicoach' && ( ... )}` section (~165 lines of inline AI Coach dashboard)
- [x] Remove entire `{activeTab === 'security' && ( ... )}` section (~80 lines of inline FraudShield dashboard)
- [x] Remove unused agent state variables from dashboard
- [x] Remove `loadAICoachData()` and `loadSecurityData()` functions
- [x] Remove agent-related tab handling in `loadTabData()` function
- [x] Verify dashboard still works correctly for all remaining tabs

### 1.2 Enhance Floating Chatbot Panel
- [x] Redesign `AgentPanel.jsx` — wider panel with enhanced layout
- [x] Add "expand/fullscreen" toggle button in panel header
- [x] Add fullscreen mode: panel takes 700px width with centered layout
- [x] Add rich response cards — income chart, spending, fraud alerts, savings, day-off inline in chat
- [x] Add inline mini bar chart for income forecast data in chat
- [x] Add inline risk summary card for fraud scan results in chat
- [x] Add inline savings goal progress card for savings recommendations  
- [x] Improve typing/thinking animation — show each reasoning step name as it "processes"
- [x] Add smooth open/close animation for the panel
- [x] Add agent avatar icons — FinWell (💰), FraudShield (🛡️), Supervisor (🧠)
- [x] Improve the quick action buttons layout and styling
- [x] Add fetchWithTimeout to prevent infinite waiting (15s timeout)
- [x] Add console.log debugging for all API requests
- [x] Show clear error messages with troubleshooting tips on failure

### 1.3 Update Styles  
- [x] Add CSS for expanded/fullscreen agent panel mode
- [x] Add CSS for rich data cards inside chat messages
- [x] Add CSS for improved reasoning step visualization with step-dot indicators
- [x] Add typing/streaming animation CSS (thinking-pulse)
- [x] Add smooth slide-in animation for panel opening
- [x] Ensure panel works in expanded mode

### 1.4 Test End-to-End
- [x] Start backend server (port 8081) — verified all endpoints respond
- [x] Start frontend dev server (port 5173) — verified chatbot renders
- [x] Login as gig worker (Amir Tan) → dashboard shows S$3,547.82 balance, 1 card, 1 loan
- [x] Send "Day Off?" → FinWell agent responds with rich Day Off Analysis card
- [x] Error handling works — shows clear error messages, NO infinite waiting
- [x] Full flow verified end-to-end with proper auth session

---

## Phase 2: Enhance Agent Intelligence (Priority 2) [COMPLETE ✅]

### 2.1 LLM Integration (Gemini) — IF API key available
- [x] Create `backend-python/com/gxs/bank/agent/llm_client.py` — Gemini API wrapper
- [x] Add `.env.example` variable: `GEMINI_API_KEY=`
- [x] Update `supervisor.py` — use LLM for intent classification with keyword fallback
- [x] Update `finwell_agent.py` — use LLM to generate conversational responses from tool data
- [x] Update `fraudshield_agent.py` — use LLM for natural language fraud explanations
- [x] Add `google-generativeai` to `requirements.txt`
- [x] Tested — rule-based responses work perfectly when no API key
- [x] Graceful fallback implemented — works with or without API key

### 2.2 Conversation Memory
- [x] Create `backend-python/com/gxs/bank/agent/memory.py` — in-memory conversation store
- [x] Store last 10 conversation turns per user (sliding window)
- [x] Pass conversation context to agent for follow-up queries
- [x] Add API endpoints: GET + DELETE `/api/agent/conversation-history`

### 2.3 Financial Goals
- [x] Add `POST /api/agent/goal` endpoint to `AgentController.py`
- [x] Add `GET /api/agent/goals` endpoint
- [x] Add `DELETE /api/agent/goal/{goal_id}` endpoint
- [x] In-memory goal storage with UUID-based IDs
- [x] Frontend API methods added: createGoal, getGoals, deleteGoal
- [ ] Connect goals to FinWell agent for personalized recommendations (optional enhancement)
- [ ] Add goal management in chatbot ("Set a savings goal of S$5000") (optional enhancement)

---

## Phase 3: Demo Polish (Priority 3)

### 3.1 Demo Data Enhancement
- [x] Update `DataSeeder.py` — added dedicated gig worker user profile
  - Name: "Amir Tan" (Grab Driver) — email: amir@demo.com / password: password
  - Pre-seeded savings account (S$3,547.82 balance)
  - Pre-seeded 60 days of mock gig transactions (Grab rides + food delivery)
  - Active FlexiLoan (S$5,000, 12 months, 6% interest)
  - Active debit card (VISA ending 3388)
  - 2 fraud scenario transactions (foreign electronics purchase + overseas ATM withdrawal)
  - 17 spending transactions (fuel, meals, rent, phone, maintenance)
- [x] Added rich notification seeds (welcome, security alert, financial tips, EMI reminder)
- [x] Updated LoginPage.jsx with correct demo credentials
- [x] Verified all demo scenarios work with seeded data

### 3.2 Demo Scenario Testing
- [x] **Scenario 1**: "Can I afford to take a day off tomorrow?"
  - FinWell agent analyzed income pattern → showed Day Off Analysis card → gave recommendation
  - Response: "Tight" with weekly surplus of S$-253.93, best day Thursday
  - Reasoning log link visible
- [ ] **Scenario 2**: "Scan my account for suspicious activity"
  - FraudShield runs anomaly detection → detects fraud transactions → recommends card freeze
  - User says "Freeze my cards" → agent freezes cards → sends notification
  - Reasoning log shows intervention chain
- [ ] **Scenario 3**: "Give me your best financial advice"
  - Agent collects all data → generates comprehensive financial health report
  - Shows income trend, savings rate, spending analysis, personalized tips

### 3.3 UI Polish
- [ ] Add micro-animations for data cards appearing in chat
- [ ] Smooth scrolling for new messages
- [ ] Add timestamp formatting for messages
- [ ] Add "powered by FinWell + FraudShield" branding in chat
- [ ] Ensure responsive design works on common screen sizes

---

## Phase 4: Deliverables (Priority 4)

### 4.1 README
- [ ] Rewrite `README.md` with hackathon-quality content:
  - Problem statement
  - Solution overview + what makes it unique
  - Architecture diagram
  - Tech stack with justification
  - Setup & run instructions
  - Demo walkthrough with screenshots
  - Team info

### 4.2 Architecture Diagram
- [ ] Generate clean architecture diagram (image or Mermaid)
- [ ] Show: React Frontend → FastAPI Backend → Agent Layer → Tools → DB/ML

### 4.3 PPT (2 slides)
- [ ] Slide 1: Problem + Opportunity
- [ ] Slide 2: Architecture + Demo Highlights

### 4.4 Video (2 minutes)
- [ ] Record screen demo of all 3 scenarios
- [ ] Add voiceover explaining the agent's reasoning
- [ ] Edit and finalize

### 4.5 Final Submission
- [ ] Final testing of all features
- [ ] Clean up code (remove debug prints, unused imports)
- [ ] Commit and push
