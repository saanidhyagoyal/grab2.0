"""
Agent Reasoning Audit Logger
=============================
Logs every agent invocation to two sinks:
  1. SQLite  — table `agent_reasoning_logs` (queryable via API)
  2. JSONL   — file  `backend-python/agent_audit_log.jsonl` (portable export)

Usage:
    from com.gxs.bank.agents.audit_logger import log_agent_call, get_logs
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger("audit_logger")

# JSONL file lives next to this package's root (backend-python/)
_LOG_FILE = Path(__file__).resolve().parents[4] / "agent_audit_log.jsonl"


# ── Write ─────────────────────────────────────────────────────────────────────

def log_agent_call(
    *,
    user_id: str,
    agent_name: str,
    intent: str = "",
    input_message: str = "",
    output: dict | None = None,
    duration_ms: float = 0.0,
    routing_chain: list | None = None,
    agents_called: list | None = None,
    graph_mode: str = "",
    db=None,
) -> None:
    """Persist one agent-call record to SQLite and JSONL."""
    output_summary = _summarize(output or {})
    entry = {
        "timestamp":     datetime.utcnow().isoformat() + "Z",
        "user_id":       user_id,
        "agent_name":    agent_name,
        "intent":        intent,
        "input_message": (input_message or "")[:500],
        "output_summary": output_summary[:1000],
        "routing_chain": routing_chain or [],
        "agents_called": agents_called or [],
        "duration_ms":   round(duration_ms, 1),
        "graph_mode":    graph_mode,
        "policy_route":  (output or {}).get("policy_route", ""),
        "chat_error":    (output or {}).get("chat_error", ""),
    }

    # ── JSONL ─────────────────────────────────────────────────────────────────
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"[AUDIT OK] JSONL written: {agent_name} / {intent[:60]}", flush=True)
    except Exception as exc:
        print(f"[AUDIT FAIL] JSONL write failed for {agent_name}: {exc!r}", flush=True)
        log.warning("Audit JSONL write failed: %s", exc)

    # ── SQLite ────────────────────────────────────────────────────────────────
    if db is not None:
        try:
            from com.gxs.bank.model.AgentReasoningLog import AgentReasoningLog
            rec = AgentReasoningLog(
                userId=user_id,
                agentName=agent_name,
                intent=intent,
                inputMessage=(input_message or "")[:500],
                outputSummary=output_summary[:1000],
                routingChain=json.dumps(routing_chain or []),
                agentsCalled=json.dumps(agents_called or []),
                durationMs=round(duration_ms, 1),
                graphMode=graph_mode,
            )
            db.add(rec)
            db.commit()
        except Exception as exc:
            log.error("Audit DB write failed: %s", exc)
            try:
                db.rollback()
            except Exception:
                pass


def clear_logs(db=None) -> None:
    """Clear all agent reasoning logs from SQLite and JSONL."""
    # 1. Truncate JSONL
    try:
        if _LOG_FILE.exists():
            _LOG_FILE.write_text("", encoding="utf-8")
        print("[AUDIT OK] JSONL cleared", flush=True)
    except Exception as exc:
        print(f"[AUDIT FAIL] JSONL clear failed: {exc!r}", flush=True)

    # 2. Clear SQLite table
    if db is not None:
        try:
            from com.gxs.bank.model.AgentReasoningLog import AgentReasoningLog
            db.query(AgentReasoningLog).delete()
            db.commit()
            print("[AUDIT OK] SQLite logs cleared", flush=True)
        except Exception as exc:
            print(f"[AUDIT FAIL] SQLite clear failed: {exc}", flush=True)
            db.rollback()


# ── Read ──────────────────────────────────────────────────────────────────────

def get_logs(user_id: str | None = None, limit: int = 50, db=None) -> list[dict]:
    """Return recent agent reasoning logs — tries SQLite first, falls back to JSONL."""
    # ── Try SQLite ────────────────────────────────────────────────────────────
    if db is not None:
        try:
            from com.gxs.bank.model.AgentReasoningLog import AgentReasoningLog
            q = db.query(AgentReasoningLog)
            if user_id:
                q = q.filter(AgentReasoningLog.userId == user_id)
            rows = q.order_by(AgentReasoningLog.createdAt.desc()).limit(limit).all()
            if rows:
                return [
                    {
                        "id":             r.id,
                        "user_id":        r.userId,
                        "agent_name":     r.agentName,
                        "intent":         r.intent,
                        "input_message":  r.inputMessage,
                        "output_summary": r.outputSummary,
                        "routing_chain":  json.loads(r.routingChain or "[]"),
                        "agents_called":  json.loads(r.agentsCalled or "[]"),
                        "duration_ms":    r.durationMs,
                        "graph_mode":     r.graphMode,
                        "policy_route":   getattr(r, "policyRoute", ""),
                        "chat_error":     getattr(r, "chatError", ""),
                        "created_at":     r.createdAt.isoformat() + "Z" if r.createdAt else None,
                    }
                    for r in rows
                ]
        except Exception as exc:
            log.error("Audit DB read failed: %s", exc)

    # ── Fallback: read from JSONL ─────────────────────────────────────────────
    return _read_jsonl(user_id, limit)


def _read_jsonl(user_id: str | None, limit: int) -> list[dict]:
    """Read logs from the JSONL file as a fallback when SQLite is unavailable."""
    if not _LOG_FILE.exists():
        return []
    try:
        entries = []
        with open(_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if user_id and entry.get("user_id") != user_id:
                    continue
                entries.append(entry)
        # Return most-recent first
        entries.reverse()
        result = []
        for i, e in enumerate(entries[:limit]):
            result.append({
                "id":             str(i + 1),
                "user_id":        e.get("user_id", ""),
                "agent_name":     e.get("agent_name", ""),
                "intent":         e.get("intent", ""),
                "input_message":  e.get("input_message", ""),
                "output_summary": e.get("output_summary", ""),
                "routing_chain":  e.get("routing_chain", []),
                "agents_called":  e.get("agents_called", []),
                "duration_ms":    e.get("duration_ms", 0),
                "graph_mode":     e.get("graph_mode", ""),
                "policy_route":   e.get("policy_route", ""),
                "chat_error":     e.get("chat_error", ""),
                "created_at":     e.get("timestamp", ""),
                "source":         "jsonl",
            })
        return result
    except Exception as exc:
        log.error("Audit JSONL read failed: %s", exc)
        return []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _summarize(output: dict) -> str:
    if not output:
        return "No output"
    parts = []

    # ── 1. Fraud / Risk ───────────────────────────────────────────────────────
    ra = output.get("risk_assessment", {})
    if ra.get("risk_level"):
        level = ra['risk_level']
        score = ra.get('risk_score', 0)
        parts.append(f"🛡️ Risk: {level} ({score}/100)")
        if ra.get("primary_risk_factor"):
            parts.append(f"Factor: {ra['primary_risk_factor']}")
    
    # ── 2. Financial Health ───────────────────────────────────────────────────
    if output.get("health_score"):
        grade = output.get('grade', '')
        parts.append(f"🏥 Health: {output['health_score']}/100 [{grade}]")
        if output.get("top_recommendation"):
            parts.append(f"Rec: {output['top_recommendation'][:80]}")

    # ── 3. Credit / GigScore ──────────────────────────────────────────────────
    cs = output.get("credit_score", {})
    gig = cs.get("gig_score") or output.get("gig_score")
    if gig:
        grade = cs.get('score_grade', '')
        parts.append(f"📈 GigScore: {gig} ({grade})")
        elig = cs.get("loan_eligibility", {})
        if elig.get("eligible"):
            parts.append(f"Loan: S${elig.get('max_amount',0):,.0f} Max")

    # ── 4. Asset Loan Eligibility ─────────────────────────────────────────────
    al = output.get("asset_loan", {})
    if al:
        atype = al.get('asset_type','asset')
        eligible = al.get("is_eligible")
        status = "✅ Eligible" if eligible else "❌ Ineligible"
        parts.append(f"🚲 {atype.title()} Loan: {status}")
        if eligible:
            parts.append(f"Amt: S${al.get('loan_amount_inr',0):,.0f} @ {al.get('interest_rate_pct',0)}%")
        elif al.get("reason"):
            parts.append(f"Reason: {al['reason'][:60]}")

    # ── 5. Dynamic Rate Review ────────────────────────────────────────────────
    rev = output.get("review", {})
    if rev.get("behaviour_score") is not None:
        score = rev['behaviour_score']
        band = rev.get('band','')
        old_r = rev.get('current_rate_pct',0)
        new_r = rev.get('new_rate_pct',0)
        diff = new_r - old_r
        parts.append(f"📉 Dynamic Rate: {score}/100 ({band})")
        parts.append(f"Rate: {old_r}% → {new_r}% ({'+' if diff > 0 else ''}{diff:.2f}%)")

    # ── 6. Peak Hours / Earnings ──────────────────────────────────────────────
    ph = output.get("peak_hours_schedule", {})
    if ph.get("weekly_target_inr"):
        target = ph['weekly_target_inr']
        hours = ph.get('total_hours_needed', 0)
        achieve = ph.get('achievability', 'unknown')
        parts.append(f"⏰ Peak Optimization: Target S${target:,.0f}/wk")
        parts.append(f"Plan: {hours}h needed [{achieve}]")

    # ── 7. Income Prediction ──────────────────────────────────────────────────
    ip = output.get("income_forecast", {})
    if ip.get("monthly_forecast_inr"):
        forecast = ip['monthly_forecast_inr']
        conf = ip.get('confidence_pct', 0)
        trend = ip.get('trend', 'stable')
        parts.append(f"💰 Forecast: S${forecast:,.0f}/mo ({trend})")
        parts.append(f"Confidence: {conf:.0f}%")

    # ── 8. Micro-Repayment ────────────────────────────────────────────────────
    if output.get("micro_repayment"):
        pct = output.get('deduction_pct', 0)
        amt = output.get('deduction_amount', 0)
        net = output.get('net_deposit', 0)
        band = output.get('band', '')
        gig = output.get('gig_score', 0)
        risk = output.get('risk_level', '')
        outstanding = output.get('loan_outstanding', 0)
        parts.append(f"🏧 Micro-Repayment: {pct}% ({band})")
        parts.append(f"Deducted: S${amt:,.2f} → Loan (outstanding: S${outstanding:,.2f})")
        parts.append(f"Net to wallet: S${net:,.2f} | GigScore: {gig} | Risk: {risk}")

    # ── 9. Chat / Advisor ─────────────────────────────────────────────────────
    if output.get("answer"):
        ans = str(output['answer'])
        parts.append(f"💬 Answer: {ans[:150]}...")
    
    # ── 9. Generic / Fallback ─────────────────────────────────────────────────
    if not parts:
        # If no specific keys matched, try to show at least something
        if output.get("message"):
            parts.append(output["message"])
        elif output.get("status"):
            parts.append(f"Status: {output['status']}")
        else:
            return json.dumps(output)[:250]

    return " | ".join(parts)
