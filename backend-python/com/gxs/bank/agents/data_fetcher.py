"""
Fetches and structures user financial data from the database for AI agents.
All monetary values returned as floats for easy JSON serialization.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from com.gxs.bank.model.Loan import Loan
from com.gxs.bank.model.Loan import Status as LoanStatus
from com.gxs.bank.model.SavingsAccount import SavingsAccount
from com.gxs.bank.model.Transaction import Transaction
from com.gxs.bank.model.Transaction import Type as TxnType
from com.gxs.bank.agents.embeddings import categorise_transactions, get_embedding_mode

# Transaction types that represent money coming in
INCOME_TYPES = {
    TxnType.CREDIT,
    TxnType.SALARY_CREDIT,
    TxnType.UPI_CREDIT,
    TxnType.TRANSFER_IN,
    TxnType.FD_MATURITY,
    TxnType.INTEREST,
    TxnType.GRAB_PAYOUT,
}

# Income types that represent real gig earnings (excludes lump-sum non-recurring
# items like FD maturity and self-transfers that skew daily income predictions)
GIG_INCOME_TYPES = {
    TxnType.CREDIT,
    TxnType.SALARY_CREDIT,
    TxnType.UPI_CREDIT,
    TxnType.GRAB_PAYOUT,
}

# Transaction types that represent money going out
EXPENSE_TYPES = {
    TxnType.DEBIT,
    TxnType.ATM_WITHDRAWAL,
    TxnType.POS_PURCHASE,
    TxnType.BILL_PAYMENT,
    TxnType.UPI_DEBIT,
    TxnType.TRANSFER_OUT,
    TxnType.EMI,
}


def get_user_financial_profile(user_id: str, db: Session) -> dict:
    """
    Returns a comprehensive financial profile dict for AI agent consumption.
    Covers last 90 days of transaction history + current account/loan state.
    """
    accounts = db.query(SavingsAccount).filter(SavingsAccount.userId == user_id).all()
    total_balance = sum(float(acc.balance or 0) for acc in accounts)
    account_ids = [acc.id for acc in accounts]

    cutoff_90d = datetime.utcnow() - timedelta(days=90)
    cutoff_30d = datetime.utcnow() - timedelta(days=30)
    cutoff_7d = datetime.utcnow() - timedelta(days=7)

    all_txns = []
    if account_ids:
        all_txns = (
            db.query(Transaction)
            .filter(
                Transaction.accountId.in_(account_ids),
                Transaction.createdAt >= cutoff_90d,
            )
            .order_by(Transaction.createdAt.desc())
            .all()
        )

    income_txns = [t for t in all_txns if t.type in INCOME_TYPES]
    expense_txns = [t for t in all_txns if t.type in EXPENSE_TYPES]

    def _sum_amount(txns, since=None):
        return sum(
            float(t.amount or 0)
            for t in txns
            if since is None or t.createdAt >= since
        )

    income_90d = _sum_amount(income_txns)
    expense_90d = _sum_amount(expense_txns)
    income_30d = _sum_amount(income_txns, cutoff_30d)
    expense_30d = _sum_amount(expense_txns, cutoff_30d)
    income_7d = _sum_amount(income_txns, cutoff_7d)

    # Daily income for the last 30 days
    daily_income: dict[str, float] = {}
    daily_gig_income: dict[str, float] = {}  # excludes FD_MATURITY, TRANSFER_IN — for prediction
    daily_expense: dict[str, float] = {}
    for t in all_txns:
        if t.createdAt >= cutoff_30d:
            day = t.createdAt.strftime("%Y-%m-%d")
            if t.type in INCOME_TYPES:
                daily_income[day] = daily_income.get(day, 0) + float(t.amount or 0)
            if t.type in GIG_INCOME_TYPES:
                daily_gig_income[day] = daily_gig_income.get(day, 0) + float(t.amount or 0)
            if t.type in EXPENSE_TYPES:
                daily_expense[day] = daily_expense.get(day, 0) + float(t.amount or 0)

    # Hour-of-day and day-of-week income breakdown (last 90 days, for peak hours analysis)
    hourly_income: dict[str, float] = {}   # "00"–"23" → total income earned in that hour
    dow_income: dict[str, float] = {}      # "Monday"–"Sunday" → total income on that weekday
    dow_count: dict[str, int] = {}         # how many times each weekday occurred (for avg)
    for t in income_txns:
        hour_key = t.createdAt.strftime("%H")
        dow_key  = t.createdAt.strftime("%A")
        amt = float(t.amount or 0)
        hourly_income[hour_key] = hourly_income.get(hour_key, 0) + amt
        dow_income[dow_key]     = dow_income.get(dow_key, 0) + amt
        dow_count[dow_key]      = dow_count.get(dow_key, 0) + 1

    # Average income per occurrence of each weekday
    dow_avg_income: dict[str, float] = {
        day: round(total / dow_count.get(day, 1), 2)
        for day, total in dow_income.items()
    }

    # Expense breakdown by transaction type (raw enum)
    expense_by_type: dict[str, float] = {}
    for t in expense_txns:
        if t.createdAt >= cutoff_30d:
            key = t.type.value if t.type else "OTHER"
            expense_by_type[key] = expense_by_type.get(key, 0) + float(t.amount or 0)

    # Expense breakdown by semantic category (embeddings)
    expense_txns_30d = [
        {"description": t.description or "", "amount": float(t.amount or 0)}
        for t in expense_txns
        if t.createdAt >= cutoff_30d
    ]
    expense_by_category = categorise_transactions(expense_txns_30d)

    # Detect suspicious / large transactions (>5× average)
    avg_txn = (income_30d + expense_30d) / max(len(all_txns), 1)
    suspicious = [
        {
            "type": t.type.value,
            "amount": float(t.amount or 0),
            "description": t.description,
            "date": t.createdAt.isoformat(),
        }
        for t in all_txns[:50]
        if float(t.amount or 0) > max(avg_txn * 5, 10000)
    ]

    # Active loans
    active_loans = (
        db.query(Loan)
        .filter(Loan.userId == user_id, Loan.status == LoanStatus.ACTIVE)
        .all()
    )
    total_monthly_emi = sum(float(l.monthlyPayment or 0) for l in active_loans)
    total_outstanding = sum(float(l.outstandingAmount or 0) for l in active_loans)

    loans_summary = [
        {
            "type": l.loanType.value,
            "amount": float(l.amount or 0),
            "outstanding": float(l.outstandingAmount or 0),
            "monthly_emi": float(l.monthlyPayment or 0),
            "interest_rate": float(l.interestRate or 0),
        }
        for l in active_loans
    ]

    savings_30d = income_30d - expense_30d
    savings_rate = (savings_30d / income_30d * 100) if income_30d > 0 else 0.0
    emi_to_income = (total_monthly_emi / income_30d * 100) if income_30d > 0 else 0.0

    return {
        # Current state
        "total_balance": round(total_balance, 2),
        "num_accounts": len(accounts),
        # 30-day summary
        "income_30d": round(income_30d, 2),
        "expense_30d": round(expense_30d, 2),
        "savings_30d": round(savings_30d, 2),
        "savings_rate_pct": round(savings_rate, 1),
        "income_7d": round(income_7d, 2),
        # 90-day summary
        "income_90d": round(income_90d, 2),
        "expense_90d": round(expense_90d, 2),
        # Daily trends
        "daily_income": daily_income,
        "daily_gig_income": daily_gig_income,
        "daily_expense": daily_expense,
        # Expense breakdown
        "expense_by_type": expense_by_type,
        # Debt situation
        "active_loans_count": len(active_loans),
        "total_monthly_emi": round(total_monthly_emi, 2),
        "total_outstanding_debt": round(total_outstanding, 2),
        "emi_to_income_pct": round(emi_to_income, 1),
        "loans": loans_summary,
        # Semantic expense categories (via embeddings)
        "expense_by_category": expense_by_category,
        "embedding_mode": get_embedding_mode(),
        # Peak-hours analysis data
        "hourly_income": hourly_income,
        "dow_income": dow_income,
        "dow_avg_income": dow_avg_income,
        # Fraud signals
        "suspicious_transactions": suspicious,
        # Recent history (for conversational context)
        "recent_transactions": [
            {
                "type": t.type.value,
                "amount": float(t.amount or 0),
                "description": t.description,
                "date": t.createdAt.isoformat(),
                "is_income": t.type in INCOME_TYPES,
            }
            for t in all_txns[:30]
        ],
    }
