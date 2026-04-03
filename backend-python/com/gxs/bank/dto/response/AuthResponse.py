from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthResponse:
    token: str
    type: str
    userId: str
    fullName: str
    email: str
    phone: str
    role: str
    kycStatus: str
    employeeRole: Optional[str]
    department: Optional[str]
    employeeId: Optional[str]
    onboardingStatus: Optional[str]
