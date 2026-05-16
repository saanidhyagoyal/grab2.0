from datetime import date, datetime
from enum import Enum
import uuid

from sqlalchemy import Column, Date, DateTime, Enum as SQLEnum, String

from com.gxs.bank.config.database import Base


class Role(str, Enum):
    CUSTOMER = "CUSTOMER"
    EMPLOYEE = "EMPLOYEE"


class KycStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class EmployeeRole(str, Enum):
    MAKER = "MAKER"
    CHECKER = "CHECKER"
    ADMIN = "ADMIN"


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class OnboardingStatus(str, Enum):
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    KYC_VERIFIED = "KYC_VERIFIED"
    FULLY_ONBOARDED = "FULLY_ONBOARDED"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fullName = Column("full_name", String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(255), nullable=False)
    passwordHash = Column("password_hash", String(255), nullable=False)
    role = Column(SQLEnum(Role), nullable=False)
    employeeId = Column("employee_id", String(255), nullable=True)
    department = Column("department", String(255), nullable=True)
    kycStatus = Column("kyc_status", SQLEnum(KycStatus), nullable=False, default=KycStatus.UNVERIFIED)
    employeeRole = Column("employee_role", SQLEnum(EmployeeRole), nullable=True)
    panNumber = Column("pan_number", String(10), nullable=True)
    aadhaarLast4 = Column("aadhaar_last4", String(4), nullable=True)
    dateOfBirth = Column("date_of_birth", Date, nullable=True)
    gender = Column(SQLEnum(Gender), nullable=True)
    address = Column(String(1024), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    pincode = Column(String(6), nullable=True)
    nomineeName = Column("nominee_name", String(255), nullable=True)
    nomineeRelation = Column("nominee_relation", String(255), nullable=True)
    onboardingStatus = Column("onboarding_status", SQLEnum(OnboardingStatus), nullable=False, default=OnboardingStatus.ACCOUNT_CREATED)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)
    updatedAt = Column("updated_at", DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


User.Role = Role
User.KycStatus = KycStatus
User.EmployeeRole = EmployeeRole
User.Gender = Gender
User.OnboardingStatus = OnboardingStatus
