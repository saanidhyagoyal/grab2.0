from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import random
import time

from com.gxs.bank.config.SecurityConfig import passwordEncoder
from com.gxs.bank.model.Beneficiary import Beneficiary
from com.gxs.bank.model.BillPayment import BillPayment
from com.gxs.bank.model.Card import Card
from com.gxs.bank.model.FixedDeposit import FixedDeposit
from com.gxs.bank.model.Loan import Loan
from com.gxs.bank.model.Notification import Notification
from com.gxs.bank.model.SavingsAccount import SavingsAccount
from com.gxs.bank.model.Transaction import Transaction
from com.gxs.bank.model.User import User
from com.gxs.bank.repository.AccountRepository import AccountRepository
from com.gxs.bank.repository.BeneficiaryRepository import BeneficiaryRepository
from com.gxs.bank.repository.BillPaymentRepository import BillPaymentRepository
from com.gxs.bank.repository.CardRepository import CardRepository
from com.gxs.bank.repository.FixedDepositRepository import FixedDepositRepository
from com.gxs.bank.repository.LoanRepository import LoanRepository
from com.gxs.bank.repository.NotificationRepository import NotificationRepository
from com.gxs.bank.repository.TransactionRepository import TransactionRepository
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


class DataSeeder:
    def __init__(self, db):
        self.db = db
        self.userRepository = UserRepository(db)
        self.accountRepository = AccountRepository(db)
        self.cardRepository = CardRepository(db)
        self.loanRepository = LoanRepository(db)
        self.fixedDepositRepository = FixedDepositRepository(db)
        self.transactionRepository = TransactionRepository(db)
        self.notificationRepository = NotificationRepository(db)
        self.beneficiaryRepository = BeneficiaryRepository(db)
        self.billPaymentRepository = BillPaymentRepository(db)

    def run(self):
        if self.userRepository.count() > 0:
            return

        self.createUser("Admin GXS", "admin@gxs.com", "9900000001", User.Role.EMPLOYEE, User.EmployeeRole.ADMIN, User.KycStatus.VERIFIED)
        self.createUser("Jane Maker", "maker@gxs.com", "9900000002", User.Role.EMPLOYEE, User.EmployeeRole.MAKER, User.KycStatus.VERIFIED)
        self.createUser("John Checker", "checker@gxs.com", "9900000003", User.Role.EMPLOYEE, User.EmployeeRole.CHECKER, User.KycStatus.VERIFIED)

        rahul = self.createUser("Rahul Sharma", "rahul@gxs.com", "9876543210", User.Role.CUSTOMER, None, User.KycStatus.VERIFIED)
        rahul.dateOfBirth = date(1992, 6, 15)
        rahul.gender = User.Gender.MALE
        rahul.address = "42, Jalan Bukit Merah, #08-12"
        rahul.city = "Singapore"
        rahul.state = "Central"
        rahul.pincode = "150042"
        rahul.panNumber = "ABCRS1234K"
        rahul.aadhaarLast4 = "7890"
        rahul.nomineeName = "Sneha Sharma"
        rahul.nomineeRelation = "Spouse"

        rahulAcc = self.createAccount(rahul, "100010000001", Decimal("500000.00"))
        self.createCard(rahul, "4820", Card.CardType.DEBIT, Card.CardNetwork.VISA, Card.Status.ACTIVE, None)
        self.createCard(rahul, "9234", Card.CardType.CREDIT, Card.CardNetwork.MASTERCARD, Card.Status.ACTIVE, Decimal("200000"))
        self.createLoan(rahul, Loan.LoanType.PERSONAL, Decimal("150000"), Decimal("1.08"), 24, "Home Renovation", Loan.Status.ACTIVE)
        self.createFD(rahul, rahulAcc, Decimal("100000"), Decimal("7.00"), 24, "FD100001")

        self.createTxn(rahulAcc, Transaction.Type.SALARY_CREDIT, "75000.00", "Salary Credit - TechCorp India", Transaction.Channel.NET_BANKING, "575000.00")
        self.createTxn(rahulAcc, Transaction.Type.BILL_PAYMENT, "2450.00", "Electricity Bill - BESCOM", Transaction.Channel.MOBILE, "572550.00")
        self.createTxn(rahulAcc, Transaction.Type.TRANSFER_OUT, "25000.00", "Transfer to Sneha Sharma", Transaction.Channel.NEFT, "547550.00")
        self.createTxn(rahulAcc, Transaction.Type.ATM_WITHDRAWAL, "10000.00", "ATM Withdrawal - Koramangala ATM", Transaction.Channel.ATM, "537550.00")
        self.createTxn(rahulAcc, Transaction.Type.CREDIT, "15000.00", "Refund from Amazon", Transaction.Channel.NET_BANKING, "552550.00")
        self.createTxn(rahulAcc, Transaction.Type.POS_PURCHASE, "3800.00", "Swiggy - Food Order", Transaction.Channel.MOBILE, "548750.00")
        self.createTxn(rahulAcc, Transaction.Type.TRANSFER_IN, "5000.00", "Received from Priya Patel", Transaction.Channel.IMPS, "553750.00")

        self.createBeneficiary(rahul, "Sneha Sharma", "100010000003", "GXSB0000001", "GXS Bank", "Wife")
        self.createBeneficiary(rahul, "Priya Patel", "100010000007", "GXSB0000001", "GXS Bank", "Friend")

        self.createBillPayment(rahul, "SP Group", BillPayment.BillerCategory.ELECTRICITY, "ELEC2023001", Decimal("245.80"), rahulAcc)
        self.createBillPayment(rahul, "Singapore Power Gas", BillPayment.BillerCategory.GAS, "GAS2023001", Decimal("68.50"), rahulAcc)
        self.createBillPayment(rahul, "PUB Water", BillPayment.BillerCategory.WATER, "WTR2023001", Decimal("32.10"), rahulAcc)
        self.createBillPayment(rahul, "Singtel Broadband", BillPayment.BillerCategory.BROADBAND, "BB2023001", Decimal("89.00"), rahulAcc)

        self.createNotif(rahul, "Salary Credited", "S$75,000 has been credited to your account ending 0001.", Notification.Type.TRANSACTION, False)
        self.createNotif(rahul, "Loan EMI Due", "Your Personal Loan EMI of S$6,901 is due on 5th April 2026.", Notification.Type.LOAN, False)
        self.createNotif(rahul, "KYC Verified", "Congratulations! Your KYC has been successfully verified.", Notification.Type.KYC, True)
        self.createNotif(rahul, "New Offer", "Earn 5x reward points on dining this month with your Credit Card.", Notification.Type.PROMOTION, True)
        self.createNotif(rahul, "Bill Payment Successful", "Electricity bill for S$245.80 paid successfully to SP Group.", Notification.Type.TRANSACTION, True)

        u2 = self.createUser("Arjun Mehta", "unverified@gxs.com", "9876500002", User.Role.CUSTOMER, None, User.KycStatus.UNVERIFIED)
        u2.onboardingStatus = User.OnboardingStatus.ACCOUNT_CREATED
        self.createNotif(u2, "Welcome to GXS Bank!", "Please complete your KYC to unlock all banking features.", Notification.Type.KYC, False)

        u3 = self.createUser("Sneha Sharma", "pending@gxs.com", "9876500003", User.Role.CUSTOMER, None, User.KycStatus.PENDING_REVIEW)
        u3.dateOfBirth = date(1995, 3, 22)
        u3.gender = User.Gender.FEMALE
        u3.address = "88 Bedok North Road, #05-21"
        u3.city = "Singapore"
        u3.state = "East"
        u3.pincode = "460088"
        self.createAccount(u3, "100010000003", Decimal("15000.00"))
        self.createNotif(u3, "KYC Under Review", "Your documents are being verified. This usually takes 2-3 business days.", Notification.Type.KYC, False)

        u4 = self.createUser("Vikram Singh", "rejected@gxs.com", "9876500004", User.Role.CUSTOMER, None, User.KycStatus.REJECTED)
        u4.dateOfBirth = date(1988, 11, 7)
        u4.gender = User.Gender.MALE
        self.createAccount(u4, "100010000004", Decimal("5000.00"))
        self.createNotif(u4, "KYC Rejected", "Your KYC submission was rejected. Please re-upload clear, valid documents.", Notification.Type.KYC, False)
        self.createNotif(u4, "Action Required", "Your account has limited access due to KYC failure. Please resubmit.", Notification.Type.SYSTEM, False)

        u5 = self.createUser("Kavita Nair", "loanpending@gxs.com", "9876500005", User.Role.CUSTOMER, None, User.KycStatus.VERIFIED)
        u5.dateOfBirth = date(1990, 8, 14)
        u5.gender = User.Gender.FEMALE
        u5.address = "12 Tampines Street 45, #10-08"
        u5.city = "Singapore"
        u5.state = "East"
        u5.pincode = "520012"
        u5.panNumber = "DEFKN5678L"
        u5.aadhaarLast4 = "3456"
        acc5 = self.createAccount(u5, "100010000005", Decimal("80000.00"))
        self.createCard(u5, "5511", Card.CardType.DEBIT, Card.CardNetwork.VISA, Card.Status.ACTIVE, None)
        self.createLoan(u5, Loan.LoanType.HOME, Decimal("2500000"), Decimal("8.50"), 240, "Purchase of 2BHK apartment", Loan.Status.PENDING)
        self.createTxn(acc5, Transaction.Type.SALARY_CREDIT, "60000.00", "Salary Credit", Transaction.Channel.NET_BANKING, "140000.00")
        self.createTxn(acc5, Transaction.Type.BILL_PAYMENT, "1800.00", "Broadband Bill - Airtel", Transaction.Channel.MOBILE, "138200.00")
        self.createNotif(u5, "Loan Application Received", "Your Home Loan application for S$2,500,000 is under review.", Notification.Type.LOAN, False)

        u6 = self.createUser("Rohan Gupta", "frozen@gxs.com", "9876500006", User.Role.CUSTOMER, None, User.KycStatus.VERIFIED)
        u6.dateOfBirth = date(1994, 1, 30)
        u6.gender = User.Gender.MALE
        u6.address = "55 Ang Mo Kio Avenue 3, #07-15"
        u6.city = "Singapore"
        u6.state = "Central"
        u6.pincode = "560055"
        acc6 = self.createAccount(u6, "100010000006", Decimal("25000.00"))
        self.createCard(u6, "7722", Card.CardType.DEBIT, Card.CardNetwork.VISA, Card.Status.FROZEN, None)
        self.createCard(u6, "4433", Card.CardType.CREDIT, Card.CardNetwork.MASTERCARD, Card.Status.ACTIVE, Decimal("100000"))
        self.createFD(u6, acc6, Decimal("50000"), Decimal("6.50"), 12, "FD100002")
        self.createTxn(acc6, Transaction.Type.TRANSFER_IN, "25000.00", "Received from Rahul Sharma", Transaction.Channel.IMPS, "50000.00")
        self.createNotif(u6, "Card Frozen", "Your Debit Card ending 7722 has been frozen as requested.", Notification.Type.CARD, True)

        u7 = self.createUser("Priya Patel", "new@gxs.com", "9876500007", User.Role.CUSTOMER, None, User.KycStatus.VERIFIED)
        u7.dateOfBirth = date(1997, 5, 10)
        u7.gender = User.Gender.FEMALE
        self.createAccount(u7, "100010000007", Decimal("0.00"))
        self.createNotif(u7, "Account Opened!", "Welcome to GXS Bank. Your savings account is ready to use.", Notification.Type.SYSTEM, False)

        self.db.commit()

    def createUser(self, name: str, email: str, phone: str, role, employeeRole, kyc):
        if kyc == User.KycStatus.VERIFIED:
            onboarding = User.OnboardingStatus.FULLY_ONBOARDED
        elif kyc == User.KycStatus.PENDING_REVIEW:
            onboarding = User.OnboardingStatus.KYC_SUBMITTED
        else:
            onboarding = User.OnboardingStatus.ACCOUNT_CREATED

        user = User(
            fullName=name,
            email=email,
            phone=phone,
            passwordHash=passwordEncoder("password"),
            role=role,
            employeeRole=employeeRole,
            kycStatus=kyc,
            onboardingStatus=onboarding,
        )
        self.userRepository.save(user)
        self.db.flush()
        return user

    def createAccount(self, user, accountNumber: str, balance: Decimal):
        account = SavingsAccount(
            user=user,
            userId=user.id,
            accountNumber=accountNumber,
            balance=balance,
            interestRate=Decimal("4.0"),
            dailyWithdrawalLimit=Decimal("100000"),
            monthlyTransferLimit=Decimal("1000000"),
            status=SavingsAccount.Status.ACTIVE,
            accountType=SavingsAccount.AccountType.SAVINGS,
            ifscCode="GXSB0000001",
            branchName="GXS Digital Branch",
            isUpiEnabled=True,
            isMobileBankingEnabled=True,
        )
        self.accountRepository.save(account)
        self.db.flush()
        return account

    def createCard(self, user, last4: str, cardType, network, status, creditLimit):
        card = Card(
            user=user,
            userId=user.id,
            cardNumberLast4=last4,
            cardHolderName=user.fullName.upper(),
            cardType=cardType,
            status=status,
            cardNetwork=network,
            creditLimit=creditLimit if creditLimit is not None else Decimal("0.00"),
            currentBalance=Decimal("0.00"),
            cashbackEarned=Decimal("0.00"),
            dailyLimit=Decimal("50000"),
            monthlyLimit=Decimal("500000"),
            expiryDate=date.today().replace(year=date.today().year + 5),
            isOnlineEnabled=True,
            isContactlessEnabled=True,
            isInternationalEnabled=False,
        )
        self.cardRepository.save(card)

    def createLoan(self, user, loanType, amount: Decimal, rate: Decimal, tenure: int, name: str, status):
        monthlyRate = (rate / Decimal("1200")).quantize(Decimal("0.0000000001"), rounding=ROUND_HALF_UP)
        r = float(monthlyRate)
        emi = float(amount) * r * ((1 + r) ** tenure) / (((1 + r) ** tenure) - 1)
        monthlyPayment = Decimal(str(round(emi, 2)))

        next_month = _add_months(date.today(), 1)
        next_emi_date = date(next_month.year, next_month.month, 5)

        loan = Loan(
            user=user,
            userId=user.id,
            loanType=loanType,
            loanName=name,
            amount=amount,
            outstandingAmount=amount,
            interestRate=rate,
            tenureMonths=tenure,
            monthlyPayment=monthlyPayment,
            totalEmis=tenure,
            emisPaid=2 if status == Loan.Status.ACTIVE else 0,
            nextEmiDate=next_emi_date,
            status=status,
        )
        self.loanRepository.save(loan)

    def createFD(self, user, account, principal: Decimal, rate: Decimal, tenure: int, fdNumber: str):
        interest = (principal * rate * Decimal(tenure) / Decimal("1200")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fd = FixedDeposit(
            user=user,
            userId=user.id,
            sourceAccount=account,
            sourceAccountId=account.id,
            principalAmount=principal,
            interestRate=rate,
            tenureMonths=tenure,
            maturityAmount=principal + interest,
            maturityDate=_add_months(date.today(), tenure),
            autoRenew=False,
            fdNumber=fdNumber,
            status=FixedDeposit.Status.ACTIVE,
        )
        self.fixedDepositRepository.save(fd)

    def createTxn(self, account, txnType, amount: str, description: str, channel, balanceAfter: str):
        txn = Transaction(
            account=account,
            accountId=account.id,
            type=txnType,
            amount=Decimal(amount),
            description=description,
            balanceAfter=Decimal(balanceAfter),
            referenceNumber=f"GXS{time.time_ns()}",
            channel=channel,
            txnStatus=Transaction.TxnStatus.SUCCESS,
        )
        self.transactionRepository.save(txn)

    def createNotif(self, user, title: str, message: str, notifType, isRead: bool):
        notif = Notification(
            user=user,
            userId=user.id,
            title=title,
            message=message,
            type=notifType,
            isRead=isRead,
            createdAt=datetime.utcnow() - timedelta(hours=random.randint(0, 72)),
        )
        self.notificationRepository.save(notif)

    def createBeneficiary(self, user, name: str, accountNumber: str, ifscCode: str, bankName: str, nickname: str):
        beneficiary = Beneficiary(
            user=user,
            userId=user.id,
            beneficiaryName=name,
            accountNumber=accountNumber,
            ifscCode=ifscCode,
            bankName=bankName,
            nickname=nickname,
            isVerified=True,
        )
        self.beneficiaryRepository.save(beneficiary)

    def createBillPayment(self, user, billerName: str, category, accountNumber: str, amount: Decimal, _account):
        payment = BillPayment(
            user=user,
            userId=user.id,
            billerName=billerName,
            billerCategory=category,
            billerAccountNumber=accountNumber,
            amount=amount,
            status=BillPayment.Status.SUCCESS,
            transactionRef=f"BP-GXS-{time.time_ns()}",
        )
        self.billPaymentRepository.save(payment)


def seed_data(db):
    DataSeeder(db).run()
