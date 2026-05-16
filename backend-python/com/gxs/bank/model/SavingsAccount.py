from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from com.gxs.bank.config.database import Base


class AccountType(str, Enum):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    RECURRING_DEPOSIT = "RECURRING_DEPOSIT"


class Status(str, Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"


class SavingsAccount(Base):
    __tablename__ = "savings_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column("user_id", String(36), ForeignKey("users.id"), nullable=False)
    user = relationship("User", lazy="select")

    accountNumber = Column("account_number", String(255), nullable=False, unique=True)
    accountType = Column("account_type", SQLEnum(AccountType), nullable=False, default=AccountType.SAVINGS)
    balance = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    interestRate = Column("interest_rate", Numeric(5, 2), nullable=False)
    dailyInterestAccrued = Column("daily_interest_accrued", Numeric(15, 6), nullable=False, default=Decimal("0.000000"))
    ifscCode = Column("ifsc_code", String(11), nullable=False, default="GXSB0000001")
    branchName = Column("branch_name", String(255), nullable=False, default="GXS Digital Branch")
    micrCode = Column("micr_code", String(9), nullable=True)
    nomineeName = Column("nominee_name", String(255), nullable=True)
    dailyWithdrawalLimit = Column("daily_withdrawal_limit", Numeric(15, 2), nullable=False, default=Decimal("200000.00"))
    monthlyTransferLimit = Column("monthly_transfer_limit", Numeric(15, 2), nullable=False, default=Decimal("1000000.00"))
    isUpiEnabled = Column("is_upi_enabled", Boolean, nullable=False, default=True)
    isMobileBankingEnabled = Column("is_mobile_banking_enabled", Boolean, nullable=False, default=True)
    status = Column(SQLEnum(Status), nullable=False, default=Status.ACTIVE)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)


SavingsAccount.AccountType = AccountType
SavingsAccount.Status = Status
