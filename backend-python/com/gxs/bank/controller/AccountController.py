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
    # Audit trail for deposit
    try:
        from com.gxs.bank.agents.audit_logger import log_agent_call
        log_agent_call(
            user_id=current_user.id,
            agent_name="account_service",
            intent="deposit",
            input_message=f"Deposit of {request.amount} to account {account_id}",
            output={"amount": float(request.amount), "account_id": account_id, "status": "success"},
            duration_ms=0,
            db=db,
        )
    except Exception:
        pass  # Non-critical — don't block the transaction
    return ok(serialize(txn), "Deposit successful")


@router.post("/{account_id}/withdraw")
def withdraw(account_id: str, request: WithdrawRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    txn = AccountService(db).withdraw(account_id, current_user.id, request)
    # Audit trail for withdrawal
    try:
        from com.gxs.bank.agents.audit_logger import log_agent_call
        log_agent_call(
            user_id=current_user.id,
            agent_name="account_service",
            intent="withdrawal",
            input_message=f"Withdrawal of {request.amount} from account {account_id}",
            output={"amount": float(request.amount), "account_id": account_id, "status": "success"},
            duration_ms=0,
            db=db,
        )
    except Exception:
        pass
    return ok(serialize(txn), "Withdrawal successful")


@router.post("/{account_id}/transfer")
def transfer(account_id: str, request: TransferRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    txn = AccountService(db).transfer(account_id, current_user.id, request)
    # Audit trail for transfer
    try:
        from com.gxs.bank.agents.audit_logger import log_agent_call
        log_agent_call(
            user_id=current_user.id,
            agent_name="account_service",
            intent="transfer",
            input_message=f"Transfer of {request.amount} from {account_id} to {request.targetAccountNumber}",
            output={"amount": float(request.amount), "from": account_id, "to": request.targetAccountNumber, "status": "success"},
            duration_ms=0,
            db=db,
        )
    except Exception:
        pass
    return ok(serialize(txn), "Transfer successful")


@router.post("/transactions/{txn_id}/confirm")
def confirm_held_transaction(txn_id: str, current_user=Depends(get_current_user)):
    """
    Release a CRITICAL-risk held transaction after the user has verified via OTP.
    Changes transaction status from PENDING -> SUCCESS.
    """
    from com.gxs.bank.agents.fraud_stream import release_held_transaction
    result = release_held_transaction(txn_id)
    msg = "Transaction confirmed and released" if result["released"] else "Could not release transaction"
    return ok(result, msg)


@router.get("/transactions/{txn_id}/fraud-result")
def get_transaction_fraud_result(txn_id: str, current_user=Depends(get_current_user)):
    """
    Poll the real-time fraud result for a specific transaction.
    Returns immediately with the result if available, or None if still processing.
    """
    from com.gxs.bank.agents.fraud_stream import get_txn_result
    result = get_txn_result(txn_id)
    if result:
        return ok(result, "Fraud result available")
    return ok({"txn_id": txn_id, "status": "processing", "result": None}, "Fraud check in progress")
