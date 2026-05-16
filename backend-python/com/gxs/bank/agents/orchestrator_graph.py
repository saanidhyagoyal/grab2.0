"""
LangGraph-based Agent Orchestrator
=====================================
Replaces the flat function calls in orchestrator.py with a StateGraph
workflow that classifies intent and routes to the appropriate agent node.

Graph topology:
  START → classify_intent → [wellness | fraud | credit | income |
                               nudges  | health | executor | chat]
        → END

If langgraph is not installed, falls back gracefully to the direct
orchestrator functions with a flag in the response.

Install: pip install langgraph
"""
from __future__ import annotations

from typing import Any, Optional, TypedDict

from sqlalchemy.orm import Session

# ── LangGraph availability ───────────────────────────────────────────────────
try:
    from langgraph.graph import END, StateGraph  # type: ignore
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


# ── State schema ─────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    user_id: str
    message: str
    intent: str
    profile: Optional[dict]
    result: Optional[dict]
    db: Any   # SQLAlchemy Session — not persisted, in-process only


# ── Intent classification ────────────────────────────────────────────────────

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "wellness":  ["wellness", "saving", "savings", "budget", "income analysis",
                  "monthly plan", "financial plan"],
    "fraud":     ["fraud", "suspicious", "scam", "hack", "block", "risk",
                  "unusual", "anomaly", "secure"],
    "credit":    ["credit", "gigscore", "gig score", "loan eligib", "borrow",
                  "credit score"],
    "income":    ["predict", "forecast", "future income", "next week",
                  "next month", "income trend"],
    "nudges":    ["nudge", "tip", "advice", "suggest"],
    "health":    ["health score", "grade", "overall score", "composite"],
    "executor":  ["auto", "execute", "automatic", "action", "move money",
                  "schedule transfer", "spending limit"],
}


def classify_intent(state: AgentState) -> AgentState:
    msg = (state.get("message") or "").lower()
    intent = "chat"
    for candidate, keywords in _INTENT_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            intent = candidate
            break
    return {**state, "intent": intent}


def _route(state: AgentState) -> str:
    return state.get("intent", "chat")


# ── Agent nodes ───────────────────────────────────────────────────────────────

def _node_wellness(state: AgentState) -> AgentState:
    from com.gxs.bank.agents.orchestrator import get_financial_wellness
    return {**state, "result": get_financial_wellness(state["user_id"], state["db"])}


def _node_fraud(state: AgentState) -> AgentState:
    from com.gxs.bank.agents.orchestrator import get_fraud_analysis
    return {**state, "result": get_fraud_analysis(state["user_id"], state["db"])}


def _node_credit(state: AgentState) -> AgentState:
    from com.gxs.bank.agents.orchestrator import get_credit_score
    return {**state, "result": get_credit_score(state["user_id"], state["db"])}


def _node_income(state: AgentState) -> AgentState:
    from com.gxs.bank.agents.orchestrator import get_income_prediction
    return {**state, "result": get_income_prediction(state["user_id"], state["db"])}


def _node_nudges(state: AgentState) -> AgentState:
    from com.gxs.bank.agents.orchestrator import get_nudges
    return {**state, "result": get_nudges(state["user_id"], state["db"])}


def _node_health(state: AgentState) -> AgentState:
    from com.gxs.bank.agents.orchestrator import get_financial_health_score
    return {**state, "result": get_financial_health_score(state["user_id"], state["db"])}


def _node_executor(state: AgentState) -> AgentState:
    from com.gxs.bank.agents.auto_executor_agent import run_auto_executor
    from com.gxs.bank.agents.data_fetcher import get_user_financial_profile
    profile = state.get("profile") or get_user_financial_profile(state["user_id"], state["db"])
    return {**state, "result": run_auto_executor(profile, state["db"])}


def _node_chat(state: AgentState) -> AgentState:
    from com.gxs.bank.agents.orchestrator import run_chat
    return {**state, "result": run_chat(state["user_id"], state["message"], state["db"])}


# ── Graph construction (singleton) ───────────────────────────────────────────

_compiled_graph = None


def _build_graph():
    if not LANGGRAPH_AVAILABLE:
        return None

    g = StateGraph(AgentState)

    g.add_node("classify_intent", classify_intent)
    g.add_node("wellness",  _node_wellness)
    g.add_node("fraud",     _node_fraud)
    g.add_node("credit",    _node_credit)
    g.add_node("income",    _node_income)
    g.add_node("nudges",    _node_nudges)
    g.add_node("health",    _node_health)
    g.add_node("executor",  _node_executor)
    g.add_node("chat",      _node_chat)

    g.set_entry_point("classify_intent")

    g.add_conditional_edges(
        "classify_intent",
        _route,
        {
            "wellness": "wellness",
            "fraud":    "fraud",
            "credit":   "credit",
            "income":   "income",
            "nudges":   "nudges",
            "health":   "health",
            "executor": "executor",
            "chat":     "chat",
        },
    )

    for node in ["wellness", "fraud", "credit", "income", "nudges", "health", "executor", "chat"]:
        g.add_edge(node, END)

    return g.compile()


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


# ── Public API ────────────────────────────────────────────────────────────────

def run_graph(user_id: str, message: str, db: Session) -> dict:
    """
    Route a user message through the Supervisor graph.
    Delegates to supervisor_agent.run_supervisor_graph which supports:
    - Single-agent routing
    - Multi-agent workflows (full_analysis, loan_assessment)
    - ChromaDB semantic memory
    - Full audit logging (SQLite + JSONL)
    """
    from com.gxs.bank.agents.supervisor_agent import run_supervisor_graph
    return run_supervisor_graph(user_id, message, db)


def graph_status() -> dict:
    """Returns metadata about the Supervisor + LangGraph setup."""
    from com.gxs.bank.agents.supervisor_agent import supervisor_graph_status
    status = supervisor_graph_status()
    status["langgraph_available"] = LANGGRAPH_AVAILABLE  # backwards compat
    return status
