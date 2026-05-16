from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, String
from sqlalchemy.orm import relationship

from com.gxs.bank.config.database import Base


class DocumentType(str, Enum):
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    VOTER_ID = "VOTER_ID"
    DRIVING_LICENSE = "DRIVING_LICENSE"
    PASSPORT = "PASSPORT"


class VerificationStatus(str, Enum):
    UPLOADED = "UPLOADED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class KycDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column("user_id", String(36), ForeignKey("users.id"), nullable=False)
    user = relationship("User", lazy="select")

    documentType = Column("document_type", SQLEnum(DocumentType), nullable=False)
    documentNumber = Column("document_number", String(255), nullable=False)
    fileUrl = Column("file_url", String(1024), nullable=True)
    verificationStatus = Column("verification_status", SQLEnum(VerificationStatus), nullable=False, default=VerificationStatus.UPLOADED)
    verifiedBy = Column("verified_by", String(36), nullable=True)
    verifiedAt = Column("verified_at", DateTime, nullable=True)
    rejectionReason = Column("rejection_reason", String(1024), nullable=True)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)


KycDocument.DocumentType = DocumentType
KycDocument.VerificationStatus = VerificationStatus
