import time

from com.gxs.bank.exception.BadRequestException import BadRequestException
from com.gxs.bank.exception.ResourceNotFoundException import ResourceNotFoundException
from com.gxs.bank.repository.AccountRepository import AccountRepository
from com.gxs.bank.repository.BillPaymentRepository import BillPaymentRepository
from com.gxs.bank.repository.UserRepository import UserRepository


class BillPaymentService:
    def __init__(self, db):
        self.db = db
        self.billPaymentRepository = BillPaymentRepository(db)
        self.userRepository = UserRepository(db)
        self.accountRepository = AccountRepository(db)

    def payBill(self, userId: str, accountId: str, request):
        user = self.userRepository.findById(userId)
        if user is None:
            raise ResourceNotFoundException("User not found")

        account = self.accountRepository.findById(accountId)
        if account is None:
            raise ResourceNotFoundException("Account not found")

        if account.userId != userId:
            raise BadRequestException("Not your account")
        if account.balance < request.amount:
            raise BadRequestException("Insufficient balance")

        account.balance = account.balance - request.amount

        request.user = user
        request.userId = user.id
        request.status = request.Status.SUCCESS
        request.transactionRef = f"BP-GXS-{int(time.time() * 1000)}"
        self.billPaymentRepository.save(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def getHistory(self, userId: str):
        return self.billPaymentRepository.findByUserId(userId)
