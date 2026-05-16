from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    fullName: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    role: str = Field(..., min_length=1)
    employeeId: Optional[str] = None
    department: Optional[str] = None
    employeeRole: Optional[str] = None
