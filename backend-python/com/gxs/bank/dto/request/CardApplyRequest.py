from pydantic import BaseModel, Field


class CardApplyRequest(BaseModel):
    cardType: str = Field(..., min_length=1, description="Card type is required (DEBIT or FLEXI)")
