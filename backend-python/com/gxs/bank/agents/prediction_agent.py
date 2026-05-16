"""
Income Prediction & Debt Management Multi-Agent Crew
======================================================
Agents:
  1. Trend Analyst     – analyses historical income patterns and seasonality
  2. Income Predictor  – forecasts next 4-week income with confidence bands
  3. Debt Strategist   – recommends EMI adjustments based on predicted income

Falls back to time-series heuristics when no LLM is configured.
"""

import io
import json
import math
import sys
from datetime import datetime, timedelta

from com.gxs.bank.agents.llm_config import CREWAI_AVAILABLE, get_llm


# ---------------------------------------------------------------------------
# CrewAI live implementation
# ---------------------------------------------------------------------------

def _run_crew(profile: dict, llm) -> dict:
    from crewai import Agent, Crew, Process, Task

    daily_income_str = json.dumps(profile["daily_income"], indent=2)
    loans_str = json.dumps(profile["loans"], indent=2)

    ctx = f"""
=== INCOME PREDICTION CONTEXT ===
Income last 30 days    : S${profile['income_30d']:,.2f}
Income last 7 days     : S${profile['income_7d']:,.2f}
Income last 90 days    : S${profile['income_90d']:,.2f}
Monthly EMI burden     : S${profile['total_monthly_emi']:,.2f}
Outstanding debt       : S${profile['total_outstanding_debt']:,.2f}
Savings (30d)          : S${profile['savings_30d']:,.2f}

Daily income (last 30 days):
{daily_income_str}

Active loans:
{loans_str}
"""

    trend_analyst = Agent(
        role="Income Trend & Seasonality Analyst",
        goal=(
            "Identify weekly patterns, seasonal effects, and trend direction "
            "in the Grab driver's income data."
        ),
        backstory=(
            "You are a data scientist specialising in gig-economy time series. "
            "You know that ride-hailing income peaks on weekends, dips during "
            "monsoon, and surges during festivals. You extract these signals "
            "from sparse daily data."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    income_predictor = Agent(
        role="Income Forecaster",
        goal=(
            "Predict next 4 weeks of daily/weekly income with low and high "
            "confidence bounds, flagging weeks likely to be below average."
        ),
        backstory=(
            "You are a quantitative analyst who builds income forecasting models "
            "for micro-finance institutions. You communicate uncertainty clearly "
            "so drivers can plan for both optimistic and pessimistic scenarios."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    debt_strategist = Agent(
        role="Adaptive Debt Repayment Strategist",
        goal=(
            "Recommend EMI adjustments and pre-payment strategies aligned with "
            "predicted income — protecting the driver in bad weeks."
        ),
        backstory=(
            "You are a debt counsellor who helps gig workers avoid defaults. "
            "You negotiate income-linked repayment schedules that flex with "
            "earnings rather than demanding fixed payments regardless of income."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    t_trend = Task(
        description=(
            f"{ctx}\n"
            "Analyse the daily income data. Output JSON: "
            "trend_direction (rising/stable/falling), "
            "avg_weekly_income, peak_days_of_week (list), "
            "low_income_weeks_risk (low/medium/high), "
            "trend_summary."
        ),
        expected_output="JSON with trend analysis",
        agent=trend_analyst,
    )

    t_predict = Task(
        description=(
            f"{ctx}\n"
            "Forecast income for the next 4 weeks. Output JSON: "
            "weekly_predictions (list of 4: {week, predicted_inr, low_inr, high_inr}), "
            "monthly_forecast_inr, confidence_pct, "
            "risk_weeks (list of week numbers with low income risk), "
            "forecast_notes."
        ),
        expected_output="JSON with 4-week income forecast",
        agent=income_predictor,
        context=[t_trend],
    )

    t_debt = Task(
        description=(
            f"{ctx}\n"
            "Using the income forecast, recommend debt management. Output JSON: "
            "emi_is_sustainable (bool), "
            "recommended_prepayment_inr (0 if not advised), "
            "bad_week_strategy (what to do if income drops >30%), "
            "debt_free_in_months, "
            "actionable_steps (list of 3)."
        ),
        expected_output="JSON with debt management plan",
        agent=debt_strategist,
        context=[t_trend, t_predict],
    )

    crew = Crew(
        agents=[trend_analyst, income_predictor, debt_strategist],
        tasks=[t_trend, t_predict, t_debt],
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
    trend_out = _safe_json(str(tasks[0].output) if tasks[0].output else "{}")
    predict_out = _safe_json(str(tasks[1].output) if tasks[1].output else "{}")
    debt_out = _safe_json(str(tasks[2].output) if tasks[2].output else "{}")

    return {
        "mode": "live_crew",
        "trend_analysis": trend_out,
        "income_forecast": predict_out,
        "debt_management": debt_out,
        "reasoning_log": reasoning_log[:4000],
    }


# ---------------------------------------------------------------------------
# Heuristic fallback
# ---------------------------------------------------------------------------

def _simple_moving_average(values: list, window: int = 7) -> float:
    if not values:
        return 0.0
    recent = values[-window:] if len(values) >= window else values
    return sum(recent) / len(recent)


def _run_fallback(profile: dict) -> dict:
    income_30d = profile["income_30d"]
    income_90d = profile["income_90d"]
    income_7d = profile["income_7d"]
    emi = profile["total_monthly_emi"]
    outstanding = profile["total_outstanding_debt"]

    daily_income_map = profile.get("daily_gig_income") or profile.get("daily_income", {})
    daily_vals = list(daily_income_map.values()) if daily_income_map else []

    # ── Trend analysis ──────────────────────────────────────────────────────
    monthly_avg_90d = income_90d / 3 if income_90d > 0 else income_30d
    weekly_avg = income_30d / 4.3

    if income_7d > weekly_avg * 1.2:
        trend = "rising"
    elif income_7d < weekly_avg * 0.8:
        trend = "falling"
    else:
        trend = "stable"

    # Simple volatility
    if daily_vals:
        avg = sum(daily_vals) / len(daily_vals)
        std = math.sqrt(sum((v - avg) ** 2 for v in daily_vals) / len(daily_vals))
        cv = std / avg if avg > 0 else 0
        risk = "high" if cv > 0.5 else "medium" if cv > 0.25 else "low"
    else:
        avg = weekly_avg / 7
        std = avg * 0.3
        cv = 0.3
        risk = "medium"

    trend_analysis = {
        "trend_direction": trend,
        "avg_weekly_income": round(weekly_avg, 2),
        "peak_days_of_week": ["Friday", "Saturday", "Sunday"],
        "low_income_weeks_risk": risk,
        "trend_summary": (
            f"Income trend is {trend}. Weekly average S${weekly_avg:,.0f}. "
            f"Volatility is {risk} (CV={cv:.2f})."
        ),
    }

    # ── Income forecast (4 weeks) ───────────────────────────────────────────
    # Use exponential smoothing: w_new = 0.4*recent + 0.6*historical
    smoothed = weekly_avg * 0.6 + (income_7d or weekly_avg) * 0.4
    weekly_predictions = []
    for i in range(1, 5):
        # Apply slight mean-reversion
        predicted = smoothed * (1 + (monthly_avg_90d - smoothed) / max(monthly_avg_90d, 1) * 0.1 * i)
        uncertainty = std * 7 * (1 + i * 0.1)  # uncertainty grows with horizon
        weekly_predictions.append({
            "week": i,
            "predicted_inr": round(predicted, 2),
            "low_inr": round(max(predicted - uncertainty, 0), 2),
            "high_inr": round(predicted + uncertainty, 2),
        })

    monthly_forecast = round(sum(w["predicted_inr"] for w in weekly_predictions), 2)
    risk_weeks = [w["week"] for w in weekly_predictions if w["low_inr"] < weekly_avg * 0.7]

    income_forecast = {
        "weekly_predictions": weekly_predictions,
        "monthly_forecast_inr": monthly_forecast,
        "confidence_pct": round(max(60, 90 - cv * 100), 1),
        "risk_weeks": risk_weeks,
        "forecast_notes": (
            f"Forecast based on 30-day average of S${income_30d:,.0f}. "
            f"{'Weeks ' + str(risk_weeks) + ' may see lower earnings.' if risk_weeks else 'All weeks look stable.'}"
        ),
    }

    # ── Debt management ─────────────────────────────────────────────────────
    emi_ratio = emi / max(monthly_forecast, 1) * 100
    sustainable = emi_ratio < 40

    months_to_payoff = int(outstanding / max(emi, 1)) if emi > 0 else 0
    surplus = monthly_forecast - profile["expense_30d"]
    prepayment = round(surplus * 0.3, -2) if surplus > emi * 0.5 else 0

    steps = [
        f"Continue paying S${emi:,.0f}/month EMI — you're on track.",
        f"In good weeks (income > S${weekly_avg * 1.2:,.0f}), pre-pay S${prepayment:,.0f} extra.",
        "In bad weeks, contact GXS support for a 1-month EMI deferral option.",
    ]

    debt_management = {
        "emi_is_sustainable": sustainable,
        "recommended_prepayment_inr": prepayment,
        "bad_week_strategy": (
            "If income drops >30%: skip discretionary spending, "
            "use emergency buffer, request EMI holiday from GXS Bank."
        ),
        "debt_free_in_months": months_to_payoff,
        "actionable_steps": steps,
    }

    return {
        "mode": "deterministic_fallback",
        "trend_analysis": trend_analysis,
        "income_forecast": income_forecast,
        "debt_management": debt_management,
        "reasoning_log": (
            f"Step 1: Loaded {len(daily_vals)} days of income data\n"
            f"Step 2: Computed weekly avg = S${weekly_avg:,.0f}, trend = {trend}\n"
            f"Step 3: Volatility CV = {cv:.2f} → risk = {risk}\n"
            f"Step 4: Applied exponential smoothing (α=0.4) for 4-week forecast\n"
            f"Step 5: Monthly forecast = S${monthly_forecast:,.0f}\n"
            f"Step 6: EMI-to-forecast ratio = {emi_ratio:.1f}% → sustainable = {sustainable}\n"
            f"Step 7: Pre-payment recommendation = S${prepayment:,.0f}/month"
        ),
    }


# ---------------------------------------------------------------------------
# Public entry point — income prediction
# ---------------------------------------------------------------------------

def run_income_prediction(profile: dict) -> dict:
    """Run the Income Prediction crew (live or fallback)."""
    llm = get_llm()
    if llm and CREWAI_AVAILABLE:
        try:
            return _run_crew(profile, llm)
        except Exception as e:
            return {**_run_fallback(profile), "crew_error": str(e)}
    return _run_fallback(profile)


# ---------------------------------------------------------------------------
# Peak Hours Earnings Optimiser — time-slot definitions
# ---------------------------------------------------------------------------

_TIME_BUCKETS = [
    {"name": "Early Morning", "label": "5am–9am",  "hours": ["05","06","07","08"]},
    {"name": "Morning Rush",  "label": "9am–12pm", "hours": ["09","10","11"]},
    {"name": "Afternoon",     "label": "12pm–4pm", "hours": ["12","13","14","15"]},
    {"name": "Evening Rush",  "label": "4pm–8pm",  "hours": ["16","17","18","19"]},
    {"name": "Night",         "label": "8pm–12am", "hours": ["20","21","22","23"]},
    {"name": "Late Night",    "label": "12am–5am", "hours": ["00","01","02","03","04"]},
]

_DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _run_peak_crew(profile: dict, weekly_target: float, llm) -> dict:
    from crewai import Agent, Crew, Process, Task

    hourly = profile.get("hourly_income", {})
    dow    = profile.get("dow_avg_income", profile.get("dow_income", {}))

    ctx = f"""
=== PEAK HOURS OPTIMISER CONTEXT ===
Weekly income target   : S${weekly_target:,.2f}
Income (30d)           : S${profile['income_30d']:,.2f}
Income (7d)            : S${profile['income_7d']:,.2f}
Avg weekly income      : S${profile['income_30d'] / 4.3:,.2f}

Hour-of-day income distribution (last 90 days, totals):
{json.dumps(hourly, indent=2)}

Day-of-week avg income:
{json.dumps(dow, indent=2)}
"""

    schedule_optimiser = Agent(
        role="Gig Schedule Optimiser",
        goal=(
            "Analyse the Grab driver's historical hour-of-day and day-of-week income data "
            "to identify the exact time slots that maximise earnings. "
            "Then compute the minimum schedule needed to hit the driver's weekly income target."
        ),
        backstory=(
            "You are a data-driven gig economy coach who has helped thousands of Grab drivers "
            "increase earnings by 30% simply by shifting their work hours. "
            "You know that 5pm–8pm Tuesday is worth more than 10am–2pm Monday, "
            "and you back every recommendation with the driver's real income data."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    t_schedule = Task(
        description=(
            f"{ctx}\n"
            "Analyse the income data and output a peak hours schedule. Output JSON:\n"
            "weekly_target_inr, current_weekly_avg_inr, gap_inr,\n"
            "top_slots (list of up to 6 objects, each: {slot_name, days, time_range, "
            "avg_income_inr, rank, reason}),\n"
            "recommended_schedule (list of specific day+time blocks to hit the target: "
            "{day, time_range, expected_income_inr}),\n"
            "total_hours_needed (minimum hours per week to hit target),\n"
            "days_off_recommendation (which days to rest),\n"
            "peak_earning_insight (1-2 sentence key insight from the data),\n"
            "achievability (easy/moderate/stretch — can the target be hit?)."
        ),
        expected_output="JSON with peak hours schedule",
        agent=schedule_optimiser,
    )

    crew = Crew(
        agents=[schedule_optimiser],
        tasks=[t_schedule],
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

    schedule_out = _safe_json(str(t_schedule.output) if t_schedule.output else "{}")
    return {
        "mode": "live_crew",
        "peak_hours_schedule": schedule_out,
        "reasoning_log": reasoning_log[:4000],
    }


def _run_peak_fallback(profile: dict, weekly_target: float) -> dict:
    """Formula-based peak hours optimiser — uses real hourly and dow data."""
    hourly_income = profile.get("hourly_income", {})
    dow_avg       = profile.get("dow_avg_income", {})
    income_30d    = profile["income_30d"]
    current_weekly_avg = round(income_30d / 4.3, 2)
    gap = max(weekly_target - current_weekly_avg, 0)

    # ── Score each time bucket using actual hourly data ─────────────────────────
    bucket_scores = []
    for bucket in _TIME_BUCKETS:
        total = sum(hourly_income.get(h, 0) for h in bucket["hours"])
        avg_per_slot = total / max(len(bucket["hours"]), 1)
        bucket_scores.append({
            "name":   bucket["name"],
            "label":  bucket["label"],
            "total":  round(total, 2),
            "avg_per_hour": round(avg_per_slot, 2),
        })

    # If no real hourly data exists (all transactions at midnight), use known gig patterns
    total_hourly = sum(b["total"] for b in bucket_scores)
    if total_hourly == 0:
        _GIG_DEFAULTS = {
            "Early Morning": 0.10, "Morning Rush": 0.18, "Afternoon": 0.12,
            "Evening Rush": 0.35, "Night": 0.20, "Late Night": 0.05,
        }
        for b in bucket_scores:
            b["total"] = round(income_30d * _GIG_DEFAULTS.get(b["name"], 0.10), 2)
            b["avg_per_hour"] = round(b["total"] / 4, 2)
        total_hourly = sum(b["total"] for b in bucket_scores)

    # Sort buckets by avg_per_hour descending
    bucket_scores.sort(key=lambda x: x["avg_per_hour"], reverse=True)

    # ── Score each day of week ──────────────────────────────────────────────────
    if not dow_avg:
        # Gig economy defaults: weekends > weekdays, Friday > Thursday
        _DOW_DEFAULTS = {
            "Monday": 0.11, "Tuesday": 0.11, "Wednesday": 0.12,
            "Thursday": 0.13, "Friday": 0.17, "Saturday": 0.20, "Sunday": 0.16,
        }
        dow_avg = {d: round(current_weekly_avg * w, 2) for d, w in _DOW_DEFAULTS.items()}

    dow_ranked = sorted(dow_avg.items(), key=lambda x: x[1], reverse=True)

    # ── Build top_slots (best day × time-bucket combos) ─────────────────────────
    top_slots = []
    for rank, bucket in enumerate(bucket_scores[:3], 1):
        for day, day_avg in dow_ranked[:3]:
            # Estimated income for this day+slot
            slot_share = bucket["avg_per_hour"] / max(total_hourly / 90, 1)  # proportion of daily income
            slot_income = round(day_avg * slot_share * len(
                [b for b in _TIME_BUCKETS if b["name"] == bucket["name"]][0]["hours"]
            ), 2)
            top_slots.append({
                "slot_name":       f"{day} {bucket['label']}",
                "days":            [day],
                "time_range":      bucket["label"],
                "avg_income_inr":  slot_income,
                "rank":            len(top_slots) + 1,
                "reason":          f"{bucket['name']} is your {['top','2nd','3rd'][rank-1]} earning window; {day} is a strong day",
            })
            if len(top_slots) >= 6:
                break
        if len(top_slots) >= 6:
            break

    top_slots.sort(key=lambda x: x["avg_income_inr"], reverse=True)
    for i, s in enumerate(top_slots):
        s["rank"] = i + 1

    # ── Build recommended schedule to hit target ─────────────────────────────────
    recommended = []
    accumulated = 0.0
    for slot in top_slots:
        if accumulated >= weekly_target:
            break
        recommended.append({
            "day":                slot["days"][0],
            "time_range":         slot["time_range"],
            "expected_income_inr": slot["avg_income_inr"],
        })
        accumulated += slot["avg_income_inr"]

    total_hours = sum(
        len([b for b in _TIME_BUCKETS if b["label"] == r["time_range"]][0]["hours"])
        for r in recommended
        if any(b["label"] == r["time_range"] for b in _TIME_BUCKETS)
    )

    days_working = list({r["day"] for r in recommended})
    days_off = [d for d in _DOW_ORDER if d not in days_working]

    if weekly_target <= current_weekly_avg * 1.1:
        achievability = "easy"
    elif weekly_target <= current_weekly_avg * 1.4:
        achievability = "moderate"
    else:
        achievability = "stretch"

    top2 = [s["slot_name"] for s in top_slots[:2]]
    insight = (
        f"Your highest-earning windows are {' and '.join(top2)}. "
        f"Focusing {total_hours} hours/week on these slots can get you to S${weekly_target:,.0f}/week."
    )

    reasoning = (
        f"Step 1: Current weekly avg = S${current_weekly_avg:,.0f}, target = S${weekly_target:,.0f}, gap = S${gap:,.0f}\n"
        f"Step 2: Scored 6 time buckets using {'real hourly data' if total_hourly > 0 else 'gig industry defaults'}\n"
        f"Step 3: Scored 7 weekdays using {'real dow data' if profile.get('dow_avg_income') else 'gig industry defaults'}\n"
        f"Step 4: Top bucket = {bucket_scores[0]['name']} ({bucket_scores[0]['label']})\n"
        f"Step 5: Built {len(top_slots)} ranked day+slot combos\n"
        f"Step 6: Schedule requires {len(recommended)} slots totalling ~{total_hours}h to hit target\n"
        f"Step 7: Achievability = {achievability}"
    )

    return {
        "mode": "deterministic_fallback",
        "peak_hours_schedule": {
            "weekly_target_inr":     round(weekly_target, 2),
            "current_weekly_avg_inr": current_weekly_avg,
            "gap_inr":               round(gap, 2),
            "top_slots":             top_slots,
            "recommended_schedule":  recommended,
            "total_hours_needed":    total_hours,
            "days_off_recommendation": days_off[:2] if len(days_off) >= 2 else days_off,
            "peak_earning_insight":  insight,
            "achievability":         achievability,
            "data_source": {
                "hourly_data": "real_transaction_timestamps" if profile.get("hourly_income") and sum(profile["hourly_income"].values()) > 0 else "gig_industry_defaults",
                "dow_data": "real_weekday_averages" if profile.get("dow_avg_income") else "gig_industry_defaults",
                "note": (
                    "Schedule is based on your actual earning patterns from the last 90 days."
                    if profile.get("hourly_income") and sum(profile["hourly_income"].values()) > 0
                    else "Your transaction data lacks varied timestamps, so we used gig industry benchmarks "
                         "(e.g., evening rush 4-8pm is typically the highest-earning window for ride-hailing drivers). "
                         "As more transactions come in with natural timestamps, this will switch to your real patterns."
                ),
            },
        },
        "reasoning_log": reasoning,
    }


# ---------------------------------------------------------------------------
# Public entry point — peak hours optimiser
# ---------------------------------------------------------------------------

def run_peak_hours_optimiser(profile: dict, weekly_target: float) -> dict:
    """
    Analyse hour-of-day and day-of-week income patterns and return
    a specific work schedule to hit the driver's weekly income target.

    weekly_target: desired weekly income in SGD
    """
    if weekly_target <= 0:
        weekly_target = profile["income_30d"] / 4.3 * 1.2   # default: 20% above current avg

    llm = get_llm()
    if llm and CREWAI_AVAILABLE:
        try:
            return _run_peak_crew(profile, weekly_target, llm)
        except Exception as e:
            return {**_run_peak_fallback(profile, weekly_target), "crew_error": str(e)}
    return _run_peak_fallback(profile, weekly_target)
