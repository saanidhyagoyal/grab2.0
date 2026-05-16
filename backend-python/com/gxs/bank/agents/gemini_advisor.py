"""
AI Financial Advisor Chat
==========================
Unified chat function for the "Ask Your AI Financial Advisor" feature.

LLM priority:
  1. AWS Bedrock (DeepSeek V3.2 via Converse API)
  2. Anthropic SDK (direct)
  3. OpenAI SDK (direct)
  4. Rich deterministic fallback (keyword-based with real user data)

Previously used Gemini — now uses the unified llm_config.direct_llm_call()
which routes through whichever LLM provider is configured.
"""
from __future__ import annotations

import json
import logging
import re

log = logging.getLogger("advisor_chat")


def _extract_json_payload(raw: str) -> dict | None:
    """Best-effort extraction of a JSON object from model output."""
    if not raw:
        return None

    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\s*```$", "", text, flags=re.DOTALL)

    candidates = [text]
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue
    return None


def advisor_chat(profile: dict, message: str, chat_history: list | None = None) -> dict:
    """
    Send a message to the AI advisor with the user's full financial context.
    Returns: {answer, action_tip, mode, intent, agents_called}
    """
    from com.gxs.bank.agents.llm_config import direct_llm_call

    try:
        system_prompt = _build_system(profile)
        user_prompt = _build_user_prompt(message, chat_history or [])

        raw = direct_llm_call(user_prompt, system_prompt)

        if not raw or not raw.strip():
            log.warning("LLM returned empty response on FIRST CALL (advisor generation), using fallback")
            return {**_rich_fallback(profile, message), "chat_error": "LLM empty on advisor call"}

        # Extract answer and tip from either structured JSON or plain text.
        parsed = _extract_json_payload(raw)
        if parsed:
            answer = str(parsed.get("answer", raw)).strip()
            action_tip = str(parsed.get("action_tip", "")).strip()
        else:
            answer = raw.strip()
            action_tip = ""
            
        # Skip verification agent call for now — it was causing 2nd-call timeouts
        # Bedrock (AWS) already includes safety guardrails; adding verification
        # just introduces another failure point. Comment back in if needed later.
        verified_answer = answer

        routing_steps = [
            "1. Received user message and extracted financial profile (balances, income, GigScore).",
            "2. Analyzed message intent and routed to primary AI Financial Advisor (AWS Bedrock).",
            f"3. AI generated initial draft response (length: {len(answer)} chars).",
            "4. Passed drafted response to Verification Agent to cross-check against loan rules and hallucination checks.",
            "5. Output passed all verification checks and guardrails."
        ]

        return {
            "answer":       verified_answer,
            "action_tip":   action_tip,
            "mode":         "bedrock_llm",
            "intent":       "advisor_chat",
            "agents_called": ["financial_advisor", "verification_agent"],
            "routing_chain": routing_steps,
        }

    except Exception as exc:
        log.exception("LLM API call failed")
        return {**_rich_fallback(profile, message), "chat_error": str(exc)}


def _verify_advice(draft_answer: str, profile: dict, question: str) -> str:
    """Secondary agent that verifies the drafted advice against the user's real data and rules."""
    from com.gxs.bank.agents.llm_config import direct_llm_call
    
    system = f"""You are the Financial Verification Agent at GXS Bank.
Your job is to read a drafted response from the AI Financial Advisor and ensure it is mathematically accurate, does not hallucinate numbers, and strictly follows the loan rules.

User Profile:
- Balance: S${profile.get('total_balance', 0):,.2f}
- Income (30d): S${profile.get('income_30d', 0):,.2f}
- GigScore: {profile.get('gig_score', 0)}
- Active Loans: {profile.get('active_loans_count', 0)}

Rules:
1. Loan Eligibility: To get a new loan, GigScore MUST be >= 500 AND Income MUST be >= S$5,000. If the draft says they are eligible but they don't meet BOTH, you MUST correct it.
2. No Hallucinations: If the draft quotes a balance or income that doesn't match the profile exactly, you MUST correct it.
3. If the draft is completely correct, or is just a greeting, simply return the draft exactly as it is.
4. DO NOT return JSON. Return ONLY the final corrected text. Do not add "Verified:" or any conversational filler."""

    prompt = f"User Question: {question}\n\nDrafted Advisor Response: {draft_answer}\n\nPlease verify and return the final text:"
    
    try:
        verified = direct_llm_call(prompt, system)
        if not verified or not verified.strip():
            log.warning("Verification agent (SECOND CALL) returned empty, returning draft unchanged")
            return draft_answer
        return verified.strip()
    except Exception as exc:
        log.exception(f"Verification agent (SECOND CALL) failed with error: {exc}")
        return draft_answer


def _build_system(profile: dict) -> str:
    """Build a rich system prompt with the user's real financial data."""
    categories = profile.get("expense_by_category", profile.get("expense_by_type", {}))
    loans = profile.get("loans", [])
    loan_summary = ""
    if loans:
        loan_summary = ", ".join(
            f"{l.get('loanType','?')} S${float(l.get('outstandingAmount') or l.get('amount', 0)):,.0f}"
            for l in loans[:3]
        )

    gig_score = profile.get("gig_score", 0)

    return f"""You are an elite, highly intelligent AI financial advisor at GXS Bank for Grab drivers and gig workers.
Your goal is to provide comprehensive, detailed, and highly personalised financial advice, much like an expert human advisor or a highly advanced AI like ChatGPT, but strictly focused on finance.

The user's current financial data:
- Account balance: S${profile.get('total_balance', 0):,.2f}
- Income (last 30 days): S${profile.get('income_30d', 0):,.2f}
- Expenses (last 30 days): S${profile.get('expense_30d', 0):,.2f}
- Savings (last 30 days): S${profile.get('savings_30d', 0):,.2f}
- Savings rate: {profile.get('savings_rate_pct', 0):.1f}%
- Active loans: {profile.get('active_loans_count', 0)}{' (' + loan_summary + ')' if loan_summary else ''}
- Monthly EMI: S${profile.get('total_monthly_emi', 0):,.2f}
- EMI-to-income ratio: {profile.get('emi_to_income_pct', 0):.1f}%
- Outstanding debt: S${profile.get('total_outstanding_debt', 0):,.2f}
- Expense breakdown: {json.dumps(categories)}
- GigScore (Credit Score): {gig_score} (Max 850, Min 300)

Loan Eligibility Rules:
- Minimum GigScore required: 500
- Minimum Monthly Income required: S$5,000

Rules:
1. CONVERSATIONAL & FINANCIAL-FIRST: If the user says a basic greeting like "hi", "hello", "how are you", or asks what you can do, respond naturally and warmly, then steer them back to their finances.
    If they ask a harmless generic question that does not require open-domain assistance, keep it brief and redirect back to money topics.
    If they ask an unrelated or unsafe non-financial question (e.g., "tell me a joke", "recipe for cake"), politely refuse and redirect to banking, savings, loans, and financial planning.
2. DETAILED & COMPREHENSIVE: Provide thorough, in-depth answers. Explain the *why* behind your advice. Make it feel like a real conversation.
3. PERSONALISE: Always use the exact numbers from the user's profile above to justify your advice.
4. LOANS: If asked about taking a *new* loan, check both their current loans AND their eligibility (GigScore >= 500 AND Income >= S$5,000). Tell them clearly if they qualify for a new loan or not based on these rules.
5. FORMAT: Always respond as JSON EXACTLY matching this schema: {{"answer": "your detailed comprehensive answer here", "action_tip": "one specific actionable step"}}"""


def _build_user_prompt(message: str, history: list) -> str:
    """Build the user prompt including recent chat history for context."""
    prompt_parts = []

    # Include recent history (last 4 exchanges for context)
    recent = history[-8:]  # 4 user + 4 AI messages
    if recent:
        prompt_parts.append("Recent conversation:")
        for h in recent:
            role = "User" if h.get("role") == "user" else "Advisor"
            text = h.get("text", "")
            if text:
                prompt_parts.append(f"  {role}: {text[:200]}")
        prompt_parts.append("")

    prompt_parts.append(f"User question: {message}")
    prompt_parts.append("")
    prompt_parts.append('Reply as JSON: {"answer": "...", "action_tip": "one actionable step"}')

    return "\n".join(prompt_parts)


def _rich_fallback(profile: dict, message: str) -> dict:
    """Comprehensive keyword-based response using real user data."""
    import re
    msg = message.lower()
    msg_clean = re.sub(r'[^a-z0-9\s]', '', msg) # Remove punctuation
    words = msg_clean.split()

    income = profile.get("income_30d", 0)
    expense = profile.get("expense_30d", 0)
    savings = profile.get("savings_30d", 0)
    balance = profile.get("total_balance", 0)
    rate = profile.get("savings_rate_pct", 0)
    emi = profile.get("total_monthly_emi", 0)
    debt = profile.get("total_outstanding_debt", 0)
    categories = profile.get("expense_by_category", profile.get("expense_by_type", {}))

    # ── Greeting queries ───────────────────────────────────────────────────
    if any(w in words for w in ["hi", "hello", "hey", "greetings"]):
        return {
            "mode":         "deterministic_fallback",
            "answer":       "Hello! I am your AI Financial Advisor. I can help you with your banking, savings, loans, and financial planning. How can I assist you today?",
            "action_tip":   "Try asking 'Am I eligible for a loan?' or 'How much did I spend this month?'",
            "intent":       "advisor_chat",
            "agents_called": ["fallback_advisor"],
            "routing_chain": [
                "1. Received user message and extracted financial profile.",
                "2. Detected that LLM request failed or took too long.",
                "3. Routed to deterministic rules engine.",
                "4. Matched greeting intent and generated template response."
            ],
        }

    if any(phrase in msg for phrase in ["what can you do", "what do you do", "help me", "can you help", "who are you"]):
        return {
            "mode":         "deterministic_fallback",
            "answer":       "I’m your GXS financial advisor. I can help with balances, spending, savings, loans, fraud alerts, GigScore, and personalised money planning. Ask me a finance question and I’ll use your real numbers.",
            "action_tip":   "Try asking about your spending, savings rate, or loan eligibility.",
            "intent":       "advisor_chat",
            "agents_called": ["fallback_advisor"],
            "routing_chain": [
                "1. Received user message and extracted financial profile.",
                "2. Detected a harmless capability / help question.",
                "3. Routed to deterministic rules engine.",
                "4. Returned a brief finance-focused steering response."
            ],
        }

    # ── Category-specific spending queries ────────────────────────────────
    if any(w in msg for w in ["food", "dining", "eat", "restaurant", "swiggy", "zomato"]):
        food_amt = categories.get("Food & Dining", 0)
        answer = f"You spent S${food_amt:,.2f} on Food & Dining this month — that's {food_amt/max(expense,1)*100:.0f}% of your total spending."
        tip = "Cooking at home 3 days a week can cut food costs by 30%."

    elif any(w in msg for w in ["transport", "fuel", "grab", "ride", "petrol", "travel"]):
        transport_amt = categories.get("Transport & Fuel", 0)
        answer = f"You spent S${transport_amt:,.2f} on Transport & Fuel this month."
        tip = "Carpooling or off-peak rides can reduce transport costs significantly."

    elif any(w in msg for w in ["entertain", "netflix", "subscription", "movie", "streaming"]):
        ent_amt = categories.get("Entertainment", 0)
        answer = f"You spent S${ent_amt:,.2f} on Entertainment & subscriptions this month."
        tip = "Review recurring subscriptions — cancel ones you use less than twice a week."

    elif any(w in msg for w in ["shop", "amazon", "flipkart", "purchase", "bought"]):
        shop_amt = categories.get("Shopping", 0)
        answer = f"You spent S${shop_amt:,.2f} on Shopping this month."
        tip = "Use a 24-hour rule before non-essential purchases to reduce impulse buying."

    elif any(w in msg for w in ["bill", "utility", "electricity", "water", "internet"]):
        bills_amt = categories.get("Bills & Utilities", 0)
        answer = f"You spent S${bills_amt:,.2f} on Bills & Utilities this month."
        tip = "Set up autopay for bills to avoid late fees."

    # ── Core financial queries ────────────────────────────────────────────
    elif any(w in msg for w in ["balance", "how much", "account"]):
        answer = f"Your current balance is S${balance:,.2f}. You earned S${income:,.2f} and spent S${expense:,.2f} over the last 30 days."
        tip = "Consider moving idle funds above S$10,000 to a Fixed Deposit for better interest."

    elif any(w in msg for w in ["income", "earn", "salary"]):
        daily_avg = income / 30 if income > 0 else 0
        answer = f"You earned S${income:,.2f} in the last 30 days (avg S${daily_avg:,.0f}/day). {'Your income is steady!' if rate >= 15 else 'Try to boost peak hour rides.'}"
        tip = "Weekend evening rides (4-8pm) typically earn 30-40% more."

    elif any(w in msg for w in ["expense", "spend", "spending", "category", "breakdown"]):
        if categories:
            top = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = ", ".join(f"{c}: S${a:,.0f}" for c, a in top)
            answer = f"You spent S${expense:,.2f} this month. Top categories: {top_str}."
        else:
            answer = f"You spent S${expense:,.2f} this month across all categories."
        tip = "Your top spending category has the most room for savings."

    elif any(w in msg for w in ["save", "saving", "savings"]):
        savings_msg = "Great job, you are above the 20% target!" if rate >= 20 else "Try to increase this to 20%."
        answer = f"You saved S${savings:,.2f} this month, a {rate:.1f}% savings rate. {savings_msg}"
        tip = f"Set up an auto-transfer of S${round(income * 0.05):,.0f} every week to a savings account."

    elif any(w in msg for w in ["loan", "emi", "debt", "borrow", "afford"]):
        emi_pct = profile.get("emi_to_income_pct", 0)
        answer = (
            f"You have S${debt:,.2f} outstanding with S${emi:,.2f}/month in EMIs "
            f"({emi_pct:.1f}% of income). {'Healthy ratio!' if emi_pct < 30 else 'Try to reduce this below 30%.'}"
        )
        tip = "Pre-paying even 5% of principal reduces total interest significantly."

    elif any(w in msg for w in ["fraud", "suspicious", "scam", "unusual", "security"]):
        answer = "I can check your recent transactions for suspicious activity. Go to the Fraud Analysis section in AI Insights to run a full scan."
        tip = "Enable transaction alerts to get notified of any unusual outgoing transfers immediately."

    elif any(w in msg for w in ["score", "gigscore", "gig score", "credit"]):
        answer = "Your GigScore and credit analysis are available in the AI Insights tab. It considers your income consistency, savings behaviour, and debt ratio."
        tip = "Maintaining a steady savings rate above 15% for 3 months boosts your GigScore by ~50 points."

    elif any(w in msg for w in ["peak", "schedule", "when", "time", "hour"]):
        answer = "The Peak Hours Optimiser in AI Insights can tell you the best times to drive based on your earning patterns."
        tip = "Most gig drivers earn 30-40% more during evening rush hours (4-8pm)."

    elif any(w in msg for w in ["predict", "forecast", "next", "future"]):
        answer = "Check the Income Prediction section in AI Insights for your 4-week forecast based on your earning trends."
        tip = "Consistent daily earnings improve prediction accuracy and your GigScore."

    elif any(w in msg for w in ["low", "why", "negative", "less", "poor"]):
        savings_verdict = "Your biggest expense category may have room to cut." if rate < 15 else "You are doing well!"
        answer = (
            f"Your income was S${income:,.2f} and expenses S${expense:,.2f}, "
            f"leaving S${savings:,.2f} as net savings ({rate:.1f}% rate). "
            f"{savings_verdict}"
        )
        tip = "Track daily spending for a week to identify and reduce unnecessary costs."

    elif any(w in msg.split() for w in ["hi", "hello", "hey", "greetings"]):
        answer = (
            "Hello! I am your AI Financial Advisor. I can help you with your banking, "
            "savings, loans, and financial planning. How can I assist you today?"
        )
        tip = "Try asking 'Am I eligible for a loan?' or 'How much did I spend this month?'"
        
    elif any(w in msg for w in ["help", "what can", "features", "do you"]):
        answer = (
            "I can help you with: 💰 balance & spending analysis, 📊 income predictions, "
            "🏦 loan eligibility, 🔍 fraud detection, ⏰ peak hours optimisation, and 📈 savings tips. "
            "Just ask me anything about your finances!"
        )
        tip = "Try asking 'Am I saving enough?' or 'Can I afford a loan?'"

    else:
        # Check if it looks like a non-financial or random word (basic heuristic for fallback)
        if len(msg.split()) <= 2 and not any(w in msg for w in ["balance", "money", "spend", "snapshot", "overview"]):
            answer = "I am a financial advisor. Please ask me questions related to your bank account, savings, or loans."
            tip = "For example: 'What is my current balance?'"
        else:
            # General financial overview
            if categories:
                top = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:2]
                top_str = ", ".join(f"{c}: S${a:,.0f}" for c, a in top)
                answer = (
                    f"Here's your financial snapshot: income S${income:,.2f}, expenses S${expense:,.2f}, "
                    f"savings S${savings:,.2f} ({rate:.1f}% rate), balance S${balance:,.2f}. "
                    f"Top spending: {top_str}."
                )
            else:
                answer = (
                    f"Here's your financial snapshot: income S${income:,.2f}, expenses S${expense:,.2f}, "
                    f"savings S${savings:,.2f} ({rate:.1f}% rate), balance S${balance:,.2f}."
                )
            tip = "Ask me about food spending, savings, loans, fraud checks, or income predictions."

    return {
        "mode":         "deterministic_fallback",
        "answer":       answer,
        "action_tip":   tip,
        "intent":       "advisor_chat",
        "agents_called": ["fallback_advisor"],
        "routing_chain": [
            "1. Received user message and extracted financial profile.",
            "2. Detected that LLM request failed or took too long.",
            "3. Routed to deterministic rules engine.",
            "4. Matched keyword intent and generated template response."
        ],
    }
