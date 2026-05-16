from datetime import datetime
from enum import Enum
import random
import time
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from com.gxs.bank.config.database import Base


def _default_reference() -> str:
    return f"GXS{int(time.time() * 1000)}{random.randint(0, 999)}"


class Type(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    INTEREST = "INTEREST"
    UPI_CREDIT = "UPI_CREDIT"
    UPI_DEBIT = "UPI_DEBIT"
    EMI = "EMI"
    ATM_WITHDRAWAL = "ATM_WITHDRAWAL"
    POS_PURCHASE = "POS_PURCHASE"
    BILL_PAYMENT = "BILL_PAYMENT"
    SALARY_CREDIT = "SALARY_CREDIT"
    FD_DEPOSIT = "FD_DEPOSIT"
    FD_MATURITY = "FD_MATURITY"
    GRAB_PAYOUT = "GRAB_PAYOUT"
    LOAN_MICRO_REPAYMENT = "LOAN_MICRO_REPAYMENT"


class Channel(str, Enum):
    NET_BANKING = "NET_BANKING"
    UPI = "UPI"
    MOBILE = "MOBILE"
    ATM = "ATM"
    BRANCH = "BRANCH"
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"


class TxnStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    accountId = Column("account_id", String(36), ForeignKey("savings_accounts.id"), nullable=False)
    account = relationship("SavingsAccount", lazy="select")

    type = Column(SQLEnum(Type), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(String(1000), nullable=False)
    balanceAfter = Column("balance_after", Numeric(15, 2), nullable=False)
    referenceNumber = Column("reference_number", String(255), unique=True, nullable=False, default=_default_reference)
    channel = Column(SQLEnum(Channel), nullable=False, default=Channel.NET_BANKING)
    counterpartyName = Column("counterparty_name", String(255), nullable=True)
    counterpartyAccount = Column("counterparty_account", String(255), nullable=True)
    remarks = Column(String(1024), nullable=True)
    txnStatus = Column("txn_status", SQLEnum(TxnStatus), nullable=False, default=TxnStatus.SUCCESS)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)


Transaction.Type = Type
Transaction.Channel = Channel
Transaction.TxnStatus = TxnStatus
