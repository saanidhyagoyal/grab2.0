from decimal import Decimal, ROUND_HALF_UP, getcontext

from com.gxs.bank.dto.request.LoanApplyRequest import LoanApplyRequest
from com.gxs.bank.dto.request.LoanRepayRequest import LoanRepayRequest
from com.gxs.bank.exception.BadRequestException import BadRequestException
from com.gxs.bank.exception.ResourceNotFoundException import ResourceNotFoundException
from com.gxs.bank.model.Loan import Loan
from com.gxs.bank.repository.LoanRepository import LoanRepository
from com.gxs.bank.repository.UserRepository import UserRepository

getcontext().prec = 28


class LoanService:
    def __init__(self, db):
        self.db = db
        self.loanRepository = LoanRepository(db)
        self.userRepository = UserRepository(db)

    def applyForLoan(self, userId: str, request: LoanApplyRequest):
        user = self.userRepository.findById(userId)
        if user is None:
            raise ResourceNotFoundException("User not found")

        try:
            loanType = Loan.LoanType(request.loanType.upper())
        except ValueError:
            raise BadRequestException(
                "Invalid loan type. Must be one of: PERSONAL, HOME, VEHICLE, EDUCATION, GOLD, BUSINESS, INSTALMENT, BALANCE_TRANSFER"
            ) from None

        interestRate = {
            Loan.LoanType.BALANCE_TRANSFER: Decimal("0.00"),
            Loan.LoanType.HOME: Decimal("8.50"),
            Loan.LoanType.VEHICLE: Decimal("7.50"),
            Loan.LoanType.EDUCATION: Decimal("5.00"),
            Loan.LoanType.GOLD: Decimal("7.00"),
            Loan.LoanType.BUSINESS: Decimal("10.00"),
        }.get(loanType, Decimal("1.08"))

        monthlyPayment = self._calculateMonthlyPayment(
            Decimal(request.amount),
            interestRate,
            int(request.tenureMonths),
        )

        loan = Loan(
            user=user,
            userId=user.id,
            loanType=loanType,
            amount=Decimal(request.amount),
            outstandingAmount=Decimal(request.amount),
            interestRate=interestRate,
            tenureMonths=int(request.tenureMonths),
            loanName=request.loanName,
            monthlyPayment=monthlyPayment,
            status=Loan.Status.PENDING,
        )

        self.loanRepository.save(loan)
        self.db.commit()
        self.db.refresh(loan)
        return loan

    def getUserLoans(self, userId: str):
        return self.loanRepository.findByUserId(userId)

    def getLoan(self, loanId: str, userId: str):
        loan = self.loanRepository.findById(loanId)
        if loan is None:
            raise ResourceNotFoundException("Loan not found")
        if loan.userId != userId:
            raise BadRequestException("Loan does not belong to user")
        return loan

    def repay(self, loanId: str, userId: str, request: LoanRepayRequest):
        loan = self.getLoan(loanId, userId)
        if loan.status == Loan.Status.PAID_OFF:
            raise BadRequestException("Loan is already paid off")

        newOutstanding = Decimal(loan.outstandingAmount) - Decimal(request.amount)
        if newOutstanding <= Decimal("0.00"):
            loan.outstandingAmount = Decimal("0.00")
            loan.status = Loan.Status.PAID_OFF
        else:
            loan.outstandingAmount = newOutstanding

        self.db.commit()
        self.db.refresh(loan)
        return loan

    def apply_rate_adjustment(self, loanId: str, userId: str, new_rate: float) -> dict:
        """
        Persist a dynamically reviewed interest rate to the loan record.
        Called after the agent confirms the weekly rate review decision.
        Recomputes monthly EMI on the remaining outstanding principal.
        """
        loan = self.getLoan(loanId, userId)
        if loan.status != Loan.Status.ACTIVE:
            raise BadRequestException("Rate adjustment only applies to active loans")

        old_rate = float(loan.interestRate)
        new_rate_dec = Decimal(str(round(new_rate, 2)))

        # Remaining months on the loan
        outstanding     = Decimal(loan.outstandingAmount or loan.amount)
        emis_paid       = int(loan.emisPaid or 0)
        total_emis      = int(loan.totalEmis or loan.tenureMonths)
        remaining_months = max(total_emis - emis_paid, 1)

        new_monthly_payment = self._calculateMonthlyPayment(outstanding, new_rate_dec, remaining_months)

        loan.interestRate   = new_rate_dec
        loan.monthlyPayment = new_monthly_payment

        self.db.commit()
        self.db.refresh(loan)

        return {
            "loan_id":             loanId,
            "old_rate_pct":        old_rate,
            "new_rate_pct":        float(new_rate_dec),
            "rate_delta_pct":      round(float(new_rate_dec) - old_rate, 2),
            "new_monthly_emi_inr": float(new_monthly_payment),
            "remaining_months":    remaining_months,
            "outstanding_inr":     float(outstanding),
            "applied":             True,
        }

    def calculateLoan(self, amount: Decimal, rate: Decimal, tenureMonths: int):
        monthlyPayment = self._calculateMonthlyPayment(amount, rate, tenureMonths)
        totalPayment = (monthlyPayment * Decimal(tenureMonths)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        totalInterest = (totalPayment - Decimal(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "loanAmount": amount,
            "interestRate": rate,
            "tenureMonths": tenureMonths,
            "monthlyPayment": monthlyPayment,
            "totalPayment": totalPayment,
            "totalInterest": totalInterest,
        }

    def _calculateMonthlyPayment(self, principal: Decimal, annualRate: Decimal, tenureMonths: int) -> Decimal:
        if annualRate == Decimal("0.00"):
            return (principal / Decimal(tenureMonths)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        monthlyRate = (annualRate / Decimal("1200")).quantize(Decimal("0.0000000001"), rounding=ROUND_HALF_UP)
        onePlusR = Decimal("1") + monthlyRate
        power = onePlusR ** tenureMonths
        numerator = principal * monthlyRate * power
        denominator = power - Decimal("1")
        return (numerator / denominator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
