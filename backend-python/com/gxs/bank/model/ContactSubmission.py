from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, String, Text

from com.gxs.bank.config.database import Base


class Status(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class ContactSubmission(Base):
    __tablename__ = "contact_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(SQLEnum(Status), nullable=False, default=Status.NEW)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)


ContactSubmission.Status = Status
