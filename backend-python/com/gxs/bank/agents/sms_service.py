"""
SMS Service
===========
Sends OTP messages via real SMS providers.
Falls back gracefully if no credentials are configured.

Supported providers (configure via .env):
  1. Twilio      — TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN + TWILIO_FROM_NUMBER
  2. Fast2SMS    — FAST2SMS_API_KEY  (India, free credits at fast2sms.com)

If neither is configured, SMS is skipped and the OTP is returned in the
API response instead (demo / development behaviour).
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger("sms_service")


def _load_env():
    """Load .env if present (without requiring python-dotenv to be imported at module level)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def send_otp_sms(phone: str, otp: str, expires_minutes: int = 5) -> dict:
    """
    Send OTP via SMS to the given phone number.

    Returns:
        {
            "sent": bool,
            "provider": "twilio" | "fast2sms" | "skipped",
            "message": str          # human-readable status
        }
    """
    _load_env()
    message_text = (
        f"GXS Bank Security Alert: Your OTP is {otp}. "
        f"Valid for {expires_minutes} minutes. Do NOT share with anyone."
    )

    # ── Try Twilio ────────────────────────────────────────────────────────────
    sid   = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_ = os.getenv("TWILIO_FROM_NUMBER", "").strip()

    if sid and token and from_:
        return _send_twilio(phone, message_text, sid, token, from_)

    # ── Try Fast2SMS ──────────────────────────────────────────────────────────
    fast2sms_key = os.getenv("FAST2SMS_API_KEY", "").strip()
    if fast2sms_key:
        return _send_fast2sms(phone, otp, message_text, fast2sms_key)

    # ── No provider configured — show in response ─────────────────────────────
    log.info("No SMS provider configured. OTP returned in API response (demo mode).")
    return {
        "sent":     False,
        "provider": "skipped",
        "message":  "No SMS provider configured. OTP shown in API response (demo mode).",
    }


def _send_twilio(phone: str, message_text: str, sid: str, token: str, from_: str) -> dict:
    try:
        from twilio.rest import Client  # type: ignore
        client = Client(sid, token)
        # Ensure E.164 format — prepend +91 for Indian numbers if no country code
        to = _to_e164(phone)
        client.messages.create(body=message_text, from_=from_, to=to)
        log.info("Twilio SMS sent to %s", to)
        return {"sent": True, "provider": "twilio", "message": f"OTP sent via SMS to {_mask(phone)}"}
    except ImportError:
        return {"sent": False, "provider": "twilio_error", "message": "twilio package not installed. Run: pip install twilio"}
    except Exception as e:
        log.error("Twilio error: %s", e)
        return {"sent": False, "provider": "twilio_error", "message": f"SMS failed: {e}"}


def _send_fast2sms(phone: str, otp: str, message_text: str, api_key: str) -> dict:
    try:
        import requests  # type: ignore
        mobile = phone.lstrip("+").lstrip("91")[-10:]  # 10-digit Indian number

        # Try Quick SMS route (no DLT registration required)
        resp = requests.post(
            "https://www.fast2sms.com/dev/bulkV2",
            headers={"authorization": api_key},
            data={
                "route":   "q",
                "message": message_text,
                "numbers": mobile,
                "flash":   "0",
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("return") is True:
            log.info("Fast2SMS Quick SMS sent to %s", mobile)
            return {"sent": True, "provider": "fast2sms", "message": f"OTP sent via SMS to {_mask(phone)}"}

        # Quick route failed — log and return error
        log.error("Fast2SMS error: %s", data)
        msg = data.get("message", ["Unknown error"])
        msg = msg[0] if isinstance(msg, list) else str(msg)
        return {"sent": False, "provider": "fast2sms_error", "message": f"Fast2SMS: {msg}"}
    except Exception as e:
        log.error("Fast2SMS error: %s", e)
        return {"sent": False, "provider": "fast2sms_error", "message": f"SMS failed: {e}"}


def _to_e164(phone: str) -> str:
    """Convert 10-digit Indian number to E.164 (+91XXXXXXXXXX)."""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return f"+91{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    return f"+{digits}"


def _mask(phone: str) -> str:
    """Mask phone for logs: 9876543210 → ******3210"""
    digits = "".join(c for c in phone if c.isdigit())
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"
