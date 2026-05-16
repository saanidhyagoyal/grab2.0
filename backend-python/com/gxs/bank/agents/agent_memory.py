"""
ChromaDB Agent Memory
======================
Persistent vector store for agent interactions.
Allows the supervisor to recall semantically similar past analyses
when handling a new request.

Install: pip install chromadb
If ChromaDB is unavailable, all operations are silent no-ops.

Storage:  backend-python/chroma_agent_memory/  (auto-created)
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger("agent_memory")

_CHROMA_AVAILABLE = False
_collection = None

try:
    import chromadb  # type: ignore
    _CHROMA_AVAILABLE = True
except ImportError:
    pass

_CHROMA_PATH = str(Path(__file__).resolve().parents[4] / "chroma_agent_memory")


# ── Collection singleton ──────────────────────────────────────────────────────

def _get_collection():
    global _collection
    if not _CHROMA_AVAILABLE:
        return None
    if _collection is not None:
        return _collection
    try:
        client = chromadb.PersistentClient(path=_CHROMA_PATH)
        _collection = client.get_or_create_collection(
            name="agent_memory",
            metadata={"hnsw:space": "cosine"},
        )
        log.info("ChromaDB ready at %s (docs: %d)", _CHROMA_PATH, _collection.count())
        return _collection
    except Exception as exc:
        log.warning("ChromaDB init failed (memory disabled): %s", exc)
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def store_memory(user_id: str, agent_type: str, result: dict, message: str = "") -> bool:
    """Embed and store an agent result for future retrieval."""
    col = _get_collection()
    if col is None:
        return False
    try:
        doc_id = f"{user_id}__{agent_type}__{int(datetime.utcnow().timestamp() * 1000)}"
        text = _to_text(agent_type, result, message)
        col.add(
            documents=[text],
            metadatas=[{
                "user_id":    user_id,
                "agent_type": agent_type,
                "timestamp":  datetime.utcnow().isoformat(),
                "message":    (message or "")[:200],
            }],
            ids=[doc_id],
        )
        return True
    except Exception as exc:
        log.debug("ChromaDB store failed: %s", exc)
        return False


def retrieve_context(user_id: str, query: str, n_results: int = 3) -> list[dict]:
    """Return past analyses semantically similar to the query."""
    col = _get_collection()
    if col is None:
        return []
    try:
        total = col.count()
        if total == 0:
            return []
        res = col.query(
            query_texts=[query],
            n_results=min(n_results, total),
            where={"user_id": user_id},
        )
        memories = []
        if res and res.get("documents"):
            for i, doc in enumerate(res["documents"][0]):
                meta = (res.get("metadatas") or [[]])[0][i] if res.get("metadatas") else {}
                dist = (res.get("distances") or [[1.0]])[0][i]
                memories.append({
                    "content":    doc,
                    "agent_type": meta.get("agent_type", ""),
                    "timestamp":  meta.get("timestamp", ""),
                    "relevance":  round(1.0 - dist, 3),
                })
        return memories
    except Exception as exc:
        log.debug("ChromaDB query failed: %s", exc)
        return []


def memory_status() -> dict:
    col = _get_collection()
    return {
        "chroma_available":  _CHROMA_AVAILABLE,
        "collection_ready":  col is not None,
        "total_memories":    col.count() if col else 0,
        "storage_path":      _CHROMA_PATH if _CHROMA_AVAILABLE else None,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_text(agent_type: str, result: dict, message: str) -> str:
    parts = [f"[{agent_type}]"]
    if message:
        parts.append(f"query={message[:100]}")

    if agent_type == "fraud":
        ra = result.get("risk_assessment", {})
        parts.append(f"risk={ra.get('risk_level', '?')}")
        factors = ra.get("risk_factors", [])
        if factors:
            parts.append(f"factors={','.join(str(f) for f in factors[:3])}")
    elif agent_type == "wellness":
        if result.get("health_score"):
            parts.append(f"wellness_score={result['health_score']}")
        recs = result.get("recommendations", [])
        if recs:
            parts.append(f"recs={';'.join(str(r) for r in recs[:2])}")
    elif agent_type == "credit":
        if result.get("gig_score"):
            parts.append(f"gig_score={result['gig_score']}")
    elif agent_type == "health":
        parts.append(f"health={result.get('health_score','?')} grade={result.get('grade','?')}")
    elif agent_type == "income":
        fw = result.get("weekly_forecast", [])
        if fw:
            parts.append(f"forecast_weeks={len(fw)}")
    elif agent_type == "executor":
        actions = result.get("actions", [])
        executed = [a.get("title", "") for a in actions if a.get("status") == "executed"]
        if executed:
            parts.append(f"executed={';'.join(executed[:3])}")
    elif agent_type == "nudges":
        nudges = result.get("nudges", [])
        if nudges:
            parts.append(f"nudges={len(nudges)}")

    for key in ("answer", "summary"):
        if key in result:
            parts.append(f"{key}={str(result[key])[:100]}")

    return " | ".join(parts)
