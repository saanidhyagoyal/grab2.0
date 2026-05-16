from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import uuid

from sqlalchemy import Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from com.gxs.bank.config.database import Base


class LoanType(str, Enum):
    PERSONAL = "PERSONAL"
    HOME = "HOME"
    VEHICLE = "VEHICLE"
    EDUCATION = "EDUCATION"
    GOLD = "GOLD"
    BUSINESS = "BUSINESS"
    BALANCE_TRANSFER = "BALANCE_TRANSFER"
    INSTALMENT = "INSTALMENT"


class Status(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAID_OFF = "PAID_OFF"
    DEFAULTED = "DEFAULTED"
    REJECTED = "REJECTED"


class Loan(Base):
    __tablename__ = "loans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column("user_id", String(36), ForeignKey("users.id"), nullable=False)
    user = relationship("User", lazy="select")

    loanType = Column("loan_type", SQLEnum(LoanType), nullable=False)
    loanName = Column("loan_name", String(255), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    outstandingAmount = Column("outstanding_amount", Numeric(15, 2), nullable=True)
    interestRate = Column("interest_rate", Numeric(5, 2), nullable=False)
    tenureMonths = Column("tenure_months", Integer, nullable=False)
    monthlyPayment = Column("monthly_payment", Numeric(15, 2), nullable=True)
    totalEmis = Column("total_emis", Integer, nullable=True)
    emisPaid = Column("emis_paid", Integer, nullable=True)
    nextEmiDate = Column("next_emi_date", Date, nullable=True)
    processingFee = Column("processing_fee", Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    purpose = Column("purpose", String(1024), nullable=True)
    appliedBy = Column("applied_by", String(36), nullable=True)
    approvedBy = Column("approved_by", String(36), nullable=True)
    approvedAt = Column("approved_at", DateTime, nullable=True)
    disbursedAccountId = Column("disbursed_account_id", String(36), nullable=True)
    status = Column(SQLEnum(Status), nullable=False, default=Status.PENDING)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)


Loan.LoanType = LoanType
Loan.Status = Status
