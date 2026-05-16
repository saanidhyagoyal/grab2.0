"""
Nudge Agent
===========
Standalone agent that generates hyper-personalised financial nudges
using the driver's real account data.

Part of the GrabHack Financial Wellness multi-agent system.
Internally delegates to the wellness_agent crew and extracts the nudges section.
"""

from com.gxs.bank.agents.wellness_agent import run_financial_wellness


def run_nudges(profile: dict) -> dict:
    """
    Generate 5 personalised nudges for today.
    Lightweight wrapper over the full wellness crew — only returns nudges.
    """
    result = run_financial_wellness(profile)
    return {
        "nudges": result.get("nudges", []),
        "mode": result.get("mode", "deterministic_fallback"),
        "reasoning_log": (
            f"Step 1: Retrieved income=S${profile['income_30d']:,.0f}, "
            f"savings_rate={profile['savings_rate_pct']}%\n"
            f"Step 2: Ran Financial Wellness crew\n"
            f"Step 3: Extracted nudges array from crew output\n"
            f"Step 4: Returned {len(result.get('nudges', []))} nudges"
        ),
    }
