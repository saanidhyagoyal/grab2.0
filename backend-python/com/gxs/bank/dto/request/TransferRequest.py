from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TransferRequest(BaseModel):
    targetAccountNumber: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    description: Optional[str] = None
