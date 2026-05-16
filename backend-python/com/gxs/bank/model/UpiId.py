from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from com.gxs.bank.config.database import Base


class UpiId(Base):
    __tablename__ = "upi_ids"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column("user_id", String(36), ForeignKey("users.id"), nullable=False)
    user = relationship("User", lazy="select")

    accountId = Column("account_id", String(36), ForeignKey("savings_accounts.id"), nullable=False)
    account = relationship("SavingsAccount", lazy="select")

    upiAddress = Column("upi_address", String(255), nullable=False, unique=True)
    isPrimary = Column("is_primary", Boolean, nullable=False, default=True)
    isActive = Column("is_active", Boolean, nullable=False, default=True)
    dailyLimit = Column("daily_limit", Numeric(15, 2), nullable=False, default=Decimal("100000.00"))
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)
