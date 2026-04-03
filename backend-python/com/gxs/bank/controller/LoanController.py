from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.request.LoanApplyRequest import LoanApplyRequest
from com.gxs.bank.dto.request.LoanRepayRequest import LoanRepayRequest
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user
from com.gxs.bank.service.LoanService import LoanService


router = APIRouter(prefix="/api/loans", tags=["Loan"])


@router.post("/apply")
def applyLoan(request: LoanApplyRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    loan = LoanService(db).applyForLoan(current_user.id, request)
    return JSONResponse(status_code=201, content=ok(serialize(loan), "Loan approved"))


@router.get("")
def getLoans(current_user=Depends(get_current_user), db=Depends(get_db)):
    loans = LoanService(db).getUserLoans(current_user.id)
    return ok(serialize(loans))


@router.get("/{loan_id}")
def getLoan(loan_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    loan = LoanService(db).getLoan(loan_id, current_user.id)
    return ok(serialize(loan))


@router.post("/{loan_id}/repay")
def repayLoan(loan_id: str, request: LoanRepayRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    loan = LoanService(db).repay(loan_id, current_user.id, request)
    return ok(serialize(loan), "Repayment processed")


@router.get("/calculate")
def calculateLoan(
    amount: Decimal = Query(...),
    rate: Decimal = Query(default=Decimal("1.08")),
    tenureMonths: int = Query(...),
    db=Depends(get_db),
):
    result = LoanService(db).calculateLoan(amount, rate, tenureMonths)
    return ok(serialize(result))
