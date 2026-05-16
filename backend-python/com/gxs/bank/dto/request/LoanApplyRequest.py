from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class LoanApplyRequest(BaseModel):
    loanType: str = Field(..., min_length=1)
    amount: Decimal = Field(..., ge=Decimal("1000"))
    tenureMonths: int = Field(..., ge=3, le=360)
    loanName: Optional[str] = None
