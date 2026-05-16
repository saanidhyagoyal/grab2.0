from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from com.gxs.bank.config.database import get_db
from com.gxs.bank.model.User import User
from com.gxs.bank.repository.UserRepository import UserRepository
from com.gxs.bank.security.JwtTokenProvider import JwtTokenProvider
from com.gxs.bank.agents.otp_lock_service import is_account_locked


bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer":
        return None
    return credentials.credentials


def get_current_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db=Depends(get_db),
) -> User:
    token = _extract_token(credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token_provider = JwtTokenProvider()
    if not token_provider.validateToken(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = token_provider.getUserIdFromToken(token)
    user = UserRepository(db).findById(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    # Check if account is locked due to high fraud risk
    if is_account_locked(user_id):
        # Allow requests to endpoints required to unlock the account
        allowed_paths = ["/api/agents/verify-otp", "/api/agents/send-otp", "/api/agents/lock-status", "/api/agents/unlock"]
        if not any(request.url.path.endswith(p) for p in allowed_paths):
            raise HTTPException(status_code=403, detail="Account is temporarily locked pending security verification. Please verify OTP.")

    return user


def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db=Depends(get_db),
) -> Optional[User]:
    token = _extract_token(credentials)
    if not token:
        return None
    token_provider = JwtTokenProvider()
    if not token_provider.validateToken(token):
        return None
    user_id = token_provider.getUserIdFromToken(token)
    return UserRepository(db).findById(user_id)


def require_employee(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != User.Role.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
