"""
Real-time Fraud Streaming
=========================
Intercepts transactions at creation time and runs fraud detection
asynchronously in a background thread.

Flow:
  1. AccountService calls emit_transaction_event() right after saving a txn
  2. A daemon worker thread picks it up from the queue
  3. Fraud crew runs on the rolling 30-day window
  4. Result stored in _results[txn_id]; pushed to per-user event list
  5. Frontend polls  GET /api/agents/fraud-stream  (SSE) for events
  6. CRITICAL risk  → transaction auto-held (PENDING status) + OTP triggered
  7. HIGH risk      → alert pushed, transaction proceeds
  8. Transactions above dynamic threshold require OTP regardless of risk
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
from typing import Generator

log = logging.getLogger("fraud_stream")

# ── In-memory stores ──────────────────────────────────────────────────────────
_task_queue: queue.Queue = queue.Queue()
_results: dict[str, dict] = {}          # txn_id  → fraud result
_user_events: dict[str, list] = {}      # user_id → list of unread events
_store_lock = threading.Lock()
_worker_thread: threading.Thread | None = None
_worker_stop = threading.Event()

_MAX_RESULTS = 1000
_MAX_EVENTS_PER_USER = 100


# ── Dynamic OTP threshold ─────────────────────────────────────────────────────

def get_dynamic_threshold(profile: dict) -> float:
    """
    Compute the OTP-confirmation threshold for this user.
    Rule: 30% of 30-day income, floored at S$5,000 and capped at S$50,000.
    """
    income_30d = profile.get("income_30d", 0.0)
    threshold = income_30d * 0.30
    return round(max(5_000.0, min(50_000.0, threshold)), 2)


# ── Public entry point (called by AccountService) ────────────────────────────

def emit_transaction_event(
    txn_id: str,
    user_id: str,
    amount: float,
    txn_type: str,
    description: str,
) -> None:
    """
    Enqueue a fraud-check task.  Non-blocking — returns immediately.
    The background worker processes it asynchronously.
    """
    _task_queue.put_nowait({
        "txn_id":      txn_id,
        "user_id":     user_id,
        "amount":      amount,
        "txn_type":    txn_type,
        "description": description,
        "queued_at":   time.time(),
    })
    start_worker()
    log.debug("Fraud task enqueued for txn %s (S$%.2f)", txn_id, amount)


# ── Background worker ─────────────────────────────────────────────────────────

def _worker() -> None:
    """Daemon thread: dequeues tasks and runs fraud checks."""
    while not _worker_stop.is_set():
        try:
            task = _task_queue.get(timeout=1.0)
        except queue.Empty:
            continue
        try:
            _process(task)
        except Exception as exc:
            log.error("Fraud stream worker error for txn %s: %s", task.get("txn_id"), exc)
        finally:
            _task_queue.task_done()


def _process(task: dict) -> None:
    from com.gxs.bank.config.database import SessionLocal
    from com.gxs.bank.agents.data_fetcher import get_user_financial_profile
    from com.gxs.bank.agents.fraud_agent import run_fraud_check

    txn_id  = task["txn_id"]
    user_id = task["user_id"]
    amount  = task["amount"]

    db = SessionLocal()
    try:
        profile    = get_user_financial_profile(user_id, db)
        threshold  = get_dynamic_threshold(profile)
        result     = run_fraud_check(profile, amount)

        risk_level = result.get("risk_assessment", {}).get("risk_level", "LOW")
        risk_score = result.get("risk_assessment", {}).get("risk_score", 0)
        above_threshold = amount >= threshold
        should_hold = risk_level == "CRITICAL"
        needs_otp   = risk_level in ("HIGH", "CRITICAL") or above_threshold

        # Auto-hold CRITICAL transactions
        if should_hold:
            _hold_transaction(txn_id, db)

        event = {
            "txn_id":          txn_id,
            "user_id":         user_id,
            "amount":          amount,
            "txn_type":        task["txn_type"],
            "description":     task["description"],
            "risk_level":      risk_level,
            "risk_score":      risk_score,
            "held":            should_hold,
            "needs_otp":       needs_otp,
            "above_threshold": above_threshold,
            "threshold":       threshold,
            "anomalies":       result.get("anomaly_detection", {}).get("anomalies", []),
            "mitigation":      result.get("mitigation", {}),
            "timestamp":       time.time(),
            "agent_mode":      result.get("agent_mode", "deterministic"),
        }

        # Store result + push to user's event list
        with _store_lock:
            _results[txn_id] = event
            while len(_results) > _MAX_RESULTS:
                oldest_txn_id = next(iter(_results))
                _results.pop(oldest_txn_id, None)

            events = _user_events.setdefault(user_id, [])
            events.append(event)
            if len(events) > _MAX_EVENTS_PER_USER:
                _user_events[user_id] = events[-_MAX_EVENTS_PER_USER:]

        # ── Audit log — persist fraud result to SQLite + JSONL ───────────────────
        from com.gxs.bank.agents.audit_logger import log_agent_call
        log_agent_call(
            user_id=str(user_id),
            agent_name="fraud_agent",
            intent="realtime_fraud_stream",
            input_message=f"txn_id={txn_id}, amount=S${amount:,.2f}",
            output=event,
            duration_ms=(time.time() - task.get("queued_at", time.time())) * 1000,
            routing_chain=["real-time event → background worker → fraud_agent"],
            agents_called=["fraud_agent"],
            graph_mode="stream",
            db=db,
        )

    finally:
        db.close()


def _hold_transaction(txn_id: str, db) -> None:
    """Set transaction status to PENDING (held for review)."""
    try:
        from com.gxs.bank.model.Transaction import Transaction, TxnStatus
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if txn and txn.txnStatus.value == "SUCCESS":
            txn.txnStatus = TxnStatus.PENDING
            txn.remarks   = "AUTO-HELD: CRITICAL fraud risk detected. Awaiting OTP confirmation."
            db.commit()
            log.warning("Transaction %s auto-held (CRITICAL risk)", txn_id)
    except Exception as exc:
        log.error("Failed to hold transaction %s: %s", txn_id, exc)
        db.rollback()


# ── Transaction release (after OTP verified) ──────────────────────────────────

def release_held_transaction(txn_id: str) -> dict:
    """
    Release a held (PENDING) transaction after OTP verification.
    Sets txnStatus → SUCCESS and marks the fraud event as confirmed.
    """
    from com.gxs.bank.config.database import SessionLocal
    from com.gxs.bank.model.Transaction import Transaction, TxnStatus

    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if txn is None:
            return {"released": False, "reason": "Transaction not found"}

        if txn.txnStatus != TxnStatus.PENDING:
            return {
                "released": False,
                "reason": f"Transaction is not held (status: {txn.txnStatus.value})",
            }

        txn.txnStatus = TxnStatus.SUCCESS
        txn.remarks   = "RELEASED: OTP verified by account holder."
        db.commit()

        # Update in-memory result
        with _store_lock:
            if txn_id in _results:
                _results[txn_id]["held"]     = False
                _results[txn_id]["released"] = True

        return {
            "released":      True,
            "txn_id":        txn_id,
            "new_status":    "SUCCESS",
            "message":       "Transaction confirmed and released successfully.",
        }
    except Exception as exc:
        db.rollback()
        return {"released": False, "reason": str(exc)}
    finally:
        db.close()


# ── Result getters ────────────────────────────────────────────────────────────

def get_txn_result(txn_id: str) -> dict | None:
    """Get fraud result for a specific transaction (non-blocking)."""
    with _store_lock:
        return _results.get(txn_id)


def pop_user_events(user_id: str) -> list:
    """Drain and return all pending events for a user."""
    with _store_lock:
        events = list(_user_events.get(user_id, []))
        _user_events[user_id] = []
        return events


# ── SSE generator ─────────────────────────────────────────────────────────────

def fraud_event_stream(user_id: str, poll_interval: float = 1.0) -> Generator[str, None, None]:
    """
    Server-Sent Events generator.
    Yields new fraud events for `user_id` as they arrive.
    Sends a keepalive comment every ~15 seconds.
    Client disconnects when they close the connection.
    """
    last_keepalive = time.time()

    # Send initial connected event
    yield f"data: {json.dumps({'type': 'connected', 'user_id': user_id, 'timestamp': time.time()})}\n\n"

    while True:
        events = pop_user_events(user_id)
        for evt in events:
            payload = {**evt, "type": "fraud_result"}
            yield f"data: {json.dumps(payload)}\n\n"

        # Keepalive ping every 15 seconds
        if time.time() - last_keepalive > 15:
            yield ": keepalive\n\n"
            last_keepalive = time.time()

        time.sleep(poll_interval)


# ── Queue status ──────────────────────────────────────────────────────────────

def stream_status() -> dict:
    with _store_lock:
        return {
            "queue_size":        _task_queue.qsize(),
            "results_cached":    len(_results),
            "active_user_feeds": len(_user_events),
            "worker_alive":      _worker_thread.is_alive() if _worker_thread else False,
        }


def start_worker() -> None:
    """Start the fraud worker thread once during app startup or on demand."""
    global _worker_thread
    with _store_lock:
        if _worker_thread and _worker_thread.is_alive():
            return
        _worker_stop.clear()
        _worker_thread = threading.Thread(target=_worker, daemon=True, name="fraud-stream-worker")
        _worker_thread.start()


def shutdown_worker() -> None:
    """Signal the fraud worker to stop gracefully."""
    _worker_stop.set()
log.info("Fraud stream worker started.")
