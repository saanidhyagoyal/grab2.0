"""
Supervisor Agent
================
LangGraph-based supervisor that orchestrates all specialist agents.

Key improvements over the flat orchestrator_graph:
  1. Supervisor node routes dynamically — can call multiple agents in sequence
  2. Multi-agent workflows (e.g. "should I take a loan?" → credit + income + wellness)
  3. Results accumulate and are synthesised into a unified response
  4. Every routing decision is logged in routing_decisions (full audit trail)
  5. ChromaDB memory provides context from similar past analyses
  6. All invocations logged to SQLite + JSONL via audit_logger

Supported single-agent intents:
  wellness | fraud | credit | income | nudges | health | executor | chat

Multi-agent workflows (supervisor calls agents in order):
  full_analysis   → wellness  + credit + health
  loan_assessment → credit + income + wellness

Install langgraph:  pip install langgraph
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional, TypedDict

log = logging.getLogger("supervisor_agent")

# ── LangGraph ──────────────────────────────────────────────────────────────────
try:
    from langgraph.graph import END, StateGraph  # type: ignore
    _LANGGRAPH = True
except ImportError:
    _LANGGRAPH = False


# ── State ──────────────────────────────────────────────────────────────────────

class SupervisorState(TypedDict):
    user_id:          str
    message:          str
    original_intent:  str           # high-level intent, e.g. "full_analysis"
    current_route:    str           # which agent node to call next
    profile:          Optional[dict]
    result:           Optional[dict]  # accumulated results keyed by agent name
    db:               Any             # SQLAlchemy Session — not checkpointed
    agents_called:    list             # ["credit", "income", ...]
    routing_decisions: list            # human-readable supervisor decisions
    iteration:        int
    final:            bool             # True → supervisor routes to END


# ── Intent classification ─────────────────────────────────────────────────────

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "wellness":        ["wellness", "saving", "savings", "budget", "income analysis",
                        "monthly plan", "financial plan", "spending"],
    "fraud":           ["fraud", "suspicious", "scam", "hack", "block", "risk",
                        "unusual", "anomaly", "secure", "security"],
    "credit":          ["credit", "gigscore", "gig score", "loan eligib", "borrow",
                        "credit score"],
    "income":          ["predict", "forecast", "future income", "next week",
                        "next month", "income trend"],
    "nudges":          ["nudge", "tip", "advice", "suggest"],
    "health":          ["health score", "grade", "overall score", "composite"],
    "executor":        ["auto", "execute", "automatic", "action", "move money",
                        "schedule transfer", "spending limit"],
    "full_analysis":   ["full analysis", "complete analysis", "everything",
                        "all agents", "comprehensive", "overall picture"],
    "loan_assessment": ["should i take a loan", "can i get a loan", "loan eligibility",
                        "afford a loan", "loan assessment", "qualify for loan"],
}

_MULTI_AGENT_PLANS: dict[str, list[str]] = {
    "full_analysis":   ["wellness", "credit", "health"],
    "loan_assessment": ["credit", "income", "wellness"],
}

_SINGLE_AGENTS = {"wellness", "fraud", "credit", "income", "nudges", "health", "executor", "chat"}
_MAX_ITERATIONS = 8


def _classify(message: str) -> str:
    msg = message.lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            return intent
    return "chat"


# ── Supervisor node ───────────────────────────────────────────────────────────

def supervisor_node(state: SupervisorState) -> SupervisorState:
    iteration = (state.get("iteration") or 0) + 1
    agents_called     = list(state.get("agents_called") or [])
    routing_decisions = list(state.get("routing_decisions") or [])

    # Classify intent on first call (when original_intent is empty)
    original_intent = state.get("original_intent") or _classify(state.get("message", ""))

    # Safety: cap iterations
    if iteration > _MAX_ITERATIONS:
        routing_decisions.append(f"[{iteration}] Max iterations reached. Forcing END.")
        return {
            **state,
            "original_intent":  original_intent,
            "current_route":    "END",
            "final":            True,
            "iteration":        iteration,
            "routing_decisions": routing_decisions,
        }

    # ── Multi-agent workflow ──────────────────────────────────────────────────
    if original_intent in _MULTI_AGENT_PLANS:
        plan = _MULTI_AGENT_PLANS[original_intent]
        next_agent = next((a for a in plan if a not in agents_called), None)

        if next_agent is None:
            routing_decisions.append(
                f"[{iteration}] All agents done {plan}. Synthesising.")
            result = _synthesise(state)
            return {
                **state,
                "original_intent":  original_intent,
                "current_route":    "END",
                "result":           result,
                "final":            True,
                "iteration":        iteration,
                "routing_decisions": routing_decisions,
            }
        else:
            routing_decisions.append(
                f"[{iteration}] Calling {next_agent} "
                f"(plan={plan}, done={agents_called})")
            return {
                **state,
                "original_intent":  original_intent,
                "current_route":    next_agent,
                "final":            False,
                "iteration":        iteration,
                "routing_decisions": routing_decisions,
            }

    # ── Single-agent ──────────────────────────────────────────────────────────
    target = original_intent if original_intent in _SINGLE_AGENTS else "chat"
    if target not in agents_called:
        routing_decisions.append(f"[{iteration}] Calling {target}")
        return {
            **state,
            "original_intent":  original_intent,
            "current_route":    target,
            "final":            False,
            "iteration":        iteration,
            "routing_decisions": routing_decisions,
        }
    else:
        routing_decisions.append(f"[{iteration}] {target} done. Ending.")
        return {
            **state,
            "original_intent":  original_intent,
            "current_route":    "END",
            "final":            True,
            "iteration":        iteration,
            "routing_decisions": routing_decisions,
        }


def _supervisor_route(state: SupervisorState):
    if state.get("final"):
        return END
    route = state.get("current_route", "chat")
    return route if route in _SINGLE_AGENTS else END


# ── Agent node factory ────────────────────────────────────────────────────────

def _make_node(agent_key: str, run_fn):
    def _node(state: SupervisorState) -> SupervisorState:
        t0 = time.time()
        try:
            res = run_fn(state)
        except Exception as exc:
            log.error("Agent %s failed: %s", agent_key, exc)
            res = {"error": str(exc), "agent": agent_key}

        # Accumulate into result dict
        accumulated = dict(state.get("result") or {})
        accumulated[agent_key] = res

        agents_called = list(state.get("agents_called") or [])
        if agent_key not in agents_called:
            agents_called.append(agent_key)

        # Store to ChromaDB memory
        try:
            from com.gxs.bank.agents.agent_memory import store_memory
            store_memory(state["user_id"], agent_key, res, state.get("message", ""))
        except Exception:
            pass

        log.info("Agent %s completed in %.0fms", agent_key, (time.time() - t0) * 1000)
        return {**state, "result": accumulated, "agents_called": agents_called}
    return _node


# ── Agent runner functions ────────────────────────────────────────────────────

def _run_wellness(state):
    from com.gxs.bank.agents.orchestrator import get_financial_wellness
    return get_financial_wellness(state["user_id"], state["db"])


def _run_fraud(state):
    from com.gxs.bank.agents.orchestrator import get_fraud_analysis
    return get_fraud_analysis(state["user_id"], state["db"])


def _run_credit(state):
    from com.gxs.bank.agents.orchestrator import get_credit_score
    return get_credit_score(state["user_id"], state["db"])


def _run_income(state):
    from com.gxs.bank.agents.orchestrator import get_income_prediction
    return get_income_prediction(state["user_id"], state["db"])


def _run_nudges(state):
    from com.gxs.bank.agents.orchestrator import get_nudges
    return get_nudges(state["user_id"], state["db"])


def _run_health(state):
    from com.gxs.bank.agents.orchestrator import get_financial_health_score
    return get_financial_health_score(state["user_id"], state["db"])


def _run_executor(state):
    from com.gxs.bank.agents.auto_executor_agent import run_auto_executor
    from com.gxs.bank.agents.data_fetcher import get_user_financial_profile
    profile = state.get("profile") or get_user_financial_profile(state["user_id"], state["db"])
    return run_auto_executor(profile, state["db"])


def _run_chat(state):
    from com.gxs.bank.agents.orchestrator import run_chat
    # Enrich message with ChromaDB context
    context_hint = ""
    try:
        from com.gxs.bank.agents.agent_memory import retrieve_context
        memories = retrieve_context(state["user_id"], state.get("message", ""), n_results=2)
        if memories:
            snippets = "; ".join(m["content"][:80] for m in memories)
            context_hint = f" [Past context: {snippets}]"
    except Exception:
        pass
    enriched = state.get("message", "") + context_hint
    return run_chat(state["user_id"], enriched, state["db"])


_AGENT_FNS: dict[str, Any] = {
    "wellness": _run_wellness,
    "fraud":    _run_fraud,
    "credit":   _run_credit,
    "income":   _run_income,
    "nudges":   _run_nudges,
    "health":   _run_health,
    "executor": _run_executor,
    "chat":     _run_chat,
}


# ── Result synthesis ──────────────────────────────────────────────────────────

def _synthesise(state: SupervisorState) -> dict:
    accumulated   = state.get("result") or {}
    agents_called = list(state.get("agents_called") or [])

    synthesis: dict = {
        "synthesized":       True,
        "agents_consulted":  agents_called,
        "routing_chain":     list(state.get("routing_decisions") or []),
    }

    # Flatten sub-results (first occurrence wins for duplicate keys)
    for agent, data in accumulated.items():
        if isinstance(data, dict):
            for k, v in data.items():
                if k not in synthesis:
                    synthesis[k] = v

    # Human-readable summary
    parts = []
    if synthesis.get("health_score"):
        parts.append(f"Health score {synthesis['health_score']}/100")
    if synthesis.get("gig_score"):
        parts.append(f"GigScore {synthesis['gig_score']}")
    ra = synthesis.get("risk_assessment", {})
    if ra.get("risk_level"):
        parts.append(f"Fraud risk {ra['risk_level']}")
    if parts:
        synthesis["synthesis_summary"] = " | ".join(parts)

    return synthesis


# ── Graph construction (singleton) ───────────────────────────────────────────

_graph = None


def _build_graph():
    if not _LANGGRAPH:
        return None
    try:
        g = StateGraph(SupervisorState)

        g.add_node("supervisor", supervisor_node)
        for name, fn in _AGENT_FNS.items():
            g.add_node(name, _make_node(name, fn))
            g.add_edge(name, "supervisor")   # all agents loop back to supervisor

        g.set_entry_point("supervisor")
        g.add_conditional_edges(
            "supervisor",
            _supervisor_route,
            {**{k: k for k in _SINGLE_AGENTS}, END: END},
        )

        compiled = g.compile()
        log.info("Supervisor graph compiled successfully.")
        return compiled
    except Exception as exc:
        log.error("Failed to build supervisor graph: %s", exc)
        return None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


# ── Public API ────────────────────────────────────────────────────────────────

def run_supervisor_graph(user_id: str, message: str, db) -> dict:
    """
    Route a user message through the supervisor graph.
    Classifies intent → supervisor → agent(s) → optional synthesis → audit log.
    Always returns a dict with `graph_mode`, `detected_intent`, `routing_chain`.
    """
    t0    = time.time()
    graph = _get_graph()

    # ── Fallback: no LangGraph ────────────────────────────────────────────────
    if graph is None:
        from com.gxs.bank.agents.orchestrator import run_chat
        result = run_chat(user_id, message, db)
        result.update({
            "graph_mode":      "fallback_no_langgraph",
            "detected_intent": "chat",
            "routing_chain":   [],
            "agents_called":   [],
        })
        _audit(user_id, "chat", "chat", message, result,
               (time.time() - t0) * 1000, [], "fallback_no_langgraph", db)
        return result

    initial: SupervisorState = {
        "user_id":          user_id,
        "message":          message,
        "original_intent":  "",
        "current_route":    "",
        "profile":          None,
        "result":           None,
        "db":               db,
        "agents_called":    [],
        "routing_decisions": [],
        "iteration":        0,
        "final":            False,
    }

    # ── Invoke ────────────────────────────────────────────────────────────────
    try:
        final_state = graph.invoke(initial)
    except Exception as exc:
        log.error("Supervisor graph invocation error: %s", exc)
        from com.gxs.bank.agents.orchestrator import run_chat
        result = run_chat(user_id, message, db)
        result.update({
            "graph_mode":      "supervisor_error_fallback",
            "detected_intent": "chat",
            "routing_chain":   [],
            "agents_called":   [],
            "graph_error":     str(exc),
        })
        _audit(user_id, "chat", "chat", message, result,
               (time.time() - t0) * 1000, [], "error", db)
        return result

    # ── Extract result ────────────────────────────────────────────────────────
    original_intent = final_state.get("original_intent", "chat")
    agents_called   = final_state.get("agents_called", [])
    routing_chain   = final_state.get("routing_decisions", [])
    accumulated     = final_state.get("result") or {}
    duration_ms     = (time.time() - t0) * 1000

    if accumulated.get("synthesized"):
        # Multi-agent synthesised result (already flat)
        result = dict(accumulated)
    elif len(agents_called) == 1:
        # Single agent: unpack sub-dict
        result = dict(accumulated.get(agents_called[0]) or accumulated)
    elif len(agents_called) > 1:
        # Multi-agent but synthesis wasn't triggered (edge case)
        result = _synthesise(final_state)
    else:
        result = {}

    result["graph_mode"]      = "supervisor"
    result["detected_intent"] = original_intent
    result["routing_chain"]   = routing_chain
    result["agents_called"]   = agents_called

    _audit(user_id, "supervisor", original_intent, message, result,
           duration_ms, routing_chain, "supervisor", db)
    return result


def _audit(user_id, agent_name, intent, message, result,
           duration_ms, routing_chain, graph_mode, db):
    try:
        from com.gxs.bank.agents.audit_logger import log_agent_call
        log_agent_call(
            user_id=user_id,
            agent_name=agent_name,
            intent=intent,
            input_message=message,
            output=result,
            duration_ms=duration_ms,
            routing_chain=routing_chain,
            agents_called=result.get("agents_called", []),
            graph_mode=graph_mode,
            db=db,
        )
    except Exception as exc:
        log.warning("Audit log failed: %s", exc)


def supervisor_graph_status() -> dict:
    graph = _get_graph()
    try:
        from com.gxs.bank.agents.agent_memory import memory_status
        mem = memory_status()
    except Exception:
        mem = {"chroma_available": False}
    return {
        "langgraph_available":    _LANGGRAPH,
        "supervisor_compiled":    graph is not None,
        "nodes":                  ["supervisor"] + list(_AGENT_FNS.keys()),
        "single_agent_intents":   sorted(_SINGLE_AGENTS),
        "multi_agent_plans":      _MULTI_AGENT_PLANS,
        "max_iterations":         _MAX_ITERATIONS,
        "memory":                 mem,
    }
