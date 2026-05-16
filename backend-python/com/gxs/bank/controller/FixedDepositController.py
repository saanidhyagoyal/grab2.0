from decimal import Decimal

from fastapi import APIRouter, Depends

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.exception.BadRequestException import BadRequestException
from com.gxs.bank.model.FixedDeposit import FixedDeposit
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user
from com.gxs.bank.service.FixedDepositService import FixedDepositService


router = APIRouter(prefix="/api/fd", tags=["FixedDeposit"])


@router.post("/create")
def createFD(payload: dict, current_user=Depends(get_current_user), db=Depends(get_db)):
    accountId = payload.get("sourceAccountId")
    if accountId is None:
        raise BadRequestException("sourceAccountId is required")

    amount_raw = payload.get("principalAmount")
    rate_raw = payload.get("interestRate")
    tenure_raw = payload.get("tenureMonths")
    auto_renew_raw = payload.get("autoRenew")

    if amount_raw is None or tenure_raw is None:
        raise BadRequestException("principalAmount and tenureMonths are required")

    fd = FixedDeposit()
    fd.principalAmount = Decimal(str(amount_raw))
    fd.tenureMonths = int(str(tenure_raw))

    if rate_raw is not None:
        fd.interestRate = Decimal(str(rate_raw))
    else:
        tenure = fd.tenureMonths
        if tenure >= 36:
            fd.interestRate = Decimal("7.25")
        elif tenure >= 24:
            fd.interestRate = Decimal("7.00")
        elif tenure >= 12:
            fd.interestRate = Decimal("6.50")
        else:
            fd.interestRate = Decimal("5.50")

    if auto_renew_raw is None:
        fd.autoRenew = False
    elif isinstance(auto_renew_raw, bool):
        fd.autoRenew = auto_renew_raw
    else:
        fd.autoRenew = str(auto_renew_raw).strip().lower() == "true"
    fd.sourceAccountId = accountId

    created = FixedDepositService(db).createFD(current_user.id, fd)
    return ok(serialize(created), "Fixed Deposit created")


@router.get("")
def getFDs(current_user=Depends(get_current_user), db=Depends(get_db)):
    fds = FixedDepositService(db).getFDs(current_user.id)
    return ok(serialize(fds))


@router.post("/{fd_id}/break")
def breakFD(fd_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    fd = FixedDepositService(db).breakFD(fd_id, current_user.id)
    return ok(serialize(fd), "Fixed Deposit broken, amount credited to account")
