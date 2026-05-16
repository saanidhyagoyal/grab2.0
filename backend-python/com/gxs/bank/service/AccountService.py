from __future__ import annotations

from decimal import Decimal
import random
import time

from com.gxs.bank.dto.request.DepositRequest import DepositRequest
from com.gxs.bank.dto.request.TransferRequest import TransferRequest
from com.gxs.bank.dto.request.WithdrawRequest import WithdrawRequest
from com.gxs.bank.exception.BadRequestException import BadRequestException
from com.gxs.bank.exception.ResourceNotFoundException import ResourceNotFoundException
from com.gxs.bank.model.SavingsAccount import SavingsAccount
from com.gxs.bank.model.Transaction import Transaction
from com.gxs.bank.model.User import User
from com.gxs.bank.repository.AccountRepository import AccountRepository
from com.gxs.bank.repository.TransactionRepository import TransactionRepository
from com.gxs.bank.repository.UserRepository import UserRepository


class AccountService:
    def __init__(self, db):
        self.db = db
        self.accountRepository = AccountRepository(db)
        self.transactionRepository = TransactionRepository(db)
        self.userRepository = UserRepository(db)

    def createAccount(self, userId: str) -> SavingsAccount:
        user = self.userRepository.findById(userId)
        if user is None:
            raise ResourceNotFoundException("User not found")

        if user.kycStatus != User.KycStatus.VERIFIED:
            raise BadRequestException(
                f"KYC must be verified before opening an account. Current status: {user.kycStatus.value}"
            )

        account = SavingsAccount(
            user=user,
            userId=user.id,
            accountNumber=self._generateAccountNumber(),
            balance=Decimal("0.00"),
            interestRate=Decimal("2.08"),
            status=SavingsAccount.Status.ACTIVE,
        )
        self.accountRepository.save(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def getUserAccounts(self, userId: str):
        return self.accountRepository.findByUserId(userId)

    def getAccount(self, accountId: str, userId: str):
        account = self.accountRepository.findById(accountId)
        if account is None:
            raise ResourceNotFoundException("Account not found")
        if account.userId != userId:
            raise BadRequestException("Account does not belong to user")
        return account

    def deposit(self, accountId: str, userId: str, request: DepositRequest):
        account = self.getAccount(accountId, userId)
        amount = Decimal(request.amount)
        description = request.description if request.description is not None else "Deposit"

        # ── Micro-repayment interception for Grab payouts ─────────────────────
        repayment_info = self._try_micro_repayment(userId, float(amount), description)

        if repayment_info and repayment_info.get("should_deduct"):
            deduction = Decimal(str(repayment_info["deduction_amount"]))
            net_amount = amount - deduction

            # 1. Credit net amount to wallet
            account.balance = Decimal(account.balance) + net_amount
            net_txn = Transaction(
                account=account,
                accountId=account.id,
                type=Transaction.Type.GRAB_PAYOUT,
                amount=net_amount,
                description=f"{description} (net after {repayment_info['deduction_pct']}% micro-repayment)",
                balanceAfter=account.balance,
                channel=Transaction.Channel.NET_BANKING,
                txnStatus=Transaction.TxnStatus.SUCCESS,
            )
            self.transactionRepository.save(net_txn)

            # 2. Record micro-repayment deduction
            repay_txn = Transaction(
                account=account,
                accountId=account.id,
                type=Transaction.Type.LOAN_MICRO_REPAYMENT,
                amount=deduction,
                description=(
                    f"Auto micro-repayment ({repayment_info['deduction_pct']}% of S${float(amount):,.2f}) "
                    f"→ {repayment_info.get('band', 'BASE')} rate"
                ),
                balanceAfter=account.balance,
                channel=Transaction.Channel.NET_BANKING,
                txnStatus=Transaction.TxnStatus.SUCCESS,
            )
            self.transactionRepository.save(repay_txn)

            # 3. Actually reduce loan outstanding
            self._apply_loan_repayment(userId, float(deduction))

            # 4. Audit log
            self._log_micro_repayment(userId, float(amount), repayment_info)

            self.db.commit()
            self.db.refresh(net_txn)
            return net_txn

        # ── Standard deposit (no loan or not a Grab payout) ───────────────────
        account.balance = Decimal(account.balance) + amount
        txn = Transaction(
            account=account,
            accountId=account.id,
            type=Transaction.Type.CREDIT,
            amount=amount,
            description=description,
            balanceAfter=account.balance,
            channel=Transaction.Channel.NET_BANKING,
            txnStatus=Transaction.TxnStatus.SUCCESS,
        )
        self.transactionRepository.save(txn)
        self.db.commit()
        self.db.refresh(txn)
        return txn

    def withdraw(self, accountId: str, userId: str, request: WithdrawRequest):
        account = self.getAccount(accountId, userId)
        amount = Decimal(request.amount)
        if Decimal(account.balance) < amount:
            raise BadRequestException("Insufficient balance")

        account.balance = Decimal(account.balance) - amount
        txn = Transaction(
            account=account,
            accountId=account.id,
            type=Transaction.Type.DEBIT,
            amount=amount,
            description=request.description if request.description is not None else "Withdrawal",
            balanceAfter=account.balance,
            channel=Transaction.Channel.NET_BANKING,
            txnStatus=Transaction.TxnStatus.SUCCESS,
        )
        self.transactionRepository.save(txn)
        self.db.commit()
        self.db.refresh(txn)

        # Real-time fraud check (fire-and-forget, non-blocking)
        self._emit_fraud_event(txn.id, userId, float(amount), "DEBIT",
                               txn.description or "Withdrawal")
        return txn

    def transfer(self, accountId: str, userId: str, request: TransferRequest):
        sourceAccount = self.getAccount(accountId, userId)
        if sourceAccount.status != SavingsAccount.Status.ACTIVE:
            raise BadRequestException("Source account is not active")

        targetAccount = self.accountRepository.findByAccountNumber(request.targetAccountNumber)
        if targetAccount is None:
            raise ResourceNotFoundException("Target account not found")
        if targetAccount.status != SavingsAccount.Status.ACTIVE:
            raise BadRequestException("Target account is not active")

        amount = Decimal(request.amount)
        if Decimal(sourceAccount.balance) < amount:
            raise BadRequestException("Insufficient balance")

        sourceAccount.balance = Decimal(sourceAccount.balance) - amount
        targetAccount.balance = Decimal(targetAccount.balance) + amount

        refNumber = f"GXS{int(time.time() * 1000)}"

        outTxn = Transaction(
            account=sourceAccount,
            accountId=sourceAccount.id,
            type=Transaction.Type.TRANSFER_OUT,
            amount=amount,
            description=f"Transfer to {request.targetAccountNumber}",
            balanceAfter=sourceAccount.balance,
            referenceNumber=f"{refNumber}OUT",
            channel=Transaction.Channel.IMPS,
            counterpartyName=targetAccount.user.fullName,
            counterpartyAccount=request.targetAccountNumber,
            txnStatus=Transaction.TxnStatus.SUCCESS,
        )
        inTxn = Transaction(
            account=targetAccount,
            accountId=targetAccount.id,
            type=Transaction.Type.TRANSFER_IN,
            amount=amount,
            description=f"Transfer from {sourceAccount.accountNumber}",
            balanceAfter=targetAccount.balance,
            referenceNumber=f"{refNumber}IN",
            channel=Transaction.Channel.IMPS,
            counterpartyName=sourceAccount.user.fullName,
            counterpartyAccount=sourceAccount.accountNumber,
            txnStatus=Transaction.TxnStatus.SUCCESS,
        )

        self.transactionRepository.save(outTxn)
        self.transactionRepository.save(inTxn)
        self.db.commit()
        self.db.refresh(outTxn)

        # Real-time fraud check on outgoing transfer (fire-and-forget)
        self._emit_fraud_event(outTxn.id, userId, float(amount), "TRANSFER_OUT",
                               outTxn.description or f"Transfer to {request.targetAccountNumber}")
        return outTxn

    @staticmethod
    def _emit_fraud_event(txn_id: str, user_id: str, amount: float,
                          txn_type: str, description: str) -> None:
        """Non-blocking: enqueue transaction for real-time fraud analysis."""
        try:
            from com.gxs.bank.agents.fraud_stream import emit_transaction_event
            emit_transaction_event(txn_id, user_id, amount, txn_type, description)
        except Exception:
            pass  # Never let fraud monitoring break the transaction

    def getTransactions(self, accountId: str, userId: str, page: int, size: int):
        self.getAccount(accountId, userId)
        return self.transactionRepository.findByAccountIdOrderByCreatedAtDesc(accountId, page, size)

    def getMiniStatement(self, accountId: str, userId: str):
        self.getAccount(accountId, userId)
        return self.transactionRepository.findTop10ByAccountIdOrderByCreatedAtDesc(accountId)

    def _generateAccountNumber(self) -> str:
        while True:
            account_number = f"GXS{random.randint(0, 9999999999):010d}"
            if not self.accountRepository.existsByAccountNumber(account_number):
                return account_number

    # ── Micro-repayment helpers ───────────────────────────────────────────────

    _GRAB_KEYWORDS = {"grab", "delivery", "ride", "payout", "grabfood", "grabexpress", "grabmart"}

    def _is_grab_payout(self, description: str) -> bool:
        """Check if a deposit description looks like a Grab delivery payout."""
        lower = (description or "").lower()
        return any(kw in lower for kw in self._GRAB_KEYWORDS)

    def _try_micro_repayment(self, userId: str, amount: float, description: str) -> dict | None:
        """
        If this is a Grab payout AND the user has active loans,
        calculate the micro-repayment deduction.
        Returns None if not applicable.
        """
        if not self._is_grab_payout(description):
            return None

        try:
            from com.gxs.bank.agents.data_fetcher import get_user_financial_profile
            from com.gxs.bank.agents.repayment_agent import calculate_deduction

            profile = get_user_financial_profile(userId, self.db)

            # Quick check: any active loans?
            if profile.get("active_loans_count", 0) == 0:
                return None

            return calculate_deduction(profile, amount)
        except Exception as exc:
            print(f"[MICRO-REPAY] Error calculating deduction: {exc}", flush=True)
            return None

    def _apply_loan_repayment(self, userId: str, amount: float) -> None:
        """Apply micro-repayment to the user's primary active loan."""
        try:
            from com.gxs.bank.model.Loan import Loan, Status as LoanStatus
            loan = (
                self.db.query(Loan)
                .filter(Loan.userId == userId, Loan.status == LoanStatus.ACTIVE)
                .order_by(Loan.outstandingAmount.desc())
                .first()
            )
            if loan and loan.outstandingAmount:
                from decimal import Decimal
                repay_amt = Decimal(str(round(amount, 2)))
                new_outstanding = Decimal(loan.outstandingAmount) - repay_amt
                if new_outstanding <= Decimal("0.00"):
                    loan.outstandingAmount = Decimal("0.00")
                    loan.status = LoanStatus.PAID_OFF
                else:
                    loan.outstandingAmount = new_outstanding
        except Exception as exc:
            print(f"[MICRO-REPAY] Loan repayment error: {exc}", flush=True)

    def _log_micro_repayment(self, userId: str, payout: float, info: dict) -> None:
        """Write micro-repayment to the agent reasoning audit log."""
        try:
            from com.gxs.bank.agents.audit_logger import log_agent_call
            log_agent_call(
                user_id=userId,
                agent_name="repayment_agent",
                intent="grab_income_deduction",
                input_message=f"Grab payout S${payout:,.2f}",
                output={
                    "deduction_pct": info.get("deduction_pct", 0),
                    "deduction_amount": info.get("deduction_amount", 0),
                    "net_deposit": info.get("net_deposit", 0),
                    "band": info.get("band", ""),
                    "reason": info.get("reason", ""),
                    "gig_score": info.get("gig_score", 0),
                    "risk_level": info.get("risk_level", ""),
                    "loan_outstanding": info.get("loan_outstanding", 0),
                    "micro_repayment": True,
                },
                duration_ms=0,
                routing_chain=info.get("routing_chain", ["deposit_hook → repayment_agent"]),
                agents_called=["repayment_agent", "credit_agent"],
                graph_mode="micro_repayment",
                db=self.db,
            )
        except Exception as exc:
            print(f"[MICRO-REPAY] Audit log error: {exc}", flush=True)
