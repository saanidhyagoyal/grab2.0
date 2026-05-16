from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from com.gxs.bank.config.database import Base


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column("user_id", String(36), ForeignKey("users.id"), nullable=False)
    user = relationship("User", lazy="select")

    beneficiaryName = Column("beneficiary_name", String(255), nullable=False)
    accountNumber = Column("account_number", String(255), nullable=False)
    ifscCode = Column("ifsc_code", String(255), nullable=False)
    bankName = Column("bank_name", String(255), nullable=True)
    nickname = Column("nickname", String(255), nullable=True)
    isVerified = Column("is_verified", Boolean, nullable=False, default=False)
    maxTransferLimit = Column(
        "max_transfer_limit",
        Numeric(15, 2),
        nullable=False,
        default=Decimal("100000.00"),
    )
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)
