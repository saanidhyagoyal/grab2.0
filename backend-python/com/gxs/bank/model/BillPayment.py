from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from com.gxs.bank.config.database import Base


class BillerCategory(str, Enum):
    ELECTRICITY = "ELECTRICITY"
    GAS = "GAS"
    WATER = "WATER"
    DTH = "DTH"
    BROADBAND = "BROADBAND"
    MOBILE_POSTPAID = "MOBILE_POSTPAID"
    INSURANCE_PREMIUM = "INSURANCE_PREMIUM"
    CREDIT_CARD = "CREDIT_CARD"
    MUNICIPAL_TAX = "MUNICIPAL_TAX"
    LOAN_EMI = "LOAN_EMI"


class Status(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class BillPayment(Base):
    __tablename__ = "bill_payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column("user_id", String(36), ForeignKey("users.id"), nullable=False)
    user = relationship("User", lazy="select")

    billerName = Column("biller_name", String(255), nullable=False)
    billerCategory = Column("biller_category", SQLEnum(BillerCategory), nullable=False)
    billerAccountNumber = Column("biller_account_number", String(255), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(SQLEnum(Status), nullable=False, default=Status.PENDING)
    transactionRef = Column("transaction_ref", String(255), nullable=True)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)


BillPayment.BillerCategory = BillerCategory
BillPayment.Status = Status
