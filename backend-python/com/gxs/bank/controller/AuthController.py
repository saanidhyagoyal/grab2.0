from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.request.LoginRequest import LoginRequest
from com.gxs.bank.dto.request.RegisterRequest import RegisterRequest
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user
from com.gxs.bank.service.AuthService import AuthService


router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register")
def register(request: RegisterRequest, db=Depends(get_db)):
    response = AuthService(db).register(request)
    return JSONResponse(
        status_code=201,
        content=ok(asdict(response), "Registration successful"),
    )


@router.post("/login")
def login(request: LoginRequest, db=Depends(get_db)):
    response = AuthService(db).login(request)
    return ok(asdict(response), "Login successful")


@router.get("/me")
def getProfile(current_user=Depends(get_current_user), db=Depends(get_db)):
    fresh = AuthService(db).getUserById(current_user.id)
    profile = {
        "id": fresh.id,
        "userId": fresh.id,
        "fullName": fresh.fullName,
        "email": fresh.email,
        "phone": fresh.phone,
        "role": fresh.role.value,
        "employeeId": fresh.employeeId,
        "department": fresh.department,
        "kycStatus": fresh.kycStatus.value if fresh.kycStatus else "UNVERIFIED",
        "employeeRole": fresh.employeeRole.value if fresh.employeeRole else None,
        "onboardingStatus": fresh.onboardingStatus.value if fresh.onboardingStatus else None,
        "createdAt": serialize(fresh.createdAt),
        "dateOfBirth": serialize(fresh.dateOfBirth),
        "gender": fresh.gender.value if fresh.gender else None,
        "address": fresh.address,
        "city": fresh.city,
        "state": fresh.state,
        "pincode": fresh.pincode,
        "panNumber": fresh.panNumber,
        "aadhaarLast4": fresh.aadhaarLast4,
        "nomineeName": fresh.nomineeName,
        "nomineeRelation": fresh.nomineeRelation,
    }
    return ok(profile)
