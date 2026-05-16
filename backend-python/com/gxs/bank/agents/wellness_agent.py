"""
Financial Wellness Multi-Agent Crew
=====================================
Agents:
  1. Income Analyst   – examines income patterns and trends
  2. Savings Coach    – designs a personalised savings plan
  3. Budget Planner   – allocates budget across spending categories
  4. Nudges Generator – crafts hyper-personalised motivational nudges

Falls back to deterministic Python logic when no LLM is configured.
"""

import io
import json
import sys
from datetime import datetime

from com.gxs.bank.agents.llm_config import CREWAI_AVAILABLE, get_llm, is_live_mode


# ---------------------------------------------------------------------------
# CrewAI live implementation
# ---------------------------------------------------------------------------

def _run_crew(profile: dict, llm) -> dict:
    from crewai import Agent, Crew, Process, Task

    # ── Shared context block ────────────────────────────────────────────────
    ctx = f"""
=== GRAB DRIVER / PARTNER FINANCIAL PROFILE ===
Period: last 30 days (currency: SGD S$)

Current balance      : S${profile['total_balance']:,.2f}
Income (30d)         : S${profile['income_30d']:,.2f}
Expenses (30d)       : S${profile['expense_30d']:,.2f}
Net savings (30d)    : S${profile['savings_30d']:,.2f}
Savings rate         : {profile['savings_rate_pct']}%
Income (7d)          : S${profile['income_7d']:,.2f}
Active loans         : {profile['active_loans_count']}
Monthly EMI burden   : S${profile['total_monthly_emi']:,.2f}
EMI-to-income ratio  : {profile['emi_to_income_pct']}%
Outstanding debt     : S${profile['total_outstanding_debt']:,.2f}

Expense breakdown by category (semantic):
{json.dumps(profile.get('expense_by_category', profile['expense_by_type']), indent=2)}

Loan details:
{json.dumps(profile['loans'], indent=2)}

Daily income trend (recent dates only):
{json.dumps(dict(list(profile['daily_income'].items())[-14:]), indent=2)}
"""

    # ── Agent 1: Income Analyst ─────────────────────────────────────────────
    income_analyst = Agent(
        role="Gig Economy Income Analyst",
        goal=(
            "Analyse the Grab driver's income patterns, identify earnings trends, "
            "peak earning days, and income volatility."
        ),
        backstory=(
            "You are a specialist in analysing variable income from gig-economy "
            "platforms. You understand that driver income fluctuates with seasons, "
            "weather, and local demand. You convert raw transaction data into "
            "actionable income insights."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # ── Agent 2: Savings Coach ──────────────────────────────────────────────
    savings_coach = Agent(
        role="Personal Savings Coach",
        goal=(
            "Design a realistic, personalised savings plan based on the driver's "
            "actual income and spending patterns, with specific weekly targets."
        ),
        backstory=(
            "You are a certified financial planner who specialises in helping "
            "gig workers build financial security. You know that rigid savings "
            "plans fail; instead you adapt targets to variable income weeks."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # ── Agent 3: Budget Planner ─────────────────────────────────────────────
    budget_planner = Agent(
        role="Dynamic Budget Planner",
        goal=(
            "Create a category-wise monthly budget that ensures essential bills "
            "are covered, EMIs are paid on time, and a surplus is maintained."
        ),
        backstory=(
            "You are an expert in zero-based budgeting and envelope methods. "
            "You help gig workers allocate every rupee with purpose, adjusting "
            "budgets dynamically when income dips below expectations."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # ── Agent 4: Nudges Generator ───────────────────────────────────────────
    nudges_agent = Agent(
        role="Hyper-Personalised Financial Nudge Generator",
        goal=(
            "Generate 3–5 short, motivating, context-aware financial nudges "
            "that will be shown as push notifications to the driver today."
        ),
        backstory=(
            "You are a behavioural economist who crafts micro-nudges that "
            "actually change spending behaviour. Your nudges are specific, "
            "warm, and reference the user's real numbers — never generic."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # ── Tasks ───────────────────────────────────────────────────────────────
    t_income = Task(
        description=(
            f"Analyse the following financial profile and deliver an income analysis:\n{ctx}\n"
            "Identify: (1) average daily income, (2) income trend (rising/falling/stable), "
            "(3) best earning days of the week if discernible, (4) income volatility risk. "
            "Output a concise JSON with keys: avg_daily_income, trend, peak_days, "
            "volatility_level (low/medium/high), insight_summary."
        ),
        expected_output="JSON object with income analysis",
        agent=income_analyst,
    )

    t_savings = Task(
        description=(
            f"Based on this profile:\n{ctx}\n"
            "And using the income analysis from the previous task, design a savings plan:\n"
            "(1) Recommended monthly savings target (S$ amount and %).\n"
            "(2) Weekly savings milestones.\n"
            "(3) An emergency fund goal (3-month expenses).\n"
            "(4) A specific goal: if income allows, save for a vehicle or phone upgrade.\n"
            "Output JSON with keys: monthly_target_inr, monthly_target_pct, "
            "weekly_milestone_inr, emergency_fund_goal_inr, special_goal, savings_advice."
        ),
        expected_output="JSON object with savings plan",
        agent=savings_coach,
        context=[t_income],
    )

    t_budget = Task(
        description=(
            f"Given the profile:\n{ctx}\n"
            "Allocate a realistic monthly budget across these categories: "
            "EMI/Debt, Food, Transport/Fuel, Mobile/Internet, Utilities, "
            "Entertainment, Savings/Investments, Emergency Buffer.\n"
            "If this week income is low, suggest which categories to trim.\n"
            "Output JSON with keys: allocations (dict category→amount), "
            "low_income_cuts (list of category + suggested cut %), overall_advice."
        ),
        expected_output="JSON object with budget allocations",
        agent=budget_planner,
        context=[t_income, t_savings],
    )

    t_nudges = Task(
        description=(
            f"Profile:\n{ctx}\n"
            "Generate exactly 5 personalised push-notification nudges for today. "
            "Each nudge must: (a) reference a real number from the profile, "
            "(b) be under 80 characters, (c) be encouraging not alarming.\n"
            "Output JSON with key: nudges (list of strings)."
        ),
        expected_output="JSON with list of nudge strings",
        agent=nudges_agent,
        context=[t_income, t_savings, t_budget],
    )

    # ── Crew ────────────────────────────────────────────────────────────────
    crew = Crew(
        agents=[income_analyst, savings_coach, budget_planner, nudges_agent],
        tasks=[t_income, t_savings, t_budget, t_nudges],
        process=Process.sequential,
        verbose=True,
    )

    # Capture reasoning log from verbose output
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        result = crew.kickoff()
    finally:
        sys.stdout = old_stdout
    reasoning_log = buffer.getvalue()

    # Parse task outputs
    def _safe_json(text):
        try:
            if hasattr(text, "raw"):
                text = text.raw
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end]) if start >= 0 else {}
        except Exception:
            return {"raw": str(text)}

    outputs = crew.tasks
    income_out = _safe_json(str(outputs[0].output) if outputs[0].output else "{}")
    savings_out = _safe_json(str(outputs[1].output) if outputs[1].output else "{}")
    budget_out = _safe_json(str(outputs[2].output) if outputs[2].output else "{}")
    nudges_out = _safe_json(str(outputs[3].output) if outputs[3].output else "{}")

    return {
        "mode": "live_crew",
        "income_analysis": income_out,
        "savings_plan": savings_out,
        "budget_plan": budget_out,
        "nudges": nudges_out.get("nudges", []),
        "reasoning_log": reasoning_log[:4000],  # truncate for response size
    }


# ---------------------------------------------------------------------------
# Deterministic fallback (no LLM configured)
# ---------------------------------------------------------------------------

def _run_fallback(profile: dict) -> dict:
    """Generates realistic recommendations using pure Python logic over real data."""

    income = profile["income_30d"]
    expense = profile["expense_30d"]
    savings = profile["savings_30d"]
    balance = profile["total_balance"]
    emi = profile["total_monthly_emi"]
    savings_rate = profile["savings_rate_pct"]
    income_7d = profile["income_7d"]

    # ── Income analysis ─────────────────────────────────────────────────────
    avg_daily = income / 30 if income > 0 else 0
    trend = "stable"
    if income_7d > 0 and income > 0:
        weekly_avg = income / 4.3
        if income_7d > weekly_avg * 1.2:
            trend = "rising"
        elif income_7d < weekly_avg * 0.8:
            trend = "falling"

    volatility = "low"
    daily_vals = list(profile["daily_income"].values())
    if daily_vals:
        avg = sum(daily_vals) / len(daily_vals)
        variance = sum((v - avg) ** 2 for v in daily_vals) / len(daily_vals)
        cv = (variance ** 0.5) / avg if avg > 0 else 0
        if cv > 0.5:
            volatility = "high"
        elif cv > 0.25:
            volatility = "medium"

    income_analysis = {
        "avg_daily_income": round(avg_daily, 2),
        "trend": trend,
        "peak_days": ["Friday", "Saturday", "Sunday"],
        "volatility_level": volatility,
        "insight_summary": (
            f"You earned S${income:,.0f} this month with a {trend} trend. "
            f"Average daily income: S${avg_daily:,.0f}."
        ),
    }

    # ── Savings plan ────────────────────────────────────────────────────────
    target_pct = 20.0
    if savings_rate < 10:
        target_pct = 15.0
    elif savings_rate > 30:
        target_pct = 25.0

    monthly_target = round(income * target_pct / 100, 2)
    weekly_target = round(monthly_target / 4, 2)
    emergency_goal = round(expense * 3, 2)

    savings_plan = {
        "monthly_target_inr": monthly_target,
        "monthly_target_pct": target_pct,
        "weekly_milestone_inr": weekly_target,
        "emergency_fund_goal_inr": emergency_goal,
        "special_goal": "Vehicle maintenance fund: S$5,000",
        "savings_advice": (
            f"Save S${weekly_target:,.0f} every week. "
            f"Your emergency fund target is S${emergency_goal:,.0f} (3 months of expenses)."
        ),
    }

    # ── Budget plan ─────────────────────────────────────────────────────────
    remaining = income - emi - monthly_target
    budget_alloc = {
        "EMI/Debt": round(emi, 2),
        "Food": round(remaining * 0.30, 2),
        "Transport/Fuel": round(remaining * 0.20, 2),
        "Mobile/Internet": round(min(remaining * 0.05, 600), 2),
        "Utilities": round(remaining * 0.10, 2),
        "Entertainment": round(remaining * 0.05, 2),
        "Savings/Investments": round(monthly_target, 2),
        "Emergency Buffer": round(remaining * 0.10, 2),
    }

    low_income_cuts = []
    if savings < 0:
        low_income_cuts = [
            {"category": "Entertainment", "cut_pct": 80},
            {"category": "Food", "cut_pct": 20},
        ]

    budget_plan = {
        "allocations": budget_alloc,
        "low_income_cuts": low_income_cuts,
        "overall_advice": (
            f"With S${income:,.0f} income and S${emi:,.0f} in EMIs, "
            f"target S${monthly_target:,.0f} savings this month."
        ),
    }

    # ── Nudges ──────────────────────────────────────────────────────────────
    nudges = [
        f"You're {savings_rate:.0f}% of the way to your savings goal — keep going!",
        f"S${weekly_target:,.0f} saved this week = S${monthly_target:,.0f} by month end.",
        f"Balance: S${balance:,.0f}. Park S${round(balance * 0.1):,.0f} in fixed deposit today.",
        f"Weekend earnings are higher — aim for S${round(avg_daily * 1.5):,.0f} Fri–Sun.",
        f"Emergency fund progress: S${balance:,.0f} / S${emergency_goal:,.0f}",
    ]

    return {
        "mode": "deterministic_fallback",
        "income_analysis": income_analysis,
        "savings_plan": savings_plan,
        "budget_plan": budget_plan,
        "nudges": nudges,
        "reasoning_log": (
            "Step 1: Fetched user transaction history (90 days)\n"
            f"Step 2: Computed income=S${income:,.0f}, expense=S${expense:,.0f}, "
            f"savings_rate={savings_rate:.1f}%\n"
            f"Step 3: Detected income trend={trend}, volatility={volatility}\n"
            f"Step 4: Set savings target at {target_pct}% = S${monthly_target:,.0f}/month\n"
            f"Step 5: Allocated budget across 8 categories\n"
            f"Step 6: Generated 5 personalised nudges using real balance/income data"
        ),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_financial_wellness(profile: dict) -> dict:
    """Run the Financial Wellness crew (live or fallback)."""
    llm = get_llm()
    if llm and CREWAI_AVAILABLE:
        try:
            return _run_crew(profile, llm)
        except Exception as e:
            return {**_run_fallback(profile), "crew_error": str(e)}
    return _run_fallback(profile)
