from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, String
from sqlalchemy.orm import relationship

from com.gxs.bank.config.database import Base


class Type(str, Enum):
    TRANSACTION = "TRANSACTION"
    KYC = "KYC"
    CARD = "CARD"
    LOAN = "LOAN"
    PROMOTION = "PROMOTION"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column("user_id", String(36), ForeignKey("users.id"), nullable=False)
    user = relationship("User", lazy="select")

    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    type = Column(SQLEnum(Type), nullable=False)
    isRead = Column("is_read", Boolean, nullable=False, default=False)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)


Notification.Type = Type
