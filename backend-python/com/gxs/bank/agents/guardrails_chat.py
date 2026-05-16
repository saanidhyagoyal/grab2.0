"""
Chat Guardrails
===============
Input and output validation for the AI chat agent.

Input guardrails  — block before sending to LLM:
  1. Empty / too short messages
  2. Messages that are too long (token abuse)
  3. Prompt injection attempts
  4. Off-topic requests (non-financial)
  5. PII in input (credit card numbers, passwords)

Output guardrails — validate before returning to user:
  1. Response must not be empty
  2. Strip any PII that leaked into LLM response
  3. Fallback message if response looks broken
"""

import re

# ── Input validation ──────────────────────────────────────────────────────────

# Prompt injection patterns
_INJECTION_PATTERNS = [
    r"ignore (all |previous |prior |above |the )?(instructions?|prompts?|rules?|guidelines?)",
    r"you are now",
    r"act as (a |an )?(different|new|another|evil|unrestricted)",
    r"disregard (your|all|any)",
    r"forget (everything|all|your instructions)",
    r"new (system|personality|role|instructions?)",
    r"jailbreak",
    r"dan mode",
    r"do anything now",
    r"pretend (you|to be|that)",
    r"override (your|the|all)",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# Financial topic keywords — at least one must be present to proceed.
# Deliberately excludes generic words like "how", "my", "can", "when" etc.
# which match virtually any sentence and made the filter useless.
_FINANCIAL_KEYWORDS = [
    # Core banking
    "balance", "money", "spend", "spent", "spending", "saving", "savings", "save",
    "income", "earn", "earning", "earnings", "loan", "emi", "debt",
    "invest", "investment", "account", "transfer", "bill", "expense",
    "budget", "salary", "credit", "debit", "card", "afford",
    "fund", "cash", "payment", "finance", "financial", "bank", "banking",
    "deposit", "withdraw", "withdrawal", "interest", "rate",
    # Currency
    "pay", "cost", "price", "rupee", "inr", "sgd", "dollar",
    # Fraud & security
    "fraud", "suspicious", "unusual", "security", "scam", "transaction",
    "block", "lock", "otp", "verify", "alert", "risk",
    # AI features
    "analyse", "analyze", "predict", "forecast", "prediction",
    "score", "gigscore", "gig score", "wellness", "nudge", "tip",
    "health score", "peak hour",
    # Gig economy
    "gig", "driver", "ride", "grab",
    # Actions
    "automat", "execut", "schedule", "fixed deposit", "fd",
]

# Harmless generic prompts are allowed, but only for short conversational turns.
_HARMLESS_GENERIC_PATTERNS = [
    r"^(hi|hello|hey|hiya|good morning|good afternoon|good evening)\b",
    r"^(thanks|thank you|thx|appreciate it)\b",
    r"^(how are you|who are you|what can you do|what do you do|help me|can you help)\b",
    r"^(are you there|is anyone there|goodbye|bye)\b",
]
_HARMLESS_GENERIC_RE = re.compile("|".join(_HARMLESS_GENERIC_PATTERNS), re.IGNORECASE)


# PII patterns to scrub from output
_PII_PATTERNS = [
    (re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"), "[CARD REDACTED]"),   # credit card
    (re.compile(r"\b\d{10,12}\b"), "[ACCOUNT REDACTED]"),                                   # long number
    (re.compile(r"password[\s:=]+\S+", re.IGNORECASE), "[REDACTED]"),                       # password
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[PAN REDACTED]"),                             # PAN card
]


class GuardrailsError(Exception):
    """Raised when input fails a guardrail check."""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code
        self.user_message = message


def classify_message(message: str) -> dict:
    """Classify a message so the advisor can distinguish finance vs harmless generic chat."""
    cleaned = (message or "").strip()
    lower = cleaned.lower()

    if not cleaned:
        return {"category": "empty", "allowed": False, "message": cleaned}

    if _INJECTION_RE.search(cleaned):
        return {"category": "injection", "allowed": False, "message": cleaned}

    is_financial = any(kw in lower for kw in _FINANCIAL_KEYWORDS)
    is_generic = bool(_HARMLESS_GENERIC_RE.search(cleaned))

    if is_financial:
        return {"category": "financial", "allowed": True, "message": cleaned}

    if is_generic:
        return {"category": "harmless_generic", "allowed": True, "message": cleaned}

    return {"category": "off_topic", "allowed": False, "message": cleaned}


def validate_input(message: str) -> str:
    """
    Validates and cleans chat input.
    Returns cleaned message or raises GuardrailsError.
    """
    if not message or not message.strip():
        raise GuardrailsError(
            "Please type a message before sending.",
            "EMPTY_INPUT"
        )

    cleaned = message.strip()

    # Length check — allow short greetings like "Hi", "Ok"
    if len(cleaned) < 2:
        raise GuardrailsError(
            "Your message is too short. Try asking a full question.",
            "TOO_SHORT"
        )

    if len(cleaned) > 500:
        raise GuardrailsError(
            "Your message is too long. Please keep it under 500 characters.",
            "TOO_LONG"
        )

    # Prompt injection check
    if _INJECTION_RE.search(cleaned):
        raise GuardrailsError(
            "I can only help with questions about your finances. Please ask something relevant.",
            "INJECTION_DETECTED"
        )

    # PII in input — scrub silently (don't block, just clean)
    for pattern, replacement in _PII_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)

    # Off-topic check — allow harmless greetings/help, but block unrelated topics.
    classification = classify_message(cleaned)
    if classification["category"] == "off_topic":
        raise GuardrailsError(
            "That's an interesting question! However, I'm your financial advisor and can only help with money-related topics. "
            "Try asking me about your balance, spending habits, savings, loans, income prediction, fraud alerts, GigScore, or even a quick hello — "
            "I'd love to help with those! 💰",
            "OFF_TOPIC"
        )

    return cleaned


def validate_output(response: dict) -> dict:
    """
    Validates and cleans agent chat output.
    Returns cleaned response dict.
    """
    answer = response.get("answer", "")
    tip = response.get("action_tip", "")

    # Empty response guard
    if not answer or not answer.strip():
        response["answer"] = "I couldn't generate a response right now. Please try again."
        response["action_tip"] = ""
        return response

    # Scrub PII from answer and tip
    for pattern, replacement in _PII_PATTERNS:
        answer = pattern.sub(replacement, answer)
        tip = pattern.sub(replacement, tip)

    # Truncate if LLM went too long
    if len(answer) > 1000:
        answer = answer[:997] + "..."

    response["answer"] = answer.strip()
    response["action_tip"] = tip.strip()
    return response


def guardrails_summary() -> dict:
    """Returns which guardrails are active — for transparency in API response."""
    return {
        "input_checks": ["empty", "length", "injection", "off_topic", "harmless_generic", "pii_scrub"],
        "output_checks": ["empty_response", "pii_scrub", "length_cap"],
        "policy": "financial-first with harmless generic greetings/help allowed",
    }
