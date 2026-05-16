"""
AI Agent Controller
===================
Exposes all multi-agent features via REST endpoints.

Endpoints:
  GET  /api/agents/financial-wellness   – full financial analysis
  GET  /api/agents/nudges               – personalised push nudges
  GET  /api/agents/credit-score         – alternative GigScore + loan eligibility
  GET  /api/agents/income-prediction    – 4-week income forecast + debt plan
  GET  /api/agents/health-score         – composite financial health score (0–100)
  POST /api/agents/fraud-check          – fraud analysis (triggers OTP on HIGH/CRITICAL)
  POST /api/agents/chat                 – conversational AI (LangGraph routed)
  GET  /api/agents/auto-executor        – autonomous financial action agent
  POST /api/agents/verify-otp           – submit OTP to unblock account
  GET  /api/agents/lock-status          – check account lock / OTP state
  POST /api/agents/unlock               – admin unlock
  GET  /api/agents/guardrails           – active guardrails config
  GET  /api/agents/graph-status         – LangGraph topology info
"""

import os

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from com.gxs.bank.agents import orchestrator
from com.gxs.bank.agents.chat_job_store import job_status, submit_job, wait_for_job
from com.gxs.bank.agents.auto_executor_agent import run_auto_executor
from com.gxs.bank.agents.data_fetcher import get_user_financial_profile
from com.gxs.bank.agents.guardrails_chat import (
    GuardrailsError,
    classify_message,
    guardrails_summary,
    validate_input,
    validate_output,
)
from com.gxs.bank.agents.audit_logger import get_logs as get_audit_logs
from com.gxs.bank.agents.agent_memory import memory_status
from com.gxs.bank.agents.orchestrator_graph import graph_status, run_graph
from com.gxs.bank.agents.otp_lock_service import (
    generate_otp,
    get_lock_status,
    is_account_locked,
    unlock_account,
    verify_otp,
)
from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.database import SessionLocal
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user, require_employee

router = APIRouter(prefix="/api/agents", tags=["AI Agents"])


# ── Request schemas ──────────────────────────────────────────────────────────

class FraudCheckRequest(BaseModel):
    suspect_amount: float = 0.0


class ChatRequest(BaseModel):
    message: str


class OtpVerifyRequest(BaseModel):
    otp: str


class SendOtpRequest(BaseModel):
    phone: str


class AdvisorChatRequest(BaseModel):
    message: str
    history: list = []    # recent chat messages [{role, text}]


class ExecuteActionRequest(BaseModel):
    action_id: str      # e.g. "AUTO_FD"
    amount: float       # amount to act on
    tenure_months: int = 12   # for FD actions





class AssetLoanRequest(BaseModel):
    asset_type: str          # bike | phone | laptop | equipment
    asset_price: float       # purchase price in INR


class DynamicRateReviewRequest(BaseModel):
    loan_id: str             # existing VEHICLE loan ID (looked up from DB)
    base_rate: float = 0.0   # original approved rate (overridden by DB value if loan_id found)
    current_rate: float = 0.0 # current effective rate (overridden by DB value if loan_id found)
    asset_type: str = "bike" # bike | phone | laptop | equipment
    apply_adjustment: bool = False  # if True, writes new rate to DB immediately


CHAT_SYNC_WAIT_SECONDS = float(os.getenv("CHAT_SYNC_WAIT_SECONDS", "30"))


# ── Existing agent endpoints ──────────────────────────────────────────────────

@router.get("/financial-wellness")
def financial_wellness(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = orchestrator.get_financial_wellness(current_user.id, db)
    return ok(result, "Financial wellness analysis complete")


@router.get("/nudges")
def get_nudges(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = orchestrator.get_nudges(current_user.id, db)
    return ok(result, "Nudges generated")


@router.get("/credit-score")
def credit_score(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = orchestrator.get_credit_score(current_user.id, db)
    return ok(result, "Credit score computed")


@router.get("/income-prediction")
def income_prediction(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = orchestrator.get_income_prediction(current_user.id, db)
    return ok(result, "Income prediction complete")


@router.get("/health-score")
def health_score(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = orchestrator.get_financial_health_score(current_user.id, db)
    return ok(result, "Financial health score computed")


@router.post("/fraud-check")
def fraud_check(
    request: FraudCheckRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Runs Fraud Detection crew.
    If risk level is HIGH or CRITICAL, automatically generates an OTP
    and includes it in the response so the user can verify their identity.
    """
    import time
    from com.gxs.bank.agents.audit_logger import log_agent_call
    t0 = time.time()
    result = orchestrator.get_fraud_analysis(current_user.id, db, request.suspect_amount)

    # ── Flag HIGH / CRITICAL risk — user will enter their phone to receive OTP ──
    risk_level = result.get("risk_assessment", {}).get("risk_level", "LOW")
    if risk_level in ("HIGH", "CRITICAL"):
        primary_risk = result.get("risk_assessment", {}).get("primary_risk_factor", "Unusual activity detected")
        result["security_alert"] = {
            "triggered":        True,
            "risk_level":       risk_level,
            "primary_risk":     primary_risk,
            "message":          f"{risk_level} risk detected. Enter your mobile number to receive a verification OTP.",
            "action_required":  "enter_phone_for_otp",
        }
    else:
        result["security_alert"] = {"triggered": False, "risk_level": risk_level}

    # ── Audit log — persist fraud result to SQLite + JSONL ───────────────────
    log_agent_call(
        user_id=current_user.id,
        agent_name="fraud_agent",
        intent="fraud_check",
        input_message=f"suspect_amount={request.suspect_amount}",
        output=result,
        duration_ms=(time.time() - t0) * 1000,
        routing_chain=["direct call → fraud_agent"],
        agents_called=["fraud_agent"],
        graph_mode="direct",
        db=db,
    )

    return ok(result, "Fraud analysis complete")


# ── Chat — LangGraph routed ───────────────────────────────────────────────────

@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Conversational AI agent routed via LangGraph.
    Input and output are protected by guardrails.
    Intent is classified and routed to the matching agent node.
    """
    policy = classify_message(request.message)

    # ── Input guardrails ─────────────────────────────────────────────────────
    try:
        clean_message = validate_input(request.message)
    except GuardrailsError as e:
        return ok(
            {
                "mode":         "guardrails_blocked",
                "answer":       e.user_message,
                "action_tip":   "",
                "blocked":      True,
                "block_reason": e.code,
                "policy_route": policy.get("category", "off_topic"),
                "guardrails":   guardrails_summary(),
            },
            "Message blocked by guardrails",
        )

    def _work() -> dict:
        worker_db = SessionLocal()
        try:
            result = run_graph(current_user.id, clean_message, worker_db)
            result = validate_output(result)
            result["guardrails"] = guardrails_summary()
            result["policy_route"] = policy.get("category", "financial")
            result["policy_allowed"] = policy.get("allowed", True)
            return result
        finally:
            worker_db.close()

    job_id = submit_job(
        kind="chat",
        work_fn=_work,
        meta={"user_id": str(current_user.id), "mode": "langgraph"},
    )

    immediate = wait_for_job(job_id, timeout=CHAT_SYNC_WAIT_SECONDS)
    if immediate is not None:
        return ok({"job_id": job_id, "status": "completed", "result": immediate}, "Chat response generated")

    return ok(
        {
            "job_id": job_id,
            "status": "queued",
            "poll_url": f"/api/agents/chat/{job_id}",
            "message": "Your chat is being processed. Poll the job URL for the answer.",
        },
        "Chat request queued",
    )


@router.get("/chat/{job_id}")
def chat_job_status(job_id: str, current_user=Depends(get_current_user)):
    """Poll the status of an async `/chat` request."""
    status = job_status(job_id)
    if not status:
        return ok({"job_id": job_id, "status": "not_found"}, "Chat job not found")

    if status.get("meta", {}).get("user_id") != str(current_user.id):
        return ok({"job_id": job_id, "status": "forbidden"}, "Chat job not accessible")

    return ok(status, "Chat job status retrieved")


# ── Autonomous Action Agent ───────────────────────────────────────────────────

@router.get("/auto-executor")
def auto_executor(current_user=Depends(get_current_user), db=Depends(get_db)):
    """
    Autonomous Financial Action Agent.
    Analyses the user's financial profile and executes / schedules actions:
    auto-savings, FD moves, spending-limit adjustments, debt alerts,
    EMI pre-payments, and milestone rewards — all without manual input.
    """
    import time
    from com.gxs.bank.agents.audit_logger import log_agent_call
    t0 = time.time()
    profile = get_user_financial_profile(current_user.id, db)
    result  = run_auto_executor(profile, db)
    
    log_agent_call(
        user_id=current_user.id,
        agent_name="auto_executor",
        intent="auto_savings_and_fd",
        input_message="periodic autonomous review",
        output=result,
        duration_ms=(time.time() - t0) * 1000,
        routing_chain=["autonomous trigger → auto_executor_agent"],
        agents_called=["auto_executor"],
        graph_mode="autonomous",
        db=db,
    )
    return ok(result, "Autonomous actions executed")


# ── OTP & Account Lock ────────────────────────────────────────────────────────

@router.post("/send-otp")
def send_otp_endpoint(
    request: SendOtpRequest,
    current_user=Depends(get_current_user),
):
    """
    User provides their mobile number → OTP is generated and sent to that number.
    Called after a HIGH/CRITICAL fraud alert is raised.
    """
    phone = request.phone.strip().replace(" ", "").replace("-", "")
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 10:
        return ok({"sent": False, "message": "Please enter a valid 10-digit mobile number."}, "Invalid phone")

    reason = f"Security verification for your GXS Bank account"
    result = generate_otp(current_user.id, reason, digits)
    return ok(result, "OTP sent")


@router.post("/verify-otp")
def verify_otp_endpoint(
    request: OtpVerifyRequest,
    current_user=Depends(get_current_user),
):
    """Submit OTP to verify identity and unblock a flagged account."""
    result = verify_otp(current_user.id, request.otp)
    result["phone_masked"] = _mask_phone(getattr(current_user, "phone", "") or "")
    msg = "OTP verified successfully" if result["verified"] else "OTP verification failed"
    return ok(result, msg)


def _mask_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) >= 4:
        return f"{'*' * (len(digits) - 4)}{digits[-4:]}"
    return "****"


@router.get("/lock-status")
def lock_status_endpoint(current_user=Depends(get_current_user)):
    """Check current account lock state and any pending OTP."""
    status = get_lock_status(current_user.id)
    return ok(status, "Lock status retrieved")


@router.post("/unlock")
def unlock_endpoint(current_user=Depends(require_employee)):
    """
    Unlock a locked account (employee / support flow only).
    Requires EMPLOYEE role — prevents users from self-unlocking after a fraud lock.
    Pass the target user_id as a query param:
      POST /api/agents/unlock?target_user_id=<uuid>
    If omitted, the employee's own account is unlocked (for testing).
    """
    from fastapi import Query
    result = unlock_account(current_user.id)
    return ok(result, "Account unlocked")


# ── Meta endpoints ────────────────────────────────────────────────────────────

@router.get("/guardrails")
def get_guardrails():
    """Returns active guardrails configuration."""
    return ok(guardrails_summary(), "Guardrails active")


@router.get("/graph-status")
def get_graph_status():
    """Returns Supervisor + LangGraph topology and availability status."""
    return ok(graph_status(), "Graph status retrieved")


@router.get("/llm-health")
def llm_health_check():
    """Lightweight health probe for the active LLM provider."""
    import time
    from com.gxs.bank.agents.llm_config import direct_llm_call, get_active_provider, is_crewai_mode, is_live_mode

    t0 = time.time()
    probe = direct_llm_call(
        "Reply with only OK.",
        "You are a health check assistant. Reply with only OK.",
    )
    latency_ms = round((time.time() - t0) * 1000, 1)
    healthy = bool(probe and probe.strip())
    return ok(
        {
            "healthy": healthy,
            "provider": get_active_provider(),
            "live_mode": is_live_mode(),
            "crewai_mode": is_crewai_mode(),
            "latency_ms": latency_ms,
            "probe_response": probe[:40] if probe else "",
        },
        "LLM health checked",
    )


@router.post("/advisor-chat")
def advisor_chat(
    req: AdvisorChatRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Ask Your AI Financial Advisor — powered by AWS Bedrock (DeepSeek V3.2).
    Uses the user's real financial data as context for personalised advice.
    Falls back to rich deterministic response if no LLM is configured.
    Input is protected by guardrails to prevent prompt injection and off-topic queries.
    """
    policy = classify_message(req.message)

    # ── Input guardrails (same as /chat) ────────────────────────────────────
    try:
        clean_message = validate_input(req.message)
    except GuardrailsError as e:
        return ok(
            {
                "mode":         "guardrails_blocked",
                "answer":       e.user_message,
                "action_tip":   "",
                "blocked":      True,
                "block_reason": e.code,
                "policy_route": policy.get("category", "off_topic"),
                "guardrails":   guardrails_summary(),
            },
            "Message blocked by guardrails",
        )

    def _work() -> dict:
        import time
        from com.gxs.bank.agents.audit_logger import log_agent_call
        from com.gxs.bank.agents.credit_agent import run_credit_scoring
        from com.gxs.bank.agents.gemini_advisor import advisor_chat

        worker_db = SessionLocal()
        try:
            t0 = time.time()
            profile = get_user_financial_profile(current_user.id, worker_db)

            # Inject GigScore so the advisor knows if the user qualifies for loans
            credit_res = run_credit_scoring(profile)
            profile["gig_score"] = credit_res.get("credit_score", {}).get("gig_score", 0)

            result = advisor_chat(profile, clean_message, req.history)
            result = validate_output(result)
            result["guardrails"] = guardrails_summary()
            result["policy_route"] = policy.get("category", "financial")
            result["policy_allowed"] = policy.get("allowed", True)

            log_agent_call(
                user_id=current_user.id,
                agent_name="advisor_chat",
                intent="advisor_chat",
                input_message=clean_message[:500],
                output=result,
                duration_ms=(time.time() - t0) * 1000,
                routing_chain=result.get("routing_chain", ["guardrails → advisor_chat → " + result.get("mode", "unknown")]),
                agents_called=result.get("agents_called", ["advisor"]),
                graph_mode=result.get("mode", "unknown"),
                db=worker_db,
            )
            return result
        finally:
            worker_db.close()

    job_id = submit_job(
        kind="advisor_chat",
        work_fn=_work,
        meta={"user_id": str(current_user.id), "mode": "advisor"},
    )

    immediate = wait_for_job(job_id, timeout=CHAT_SYNC_WAIT_SECONDS)
    if immediate is not None:
        return ok({"job_id": job_id, "status": "completed", "result": immediate}, "Advisor response")

    return ok(
        {
            "job_id": job_id,
            "status": "queued",
            "poll_url": f"/api/agents/advisor-chat/{job_id}",
            "message": "Your financial advisor is thinking. Poll the job URL for the answer.",
        },
        "Advisor request queued",
    )


@router.get("/advisor-chat/{job_id}")
def advisor_chat_job_status(job_id: str, current_user=Depends(get_current_user)):
    """Poll the status of an async `/advisor-chat` request."""
    status = job_status(job_id)
    if not status:
        return ok({"job_id": job_id, "status": "not_found"}, "Advisor job not found")

    if status.get("meta", {}).get("user_id") != str(current_user.id):
        return ok({"job_id": job_id, "status": "forbidden"}, "Advisor job not accessible")

    return ok(status, "Advisor job status retrieved")


# ── Micro-Repayment Config ────────────────────────────────────────────────────

@router.get("/repayment-config")
def get_repayment_config_endpoint(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Returns the user's current micro-repayment configuration:
    deduction rate, band, GigScore, active loan info, and today's summary.
    """
    import time
    from com.gxs.bank.agents.audit_logger import log_agent_call
    from com.gxs.bank.agents.credit_agent import run_credit_scoring
    from com.gxs.bank.agents.repayment_agent import get_repayment_config

    t0 = time.time()
    profile = get_user_financial_profile(current_user.id, db)
    credit_res = run_credit_scoring(profile)
    profile["gig_score"] = credit_res.get("credit_score", {}).get("gig_score", 0)

    config = get_repayment_config(profile)

    log_agent_call(
        user_id=current_user.id,
        agent_name="repayment_agent",
        intent="repayment_config_view",
        input_message="User viewed micro-repayment config",
        output=config,
        duration_ms=(time.time() - t0) * 1000,
        routing_chain=["user request → repayment_agent → config"],
        agents_called=["credit_agent", "repayment_agent"],
        graph_mode="config_view",
        db=db,
    )
    return ok(config, "Micro-repayment configuration")


@router.get("/audit-log")
def get_agent_audit_log(
    limit: int = 50,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Returns the agent reasoning audit trail for the current user.
    Each entry records: agent called, intent, routing chain, duration, output summary.
    """
    logs = get_audit_logs(user_id=current_user.id, limit=limit, db=db)
    return ok(logs, f"Audit log retrieved ({len(logs)} entries)")


@router.get("/memory-status")
def get_memory_status():
    """Returns ChromaDB agent memory status."""
    return ok(memory_status(), "Memory status retrieved")


@router.post("/execute-action")
def execute_agent_action(
    req: ExecuteActionRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Execute an autonomous agent action that the user has approved.
    Currently supports: AUTO_FD (transfer idle funds to Fixed Deposit).
    """
    if req.action_id == "AUTO_FD":
        from decimal import Decimal
        from com.gxs.bank.model.FixedDeposit import FixedDeposit
        from com.gxs.bank.service.FixedDepositService import FixedDepositService
        from com.gxs.bank.repository.AccountRepository import AccountRepository

        # Get user's primary savings account
        acct_repo = AccountRepository(db)
        accounts = acct_repo.findByUserId(current_user.id)
        if not accounts:
            from com.gxs.bank.exception.BadRequestException import BadRequestException
            raise BadRequestException("No savings account found")

        account = accounts[0]
        amount = Decimal(str(round(req.amount, 2)))

        if account.balance < amount:
            from com.gxs.bank.exception.BadRequestException import BadRequestException
            raise BadRequestException(
                f"Insufficient balance. Available: ₹{float(account.balance):,.2f}, Requested: ₹{float(amount):,.2f}"
            )

        fd_request = FixedDeposit(
            sourceAccountId=account.id,
            principalAmount=amount,
            interestRate=Decimal("6.50"),
            tenureMonths=req.tenure_months,
        )

        svc = FixedDepositService(db)
        fd = svc.createFD(current_user.id, fd_request)

        return ok({
            "action_id":       req.action_id,
            "status":          "executed",
            "fd_number":       fd.fdNumber,
            "amount":          float(fd.principalAmount),
            "interest_rate":   float(fd.interestRate),
            "tenure_months":   fd.tenureMonths,
            "maturity_date":   str(fd.maturityDate),
            "maturity_amount": float(fd.maturityAmount),
            "new_balance":     float(account.balance),
            "message":         f"Rs.{float(fd.principalAmount):,.0f} transferred to Fixed Deposit (FD#{fd.fdNumber}) at 6.5% p.a. Matures on {fd.maturityDate}.",
        }, "FD created successfully")

    # ── Unsupported action — return informative response (not a 500) ─────────
    supported_actions = ["AUTO_FD"]
    return ok(
        {
            "action_id":        req.action_id,
            "status":           "not_executable",
            "supported_actions": supported_actions,
            "message":          (
                f"Action '{req.action_id}' is evaluated by the agent but cannot be executed server-side yet. "
                f"Supported executable actions: {', '.join(supported_actions)}."
            ),
        },
        "Action not yet executable",
    )


# ── Vehicle / Equipment Asset Loan Eligibility ────────────────────────────────

@router.post("/asset-loan-eligibility")
def asset_loan_eligibility(
    req: AssetLoanRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Assess eligibility for a vehicle or equipment loan.

    Asset types:
      - bike       : 80% LTV, 36 months, 2% rate discount vs personal
      - phone      : 70% LTV, 18 months, 1% rate discount
      - laptop     : 70% LTV, 18 months, 1% rate discount
      - equipment  : 75% LTV, 24 months, 1.5% rate discount

    Considers the asset's income-generating capacity (e.g. a bike → more rides → higher
    future income) and factors this into the eligibility decision and payback period.
    Uses the existing GigScore as credit base.
    """
    if req.asset_price <= 0:
        return ok({"error": "asset_price must be greater than 0"}, "Invalid request")

    allowed_types = {"bike", "phone", "laptop", "equipment"}
    asset_type = req.asset_type.lower().strip()
    if asset_type not in allowed_types:
        return ok(
            {"error": f"Unknown asset_type '{req.asset_type}'. Use: {', '.join(sorted(allowed_types))}"},
            "Invalid asset type",
        )

    result = orchestrator.get_asset_loan_eligibility(current_user.id, db, asset_type, req.asset_price)
    return ok(result, "Asset loan eligibility assessed")


# ── Dynamic Loan Rate Review ──────────────────────────────────────────────────

@router.post("/asset-loan-rate-review")
def asset_loan_rate_review(
    req: DynamicRateReviewRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Weekly dynamic rate review for an active asset-backed gig loan.

    The agent scores the borrower's current financial behaviour across 5 dimensions:
      1. Income performance  — this week vs 30-day average
      2. Savings discipline  — current savings rate vs 20% target
      3. Spending control    — estimated weekly spend vs baseline
      4. Balance buffer      — months of expenses covered
      5. EMI burden          — debt-to-income health

    Score 85-100 → rate drops 1.50%  (Excellent)
    Score 70-84  → rate drops 0.75%  (Good)
    Score 55-69  → rate holds        (Neutral)
    Score 40-54  → rate rises 0.50%  (Caution — warning signal)
    Score  0-39  → rate rises 1.50%  (At-Risk — strong warning)

    Hard caps: floor 7.0%, ceiling base_rate+3.0%, max benefit ±2.0% from original.

    If apply_adjustment=true and loan_id is provided, the new rate is written to
    the loan record and EMI is recomputed on the remaining outstanding principal.
    """
    from com.gxs.bank.service.LoanService import LoanService

    loan_svc = LoanService(db)

    # ── Resolve loan details from DB if loan_id provided ──────────────────────
    base_rate      = req.base_rate
    current_rate   = req.current_rate
    outstanding    = 0.0
    remaining_months = 12
    asset_type     = req.asset_type

    if req.loan_id:
        try:
            loan = loan_svc.getLoan(req.loan_id, current_user.id)
            base_rate    = float(loan.interestRate)    # treat current as base (conservative)
            current_rate = float(loan.interestRate)
            outstanding  = float(loan.outstandingAmount or loan.amount)
            emis_paid    = int(loan.emisPaid or 0)
            total_emis   = int(loan.totalEmis or loan.tenureMonths)
            remaining_months = max(total_emis - emis_paid, 1)
            # Map loan type to asset_type
            if loan.loanType and "VEHICLE" in str(loan.loanType):
                asset_type = "bike"
        except Exception:
            pass   # fall through to request values

    # At minimum need a valid rate
    if base_rate <= 0:
        return ok({"error": "Provide a valid base_rate or a loan_id that resolves to an active loan"}, "Invalid request")
    if current_rate <= 0:
        current_rate = base_rate

    # ── Run the dynamic rate agent ────────────────────────────────────────────
    result = orchestrator.get_dynamic_loan_rate_review(
        current_user.id, db,
        base_rate=base_rate,
        current_rate=current_rate,
        asset_type=asset_type,
        outstanding=outstanding,
        remaining_months=remaining_months,
    )

    # ── Optionally persist the new rate to DB ─────────────────────────────────
    if req.apply_adjustment and req.loan_id:
        new_rate = result.get("review", {}).get("new_rate_pct", current_rate)
        try:
            apply_result = loan_svc.apply_rate_adjustment(req.loan_id, current_user.id, new_rate)
            result["rate_applied_to_db"] = apply_result
        except Exception as exc:
            result["rate_apply_error"] = str(exc)
    else:
        result["rate_applied_to_db"] = None
        if not req.apply_adjustment:
            result["apply_hint"] = "Set apply_adjustment=true to write the new rate to the loan record"

    return ok(result, "Dynamic rate review complete")


# ── Peak Hours Earnings Optimiser ─────────────────────────────────────────────

@router.get("/peak-hours")
def peak_hours_optimiser(
    weekly_target: float = 0.0,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Analyse hour-of-day and day-of-week income patterns from 90 days of history
    and return a specific work schedule to hit the driver's weekly income target.

    Query param:
      weekly_target (float, INR) — desired weekly income.
                                   If 0 or omitted, defaults to 20% above current weekly average.

    Returns:
      - top_slots       : ranked list of best day × time-window combos
      - recommended_schedule : minimum slots to work to hit the target
      - total_hours_needed   : how many hours per week
      - days_off_recommendation
      - peak_earning_insight : key insight from the data
      - achievability        : easy / moderate / stretch
    """
    result = orchestrator.get_peak_hours_schedule(current_user.id, db, weekly_target)
    return ok(result, "Peak hours schedule generated")


# ── Real-time Fraud Streaming (SSE) ──────────────────────────────────────────

@router.get("/fraud-stream")
def fraud_stream_sse(token: str = ""):
    """
    Server-Sent Events endpoint for real-time fraud alerts.
    Pass JWT token as query param: /api/agents/fraud-stream?token=<jwt>
    (EventSource cannot send custom headers, so Bearer auth is not possible.)
    """
    from com.gxs.bank.agents.fraud_stream import fraud_event_stream
    from com.gxs.bank.security.JwtTokenProvider import JwtTokenProvider
    from fastapi import HTTPException

    if not token:
        raise HTTPException(status_code=401, detail="Token required as query param")

    provider = JwtTokenProvider()
    if not provider.validateToken(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    # JWT is valid — extract user_id directly (no DB lookup needed for SSE auth)
    user_id = provider.getUserIdFromToken(token)

    return StreamingResponse(
        fraud_event_stream(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/fraud-stream/status")
def fraud_stream_status():
    """Returns real-time fraud streaming worker health and queue stats."""
    from com.gxs.bank.agents.fraud_stream import stream_status
    return ok(stream_status(), "Fraud stream status")


@router.get("/fraud-stream/result/{txn_id}")
def get_stream_fraud_result(txn_id: str, current_user=Depends(get_current_user)):
    """
    Poll fraud result for a specific transaction (non-SSE alternative).
    Returns immediately — result is None if fraud check is still running.
    """
    from com.gxs.bank.agents.fraud_stream import get_txn_result
    result = get_txn_result(txn_id)
    if result:
        return ok(result, "Fraud result ready")
    return ok({"txn_id": txn_id, "status": "processing"}, "Fraud check in progress")



