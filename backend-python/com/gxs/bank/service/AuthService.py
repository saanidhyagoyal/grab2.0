from dataclasses import asdict

from com.gxs.bank.config.SecurityConfig import passwordEncoder, passwordMatches
from com.gxs.bank.dto.request.LoginRequest import LoginRequest
from com.gxs.bank.dto.request.RegisterRequest import RegisterRequest
from com.gxs.bank.dto.response.AuthResponse import AuthResponse
from com.gxs.bank.exception.BadRequestException import BadRequestException
from com.gxs.bank.exception.ResourceNotFoundException import ResourceNotFoundException
from com.gxs.bank.model.User import User
from com.gxs.bank.repository.UserRepository import UserRepository
from com.gxs.bank.security.JwtTokenProvider import JwtTokenProvider


class AuthService:
    def __init__(self, db):
        self.db = db
        self.userRepository = UserRepository(db)
        self.tokenProvider = JwtTokenProvider()

    def register(self, request: RegisterRequest) -> AuthResponse:
        if self.userRepository.existsByEmail(request.email):
            raise BadRequestException("Email already registered")

        try:
            role = User.Role(request.role.upper())
        except ValueError:
            raise BadRequestException("Invalid role. Must be CUSTOMER or EMPLOYEE") from None

        employeeRole = None
        if role == User.Role.EMPLOYEE and request.employeeRole is not None:
            try:
                employeeRole = User.EmployeeRole(request.employeeRole.upper())
            except ValueError:
                raise BadRequestException("Invalid employee role. Must be MAKER, CHECKER, or ADMIN") from None

        user = User(
            fullName=request.fullName,
            email=request.email,
            phone=request.phone,
            passwordHash=passwordEncoder(request.password),
            role=role,
            employeeRole=employeeRole,
            employeeId=request.employeeId,
            department=request.department,
        )
        self.userRepository.save(user)
        self.db.commit()
        self.db.refresh(user)
        return self._buildAuthResponse(user)

    def login(self, request: LoginRequest) -> AuthResponse:
        user = self.userRepository.findByEmail(request.email)
        if user is None or not passwordMatches(request.password, user.passwordHash):
            raise BadRequestException("Invalid email or password")
        return self._buildAuthResponse(user)

    def getUserById(self, userId: str):
        user = self.userRepository.findById(userId)
        if user is None:
            raise ResourceNotFoundException("User not found")
        return user

    def _buildAuthResponse(self, user) -> AuthResponse:
        token = self.tokenProvider.generateToken(user.id, user.email, user.role.value)
        return AuthResponse(
            token=token,
            type="Bearer",
            userId=user.id,
            fullName=user.fullName,
            email=user.email,
            phone=user.phone,
            role=user.role.value,
            kycStatus=user.kycStatus.value if user.kycStatus else "UNVERIFIED",
            employeeRole=user.employeeRole.value if user.employeeRole else None,
            department=user.department,
            employeeId=user.employeeId,
            onboardingStatus=user.onboardingStatus.value if user.onboardingStatus else None,
        )

    def buildAuthResponseDict(self, user):
        return asdict(self._buildAuthResponse(user))
