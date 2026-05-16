"""
Transaction Embedding & Categorisation
=======================================
Uses sentence-transformers to embed transaction descriptions and classify
them into meaningful semantic categories using cosine similarity.

Falls back to keyword rules if sentence-transformers is unavailable.

Categories (8):
  Food & Dining, Transport & Fuel, Shopping, Bills & Utilities,
  Entertainment, Healthcare, EMI & Debt, Income & Transfers
"""

import re
from functools import lru_cache

import numpy as np

# ── sentence-transformers availability ──────────────────────────────────────
EMBEDDINGS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    pass

# ── Category definitions with anchor phrases ─────────────────────────────────
CATEGORIES = {
    "Food & Dining": [
        "food order delivery restaurant meal swiggy zomato lunch dinner breakfast cafe",
        "grocery supermarket provisions eating out dining fast food",
    ],
    "Transport & Fuel": [
        "grab ride taxi cab ola uber auto rickshaw petrol diesel fuel",
        "metro bus train commute travel transport parking toll",
    ],
    "Shopping": [
        "amazon flipkart shopping purchase store retail myntra nykaa",
        "clothes electronics gadgets accessories online order",
    ],
    "Bills & Utilities": [
        "electricity bill water gas broadband internet mobile recharge",
        "utility payment bescom tata power airtel jio bsnl",
        "insurance premium health policy renewal",
    ],
    "Entertainment": [
        "netflix hotstar prime video spotify youtube subscription streaming",
        "movie cinema concert event gaming entertainment leisure",
    ],
    "Healthcare": [
        "hospital pharmacy medicine doctor consultation clinic",
        "medical lab test health checkup apollo fortis",
    ],
    "EMI & Debt": [
        "emi loan repayment instalment debt credit card payment",
        "personal loan home loan vehicle loan monthly payment",
    ],
    "Income & Transfers": [
        "salary credit refund received transfer cashback reward",
        "income payment received from bonus incentive",
    ],
}

# Flat list of (category, anchor) tuples for embedding
_ANCHORS: list[tuple[str, str]] = [
    (cat, phrase)
    for cat, phrases in CATEGORIES.items()
    for phrase in phrases
]

# ── Keyword fallback rules ───────────────────────────────────────────────────
_KEYWORD_RULES: list[tuple[str, list[str]]] = [
    ("Food & Dining",       ["swiggy", "zomato", "food", "restaurant", "cafe", "meal", "grocery", "dining"]),
    ("Transport & Fuel",    ["grab", "ola", "uber", "fuel", "petrol", "diesel", "metro", "bus", "train", "toll", "parking"]),
    ("Shopping",            ["amazon", "flipkart", "myntra", "shopping", "purchase", "retail", "store"]),
    ("Bills & Utilities",   ["electricity", "bill", "water", "gas", "broadband", "internet", "mobile", "recharge", "utility", "insurance"]),
    ("Entertainment",       ["netflix", "hotstar", "prime", "spotify", "youtube", "cinema", "movie", "gaming", "subscription"]),
    ("Healthcare",          ["hospital", "pharmacy", "medicine", "doctor", "clinic", "medical", "health"]),
    ("EMI & Debt",          ["emi", "loan", "repayment", "instalment", "credit card payment"]),
    ("Income & Transfers",  ["salary", "credit", "refund", "received", "transfer", "cashback", "bonus"]),
]


@lru_cache(maxsize=1)
def _get_model():
    """Load model once and cache it. Uses a small, fast model."""
    return SentenceTransformer("all-MiniLM-L6-v2")


@lru_cache(maxsize=1)
def _get_anchor_embeddings():
    """Pre-compute anchor embeddings once."""
    model = _get_model()
    anchor_texts = [phrase for _, phrase in _ANCHORS]
    return model.encode(anchor_texts, normalize_embeddings=True)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Cosine similarity between a single vector and a matrix of vectors."""
    return np.dot(b, a)  # both already L2-normalised


def categorise_description(description: str) -> str:
    """
    Returns the best-matching category for a transaction description.
    Uses embeddings if available, else keyword rules.
    """
    if not description:
        return "Other"

    text = description.strip()

    if EMBEDDINGS_AVAILABLE:
        try:
            return _categorise_with_embeddings(text)
        except Exception:
            pass

    return _categorise_with_keywords(text)


def _categorise_with_embeddings(text: str) -> str:
    model = _get_model()
    anchor_embeddings = _get_anchor_embeddings()

    query_vec = model.encode([text], normalize_embeddings=True)[0]
    similarities = _cosine_similarity(query_vec, anchor_embeddings)

    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])

    # If similarity too low, return Other
    if best_score < 0.25:
        return "Other"

    return _ANCHORS[best_idx][0]


def _categorise_with_keywords(text: str) -> str:
    lower = text.lower()
    for category, keywords in _KEYWORD_RULES:
        if any(kw in lower for kw in keywords):
            return category
    return "Other"


def categorise_transactions(transactions: list[dict]) -> dict[str, float]:
    """
    Takes a list of expense transaction dicts (with 'description' and 'amount')
    and returns a dict of category -> total amount.

    Each dict must have: description (str), amount (float)
    """
    totals: dict[str, float] = {}
    for txn in transactions:
        desc = txn.get("description", "")
        amount = float(txn.get("amount", 0))
        category = categorise_description(desc)
        totals[category] = totals.get(category, 0.0) + amount
    return totals


def get_embedding_mode() -> str:
    """Returns which mode is active for transparency."""
    if EMBEDDINGS_AVAILABLE:
        return "sentence_transformers"
    return "keyword_rules"
