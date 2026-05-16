from datetime import date, datetime
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, String, Text

from com.gxs.bank.config.database import Base


class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    badgeText = Column("badge_text", String(255), nullable=True)
    ctaText = Column("cta_text", String(255), nullable=True)
    ctaUrl = Column("cta_url", String(1024), nullable=True)
    termsUrl = Column("terms_url", String(1024), nullable=True)
    imageUrl = Column("image_url", String(1024), nullable=True)
    validFrom = Column("valid_from", Date, nullable=True)
    validTo = Column("valid_to", Date, nullable=True)
    isActive = Column("is_active", Boolean, nullable=False, default=True)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)
