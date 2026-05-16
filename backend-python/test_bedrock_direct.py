#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load .env explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from com.gxs.bank.agents.llm_config import (
    _has_bedrock_credentials, BEDROCK_AVAILABLE, 
    _get_bedrock_client, direct_llm_call
)

print("=" * 70)
print("BEDROCK CREDENTIAL CHECK")
print("=" * 70)
print(f"AWS_ACCESS_KEY_ID set: {bool(os.getenv('AWS_ACCESS_KEY_ID'))}")
print(f"AWS_SECRET_ACCESS_KEY set: {bool(os.getenv('AWS_SECRET_ACCESS_KEY'))}")
print(f"AWS_SESSION_TOKEN set: {bool(os.getenv('AWS_SESSION_TOKEN'))}")
print(f"BEDROCK_AVAILABLE: {BEDROCK_AVAILABLE}")
print(f"_has_bedrock_credentials(): {_has_bedrock_credentials()}")

client = _get_bedrock_client()
print(f"Bedrock client created: {client is not None}")
print()

print("=" * 70)
print("DIRECT LLM CALL TEST")
print("=" * 70)
result = direct_llm_call("Say 'SUCCESS' only", "Reply with only 'SUCCESS'")
print(f"Result: {repr(result)}")
print(f"Result length: {len(result)}")
print()

print("=" * 70)
print("ADVISOR CHAT TEST")
print("=" * 70)
from com.gxs.bank.agents.gemini_advisor import advisor_chat

profile = {
    "user_id": "test", "total_balance": 5000, "income_30d": 8500,
    "expense_30d": 3200, "savings_30d": 5300, "savings_rate_pct": 62.4,
    "gig_score": 720, "active_loans_count": 1, "total_monthly_emi": 800,
    "emi_to_income_pct": 9.4, "total_outstanding_debt": 12000,
    "expense_by_category": {"food": 1200, "transport": 500, "utilities": 300, "other": 1200},
    "loans": [{"loanType": "Personal", "outstandingAmount": 12000}]
}

result = advisor_chat(profile, "How can I save more money?", [])
print(f"✅ Fallback used? {('chat_error' in result)}")
print(f"   Mode: {result.get('mode')}")
print(f"   Answer (first 150): {str(result.get('answer', ''))[:150]}...")
