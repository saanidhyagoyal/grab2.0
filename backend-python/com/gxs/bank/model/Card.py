from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from com.gxs.bank.config.database import Base


class CardType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    PREPAID = "PREPAID"
    FLEXI = "FLEXI"


class CardNetwork(str, Enum):
    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    RUPAY = "RUPAY"


class Status(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Card(Base):
    __tablename__ = "cards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column("user_id", String(36), ForeignKey("users.id"), nullable=False)
    user = relationship("User", lazy="select")

    cardNumberLast4 = Column("card_number_last4", String(4), nullable=False)
    cardHolderName = Column("card_holder_name", String(255), nullable=True)
    cardType = Column("card_type", SQLEnum(CardType), nullable=False)
    cardNetwork = Column("card_network", SQLEnum(CardNetwork), nullable=True)
    status = Column(SQLEnum(Status), nullable=False, default=Status.PENDING)
    expiryDate = Column("expiry_date", Date, nullable=False, default=lambda: date.today().replace(year=date.today().year + 5))
    creditLimit = Column("credit_limit", Numeric(15, 2), nullable=True)
    currentBalance = Column("current_balance", Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    cashbackEarned = Column("cashback_earned", Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    dailyLimit = Column("daily_limit", Numeric(15, 2), nullable=False, default=Decimal("50000.00"))
    monthlyLimit = Column("monthly_limit", Numeric(15, 2), nullable=False, default=Decimal("500000.00"))
    isInternationalEnabled = Column("is_international_enabled", Boolean, nullable=False, default=False)
    isOnlineEnabled = Column("is_online_enabled", Boolean, nullable=False, default=True)
    isContactlessEnabled = Column("is_contactless_enabled", Boolean, nullable=False, default=True)
    appliedBy = Column("applied_by", String(36), nullable=True)
    approvedBy = Column("approved_by", String(36), nullable=True)
    approvedAt = Column("approved_at", DateTime, nullable=True)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)


Card.CardType = CardType
Card.CardNetwork = CardNetwork
Card.Status = Status
