from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
import random
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from com.gxs.bank.config.database import Base


class Status(str, Enum):
    ACTIVE = "ACTIVE"
    MATURED = "MATURED"
    BROKEN = "BROKEN"
    RENEWED = "RENEWED"


def _default_fd_number() -> str:
    return f"FD{random.randint(0, 999999):06d}"


def _default_maturity_date() -> date:
    return date.today() + timedelta(days=30)


class FixedDeposit(Base):
    __tablename__ = "fixed_deposits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column("user_id", String(36), ForeignKey("users.id"), nullable=False)
    user = relationship("User", lazy="select")

    sourceAccountId = Column("source_account_id", String(36), ForeignKey("savings_accounts.id"), nullable=False)
    sourceAccount = relationship("SavingsAccount", lazy="select")

    principalAmount = Column("principal_amount", Numeric(15, 2), nullable=False)
    interestRate = Column("interest_rate", Numeric(5, 2), nullable=False)
    tenureMonths = Column("tenure_months", Integer, nullable=False)
    maturityDate = Column("maturity_date", Date, nullable=False, default=_default_maturity_date)
    maturityAmount = Column("maturity_amount", Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    status = Column(SQLEnum(Status), nullable=False, default=Status.ACTIVE)
    autoRenew = Column("auto_renew", Boolean, nullable=False, default=False)
    fdNumber = Column("fd_number", String(255), unique=True, nullable=False, default=_default_fd_number)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)


FixedDeposit.Status = Status
