"""
OTP & Account Lock Service
============================
Generates time-limited OTPs when suspicious financial activity is detected.
Automatically locks accounts if the OTP is not verified within the threshold.

Flow:
  1. Fraud crew detects HIGH/CRITICAL risk
     → AgentController calls generate_otp(user_id, reason)
  2. OTP is returned in the API response (demo: shown in response)
     In production, sent via SMS / push notification only.
  3. User submits OTP via POST /api/agents/verify-otp
  4. Wrong OTP 3× or expired → account auto-locked
  5. Locked accounts rejected at lock-status check middleware
  6. POST /api/agents/unlock clears the lock (admin / support flow)

Background sweep:
  check_expired_otps() should be called periodically (every ~30 s via
  FastAPI BackgroundTasks or asyncio task) to enforce timeout locking.
"""
from __future__ import annotations

import secrets
import time
from threading import Lock

OTP_EXPIRY_SECONDS = 300   # 5 minutes
MAX_ATTEMPTS       = 3

# In-memory stores (reset on server restart — acceptable for demo)
_otp_store:  dict[str, dict] = {}   # user_id → {otp, expires_at, reason, attempts}
_lock_store: dict[str, dict] = {}   # user_id → {locked, locked_at, reason}
_mutex = Lock()


# ── OTP generation ───────────────────────────────────────────────────────────

def generate_otp(user_id: str, reason: str, phone: str = "") -> dict:
    """
    Generate a fresh 6-digit OTP for the given user and attempt SMS delivery.
    If no SMS provider is configured, OTP is returned in the response (demo mode).
    """
    from com.gxs.bank.agents.sms_service import send_otp_sms

    otp = f"{secrets.randbelow(900_000) + 100_000}"
    expires_at = time.time() + OTP_EXPIRY_SECONDS

    with _mutex:
        _otp_store[user_id] = {
            "otp":        otp,
            "expires_at": expires_at,
            "reason":     reason,
            "attempts":   0,
            "phone":      phone,
        }

    # Attempt real SMS delivery
    sms_result = {"sent": False, "provider": "skipped", "message": "No phone number provided"}
    if phone:
        sms_result = send_otp_sms(phone, otp, OTP_EXPIRY_SECONDS // 60)

    # Show OTP in response only if SMS was not sent (demo / no provider)
    response = {
        "otp_sent":           True,
        "expires_in_seconds": OTP_EXPIRY_SECONDS,
        "reason":             reason,
        "sms":                sms_result,
        "phone_masked":       _mask_phone(phone) if phone else "not provided",
    }

    if sms_result["sent"]:
        # Real SMS sent — do NOT expose OTP in response
        response["message"] = (
            f"OTP sent to your registered mobile {_mask_phone(phone)}. "
            f"Verify within {OTP_EXPIRY_SECONDS // 60} minutes or your account will be locked."
        )
    else:
        # No SMS provider — show OTP for demo
        response["otp"] = otp
        response["message"] = (
            f"Security alert: {reason}. "
            f"OTP shown below (demo mode — configure SMS provider in .env to send via SMS). "
            f"Verify within {OTP_EXPIRY_SECONDS // 60} minutes or your account will be locked."
        )

    return response


def _mask_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) >= 4:
        return f"{'*' * (len(digits) - 4)}{digits[-4:]}"
    return "****"


# ── OTP verification ─────────────────────────────────────────────────────────

def verify_otp(user_id: str, otp_input: str) -> dict:
    """
    Verify the OTP submitted by the user.
    Returns {verified, locked, reason}.
    Side-effects: may auto-lock the account on expiry or too many failures.
    """
    with _mutex:
        # Already locked?
        if _lock_store.get(user_id, {}).get("locked"):
            return {
                "verified": False,
                "locked":   True,
                "reason":   "Account is locked. Please contact GXS Bank support to unlock.",
            }

        record = _otp_store.get(user_id)
        if not record:
            return {"verified": False, "locked": False, "reason": "No pending OTP found for this account."}

        # Expired?
        if time.time() > record["expires_at"]:
            del _otp_store[user_id]
            _lock_account_internal(user_id, "OTP verification timed out — automatic security lock")
            return {"verified": False, "locked": True, "reason": "OTP expired. Account locked for security."}

        # Increment attempt
        record["attempts"] += 1

        # Too many failures?
        if record["attempts"] > MAX_ATTEMPTS:
            del _otp_store[user_id]
            _lock_account_internal(user_id, f"Exceeded {MAX_ATTEMPTS} failed OTP attempts")
            return {"verified": False, "locked": True, "reason": f"{MAX_ATTEMPTS} failed attempts. Account locked for security."}

        # Correct OTP?
        if record["otp"] == otp_input.strip():
            del _otp_store[user_id]
            _lock_store.pop(user_id, None)   # clear any prior soft lock
            return {"verified": True, "locked": False, "reason": "OTP verified. Account secured."}

        remaining_attempts = MAX_ATTEMPTS - record["attempts"]
        remaining_secs = max(0, int(record["expires_at"] - time.time()))
        return {
            "verified": False,
            "locked":   False,
            "reason": (
                f"Invalid OTP. "
                f"{remaining_attempts} attempt(s) remaining. "
                f"Expires in {remaining_secs}s."
            ),
        }


# ── Account lock / unlock ────────────────────────────────────────────────────

def _lock_account_internal(user_id: str, reason: str) -> None:
    """Internal helper — caller must hold _mutex."""
    _lock_store[user_id] = {
        "locked":    True,
        "locked_at": time.time(),
        "reason":    reason,
    }


def lock_account(user_id: str, reason: str) -> dict:
    with _mutex:
        _lock_account_internal(user_id, reason)
    return {"locked": True, "user_id": user_id, "reason": reason}


def unlock_account(user_id: str) -> dict:
    with _mutex:
        _otp_store.pop(user_id, None)
        _lock_store.pop(user_id, None)
    return {"unlocked": True, "user_id": user_id, "message": "Account successfully unlocked."}


# ── Status queries ────────────────────────────────────────────────────────────

def is_account_locked(user_id: str) -> bool:
    return _lock_store.get(user_id, {}).get("locked", False)


def get_lock_status(user_id: str) -> dict:
    otp  = _otp_store.get(user_id)
    lock = _lock_store.get(user_id)
    return {
        "locked":         bool(lock and lock.get("locked")),
        "lock_reason":    lock.get("reason", "") if lock else "",
        "locked_at":      lock.get("locked_at") if lock else None,
        "otp_pending":    bool(otp),
        "otp_expires_in": max(0, int(otp["expires_at"] - time.time())) if otp else 0,
        "otp_reason":     otp.get("reason", "") if otp else "",
    }


# ── Background sweep ─────────────────────────────────────────────────────────

def check_expired_otps() -> list[str]:
    """
    Sweep all pending OTPs; lock accounts whose OTPs have expired.
    Call this from a periodic background task (every 30 s).
    Returns list of user_ids that were locked.
    """
    now = time.time()
    expired_ids: list[str] = []

    with _mutex:
        for uid in list(_otp_store.keys()):
            if now > _otp_store[uid]["expires_at"]:
                del _otp_store[uid]
                expired_ids.append(uid)

    for uid in expired_ids:
        with _mutex:
            _lock_account_internal(uid, "OTP expired — automatic security lock")

    return expired_ids
