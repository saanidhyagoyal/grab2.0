from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    description: Optional[str] = None
