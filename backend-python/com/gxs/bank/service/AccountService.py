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
        account.balance = Decimal(account.balance) + Decimal(request.amount)

        txn = Transaction(
            account=account,
            accountId=account.id,
            type=Transaction.Type.CREDIT,
            amount=Decimal(request.amount),
            description=request.description if request.description is not None else "Deposit",
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
        return outTxn

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
