from decimal import Decimal

from fastapi import APIRouter, Depends

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.model.BillPayment import BillPayment
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user
from com.gxs.bank.service.BillPaymentService import BillPaymentService


router = APIRouter(prefix="/api/bills", tags=["BillPayment"])


@router.post("/pay")
def payBill(payload: dict, current_user=Depends(get_current_user), db=Depends(get_db)):
    request = BillPayment()
    request.billerName = payload.get("billerName")
    request.billerCategory = BillPayment.BillerCategory(payload.get("billerCategory"))
    billerAccNo = payload.get("billerAccountNumber")
    if billerAccNo is None:
        billerAccNo = payload.get("consumerNumber")
    request.billerAccountNumber = billerAccNo if billerAccNo is not None else "N/A"
    request.amount = Decimal(str(payload.get("amount")))
    accountId = payload.get("accountId")

    payment = BillPaymentService(db).payBill(current_user.id, accountId, request)
    return ok(serialize(payment), "Bill payment successful")


@router.get("/history")
def getHistory(current_user=Depends(get_current_user), db=Depends(get_db)):
    history = BillPaymentService(db).getHistory(current_user.id)
    return ok(serialize(history))


@router.get("/billers")
def getBillers():
    categories = [value.value for value in BillPayment.BillerCategory]
    return ok(categories)
