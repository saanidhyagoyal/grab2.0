"""
Fraud Detection Multi-Agent Crew
===================================
Agents:
  1. Anomaly Detector   – spots unusual transaction patterns using rolling 30-day window
  2. Risk Assessor      – scores overall account risk level (0-100)
  3. Mitigation Advisor – recommends concrete protective actions

Falls back to rule-based detection when no LLM is configured.

Rolling window:
  All anomaly baselines (average transaction, income baseline, spending norms)
  are computed from the last 30 days only, not full history.
  This ensures the detector responds to recent behavioural changes.
"""

import io
import json
import sys
from datetime import datetime, timedelta

from com.gxs.bank.agents.llm_config import CREWAI_AVAILABLE, get_llm


# ---------------------------------------------------------------------------
# Rolling 30-day window helper
# ---------------------------------------------------------------------------

# Transaction types that represent money leaving the account (fraud-relevant)
_OUTGOING_TYPES = {
    "DEBIT", "TRANSFER_OUT", "UPI_DEBIT", "ATM_WITHDRAWAL",
    "POS_PURCHASE", "BILL_PAYMENT", "EMI",
}


def _build_30d_window(profile: dict) -> dict:
    """
    Extract the rolling 30-day transaction subset from the full profile.
    Anomaly detection baselines are computed from OUTGOING transactions only —
    incoming money (salary, transfers in) is not a fraud signal.
    """
    cutoff = datetime.utcnow() - timedelta(days=30)
    all_txns = profile.get("recent_transactions", [])

    # Filter to 30-day window (recent_transactions already sorted desc by date)
    window = [
        t for t in all_txns
        if t.get("date") and datetime.fromisoformat(t["date"].replace("Z", "")) >= cutoff
    ]

    if not window:
        window = all_txns[:20]  # fallback: last 20 transactions

    # Separate outgoing transactions for anomaly detection
    outgoing = [t for t in window if t.get("type") in _OUTGOING_TYPES]
    outgoing_amounts = [t["amount"] for t in outgoing if t["amount"] > 0]
    avg_outgoing = sum(outgoing_amounts) / len(outgoing_amounts) if outgoing_amounts else 0
    max_outgoing = max(outgoing_amounts) if outgoing_amounts else 0

    return {
        "transactions": window,
        "outgoing": outgoing,
        "count": len(window),
        "outgoing_count": len(outgoing),
        "avg_amount": round(avg_outgoing, 2),
        "max_amount": round(max_outgoing, 2),
        "income_baseline": profile.get("income_30d", 0),
        "expense_baseline": profile.get("expense_30d", 0),
    }


# ---------------------------------------------------------------------------
# CrewAI live implementation
# ---------------------------------------------------------------------------

def _run_crew(profile: dict, suspect_amount: float, llm) -> dict:
    from crewai import Agent, Crew, Process, Task

    window = _build_30d_window(profile)
    recent_txns_str = json.dumps(window["transactions"][:20], indent=2)
    suspicious_str = json.dumps(profile["suspicious_transactions"], indent=2)

    ctx = f"""
=== ACCOUNT FRAUD ANALYSIS CONTEXT (Rolling 30-Day Window) ===
Total balance          : S${profile['total_balance']:,.2f}
Income (30d)           : S${profile['income_30d']:,.2f}
Expense (30d)          : S${profile['expense_30d']:,.2f}
Suspicious amount flag : S${suspect_amount:,.2f}

30-day window stats (anomaly baseline):
  Transactions in window : {window['count']}
  Average amount         : S${window['avg_amount']:,.2f}
  Largest amount         : S${window['max_amount']:,.2f}

Recent transactions (30-day rolling window, latest first):
{recent_txns_str}

Already-flagged large transactions:
{suspicious_str}
"""

    anomaly_detector = Agent(
        role="Financial Anomaly Detector",
        goal=(
            "Identify all unusual, suspicious, or out-of-pattern transactions "
            "in the user's recent activity."
        ),
        backstory=(
            "You are a fraud analyst at GXS Bank trained on millions of transaction "
            "records. You know that gig worker income is variable but expenses "
            "are usually consistent. You spot outliers by comparing against "
            "personal baselines, not just static thresholds."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    risk_assessor = Agent(
        role="Account Risk Assessor",
        goal=(
            "Calculate an overall fraud risk score (0–100) and risk level "
            "(LOW/MEDIUM/HIGH/CRITICAL) for this account."
        ),
        backstory=(
            "You are a risk quantification specialist. You weigh factors including "
            "transaction velocity, geographic anomalies, amount spikes, and "
            "time-of-day patterns to produce a calibrated risk score."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    mitigation_advisor = Agent(
        role="Fraud Mitigation Advisor",
        goal=(
            "Recommend specific, prioritised actions the user and the bank should "
            "take right now to protect the account."
        ),
        backstory=(
            "You are a consumer protection specialist who balances security with "
            "user experience. You never over-react to false positives, but you "
            "act decisively on genuine threats."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    t_anomaly = Task(
        description=(
            f"{ctx}\n"
            "List all anomalies found. For each, state: transaction details, "
            "why it's suspicious, and confidence level (0–1).\n"
            "Output JSON: anomalies (list of {description, amount, reason, confidence}), "
            "total_anomalies_found."
        ),
        expected_output="JSON with anomalies list",
        agent=anomaly_detector,
    )

    t_risk = Task(
        description=(
            f"{ctx}\n"
            "Using the anomalies identified, compute a fraud risk score.\n"
            "Output JSON: risk_score (0–100), risk_level (LOW/MEDIUM/HIGH/CRITICAL), "
            "primary_risk_factor, secondary_factors (list)."
        ),
        expected_output="JSON with risk score",
        agent=risk_assessor,
        context=[t_anomaly],
    )

    t_mitigation = Task(
        description=(
            f"{ctx}\n"
            "Based on risk level, recommend mitigation actions.\n"
            "Output JSON: immediate_actions (list), recommended_actions (list), "
            "should_block_transaction (bool), user_message (friendly string to show user)."
        ),
        expected_output="JSON with mitigation plan",
        agent=mitigation_advisor,
        context=[t_anomaly, t_risk],
    )

    crew = Crew(
        agents=[anomaly_detector, risk_assessor, mitigation_advisor],
        tasks=[t_anomaly, t_risk, t_mitigation],
        process=Process.sequential,
        verbose=True,
    )

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        crew.kickoff()
    finally:
        sys.stdout = old_stdout
    reasoning_log = buffer.getvalue()

    def _safe_json(text):
        try:
            if hasattr(text, "raw"):
                text = text.raw
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end]) if start >= 0 else {}
        except Exception:
            return {"raw": str(text)}

    tasks = crew.tasks
    anomaly_out = _safe_json(str(tasks[0].output) if tasks[0].output else "{}")
    risk_out = _safe_json(str(tasks[1].output) if tasks[1].output else "{}")
    mitigation_out = _safe_json(str(tasks[2].output) if tasks[2].output else "{}")

    return {
        "mode": "live_crew",
        "anomaly_detection": anomaly_out,
        "risk_assessment": risk_out,
        "mitigation": mitigation_out,
        "reasoning_log": reasoning_log[:4000],
    }


# ---------------------------------------------------------------------------
# Rule-based fallback
# ---------------------------------------------------------------------------

def _run_fallback(profile: dict, suspect_amount: float) -> dict:
    income  = profile["income_30d"]
    balance = profile["total_balance"]
    suspicious = profile["suspicious_transactions"]

    # Use rolling 30-day window for baseline computation
    window = _build_30d_window(profile)
    outgoing = window["outgoing"]  # only outgoing transactions are fraud-relevant
    avg_txn = window["avg_amount"] if window["avg_amount"] > 0 else income / max(len(outgoing), 1)

    # Anomaly detection — only on OUTGOING transactions (money leaving the account)
    anomalies = []

    for txn in outgoing:
        amt = txn["amount"]
        reasons = []
        confidence = 0.0

        if amt > avg_txn * 8:
            reasons.append(f"Amount S${amt:,.0f} is 8× above your average transaction")
            confidence = max(confidence, 0.85)

        if txn["type"] in ("TRANSFER_OUT", "UPI_DEBIT") and amt > income * 0.5:
            reasons.append(f"Transfer of S${amt:,.0f} exceeds 50% of monthly income")
            confidence = max(confidence, 0.75)

        if suspect_amount > 0 and abs(amt - suspect_amount) < 1:
            reasons.append(f"Matches flagged amount S${suspect_amount:,.0f}")
            confidence = max(confidence, 0.90)

        if reasons:
            anomalies.append({
                "description": txn.get("description", ""),
                "amount": amt,
                "type": txn["type"],
                "date": txn["date"],
                "reason": "; ".join(reasons),
                "confidence": round(confidence, 2),
            })

    # Add pre-identified suspicious transactions
    for s in suspicious:
        if not any(a["amount"] == s["amount"] for a in anomalies):
            anomalies.append({
                "description": s.get("description", ""),
                "amount": s["amount"],
                "type": s["type"],
                "date": s["date"],
                "reason": "Transaction amount significantly exceeds account baseline",
                "confidence": 0.70,
            })

    # Add synthetic anomaly for large suspect_amount not in recent transactions
    if suspect_amount > 0 and not any(abs(a["amount"] - suspect_amount) < 1 for a in anomalies):
        ratio = suspect_amount / max(income, 1)
        if ratio > 0.3:
            sa_confidence = min(0.5 + ratio * 0.1, 0.97)
            anomalies.append({
                "description": f"Flagged transaction of S${suspect_amount:,.0f}",
                "amount": suspect_amount,
                "type": "TRANSFER_OUT",
                "date": "pending review",
                "reason": f"Suspect amount S${suspect_amount:,.0f} is {ratio:.1f}× monthly income (S${income:,.0f})",
                "confidence": round(sa_confidence, 2),
            })

    # Risk score
    base_score = 0
    if len(anomalies) > 0:
        base_score += min(len(anomalies) * 15, 45)
    max_confidence = max((a["confidence"] for a in anomalies), default=0)
    base_score += int(max_confidence * 40)
    # Scale score based on suspect_amount vs income ratio
    if suspect_amount > 0 and income > 0:
        ratio = suspect_amount / income
        if ratio >= 3:
            base_score += 35    # 3x income = critical
        elif ratio >= 1:
            base_score += 25    # > 1x income = high
        elif ratio >= 0.5:
            base_score += 15    # > 50% income = medium
        elif ratio >= 0.3:
            base_score += 8

    risk_score = min(base_score, 100)
    if risk_score >= 75:
        risk_level = "CRITICAL"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Mitigation
    should_block = risk_score >= 70
    if risk_level == "CRITICAL":
        immediate = [
            "Temporarily block outgoing transfers > S$10,000",
            "Send SMS/email OTP verification to account holder",
            "Escalate to fraud review team",
        ]
        recommended = [
            "Review all transactions in the last 48 hours",
            "Reset UPI PIN and net-banking password",
            "Enable 2-factor authentication",
        ]
        user_msg = (
            f"⚠️ We detected unusual activity (S${suspect_amount:,.0f} flagged). "
            "Your account has been temporarily secured. Please verify via OTP."
        )
    elif risk_level == "HIGH":
        immediate = [
            "Flag transaction for manual review",
            "Send fraud alert to user",
        ]
        recommended = [
            "Temporarily reduce daily transfer limit",
            "Ask user to confirm transaction via in-app verification",
        ]
        user_msg = (
            f"🔔 Unusual transaction of S${suspect_amount:,.0f} detected. "
            "Did you authorise this? Tap to confirm."
        )
    else:
        immediate = ["Log event for monitoring"]
        recommended = ["Continue normal monitoring"]
        user_msg = "Your account activity looks normal. Stay alert to unknown transfers."

    return {
        "mode": "deterministic_fallback",
        "anomaly_detection": {
            "anomalies": anomalies,
            "total_anomalies_found": len(anomalies),
        },
        "risk_assessment": {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "primary_risk_factor": anomalies[0]["reason"] if anomalies else "None detected",
            "secondary_factors": [a["reason"] for a in anomalies[1:3]],
        },
        "mitigation": {
            "immediate_actions": immediate,
            "recommended_actions": recommended,
            "should_block_transaction": should_block,
            "user_message": user_msg,
        },
        "reasoning_log": (
            f"Step 1: Built rolling 30-day window ({window['count']} transactions)\n"
            f"Step 2: 30d baseline — avg txn = S${avg_txn:,.0f}, max = S${window['max_amount']:,.0f}\n"
            f"Step 3: Flagged {len(anomalies)} anomalous transactions\n"
            f"Step 4: Calculated risk score = {risk_score}/100 -> {risk_level}\n"
            f"Step 5: block_transaction = {should_block}\n"
            f"Step 6: Generated user-facing alert message"
        ),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_fraud_check(profile: dict, suspect_amount: float = 0.0) -> dict:
    """Run the Fraud Detection crew (live or fallback)."""
    llm = get_llm()
    if llm and CREWAI_AVAILABLE:
        try:
            return _run_crew(profile, suspect_amount, llm)
        except Exception as e:
            return {**_run_fallback(profile, suspect_amount), "crew_error": str(e)}
    return _run_fallback(profile, suspect_amount)
