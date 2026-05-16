from decimal import Decimal

from pydantic import BaseModel, Field


class LoanRepayRequest(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.00"))
