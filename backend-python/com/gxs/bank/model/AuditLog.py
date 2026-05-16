from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, String, Text

from com.gxs.bank.config.database import Base


class Action(str, Enum):
    KYC_APPROVED = "KYC_APPROVED"
    KYC_REJECTED = "KYC_REJECTED"
    CARD_APPROVED = "CARD_APPROVED"
    CARD_REJECTED = "CARD_REJECTED"
    LOAN_APPROVED = "LOAN_APPROVED"
    LOAN_REJECTED = "LOAN_REJECTED"
    ACCOUNT_FROZEN = "ACCOUNT_FROZEN"
    ACCOUNT_UNFROZEN = "ACCOUNT_UNFROZEN"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    performedBy = Column("performed_by", String(36), nullable=False)
    action = Column(SQLEnum(Action), nullable=False)
    targetEntityType = Column("target_entity_type", String(255), nullable=False)
    targetEntityId = Column("target_entity_id", String(36), nullable=True)
    details = Column(Text, nullable=True)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)


AuditLog.Action = Action
