from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from com.gxs.bank.exception.BadRequestException import BadRequestException
from com.gxs.bank.exception.ResourceNotFoundException import ResourceNotFoundException
from com.gxs.bank.model.FixedDeposit import FixedDeposit
from com.gxs.bank.repository.AccountRepository import AccountRepository
from com.gxs.bank.repository.FixedDepositRepository import FixedDepositRepository
from com.gxs.bank.repository.UserRepository import UserRepository


def _add_months(start_date: date, months: int) -> date:
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(
        start_date.day,
        [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1],
    )
    return date(year, month, day)


class FixedDepositService:
    def __init__(self, db):
        self.db = db
        self.fixedDepositRepository = FixedDepositRepository(db)
        self.userRepository = UserRepository(db)
        self.accountRepository = AccountRepository(db)

    def createFD(self, userId: str, request: FixedDeposit):
        user = self.userRepository.findById(userId)
        if user is None:
            raise ResourceNotFoundException("User not found")

        source = self.accountRepository.findById(request.sourceAccountId)
        if source is None:
            raise ResourceNotFoundException("Source account not found")

        if source.userId != userId:
            raise BadRequestException("Unauthorized")
        if source.balance < request.principalAmount:
            raise BadRequestException("Insufficient balance")

        source.balance = source.balance - request.principalAmount

        request.user = user
        request.userId = user.id
        request.sourceAccount = source
        request.sourceAccountId = source.id
        request.maturityDate = _add_months(date.today(), int(request.tenureMonths))

        interest = (
            Decimal(request.principalAmount)
            * Decimal(request.interestRate)
            * Decimal(request.tenureMonths)
            / Decimal("1200")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        request.maturityAmount = Decimal(request.principalAmount) + interest
        request.status = FixedDeposit.Status.ACTIVE

        self.fixedDepositRepository.save(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def getFDs(self, userId: str):
        return self.fixedDepositRepository.findByUserId(userId)

    def breakFD(self, fdId: str, userId: str):
        fd = self.fixedDepositRepository.findById(fdId)
        if fd is None:
            raise ResourceNotFoundException("Fixed Deposit not found")
        if fd.userId != userId:
            raise BadRequestException("Unauthorized")
        if fd.status != FixedDeposit.Status.ACTIVE:
            raise BadRequestException("FD is not active")

        penalty = Decimal(fd.principalAmount) * Decimal("0.01")
        refund = Decimal(fd.principalAmount) - penalty

        source = fd.sourceAccount
        source.balance = Decimal(source.balance) + refund
        fd.status = FixedDeposit.Status.BROKEN

        self.db.commit()
        self.db.refresh(fd)
        return fd
