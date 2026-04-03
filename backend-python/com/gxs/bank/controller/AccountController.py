from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.request.DepositRequest import DepositRequest
from com.gxs.bank.dto.request.TransferRequest import TransferRequest
from com.gxs.bank.dto.request.WithdrawRequest import WithdrawRequest
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user
from com.gxs.bank.service.AccountService import AccountService


router = APIRouter(prefix="/api/accounts", tags=["Account"])


@router.post("")
def createAccount(current_user=Depends(get_current_user), db=Depends(get_db)):
    account = AccountService(db).createAccount(current_user.id)
    return JSONResponse(
        status_code=201,
        content=ok(serialize(account), "Account created successfully"),
    )


@router.get("")
def getAccounts(current_user=Depends(get_current_user), db=Depends(get_db)):
    accounts = AccountService(db).getUserAccounts(current_user.id)
    return ok(serialize(accounts))


@router.get("/{account_id}")
def getAccount(account_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    account = AccountService(db).getAccount(account_id, current_user.id)
    return ok(serialize(account))


@router.get("/{account_id}/transactions")
def getTransactions(
    account_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1)] = 20,
):
    transactions = AccountService(db).getTransactions(account_id, current_user.id, page, size)
    transactions["content"] = serialize(transactions["content"])
    return ok(transactions)


@router.post("/{account_id}/deposit")
def deposit(account_id: str, request: DepositRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    txn = AccountService(db).deposit(account_id, current_user.id, request)
    return ok(serialize(txn), "Deposit successful")


@router.post("/{account_id}/withdraw")
def withdraw(account_id: str, request: WithdrawRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    txn = AccountService(db).withdraw(account_id, current_user.id, request)
    return ok(serialize(txn), "Withdrawal successful")


@router.post("/{account_id}/transfer")
def transfer(account_id: str, request: TransferRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    txn = AccountService(db).transfer(account_id, current_user.id, request)
    return ok(serialize(txn), "Transfer successful")
