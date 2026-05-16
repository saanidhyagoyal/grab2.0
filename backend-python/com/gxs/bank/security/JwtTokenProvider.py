from datetime import datetime, timedelta, timezone

import jwt

from com.gxs.bank.config.runtime import settings


class JwtTokenProvider:
    def __init__(self):
        self._secret = settings.jwt_secret
        self._expiration_ms = settings.jwt_expiration_ms

    def generateToken(self, userId: str, email: str, role: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(userId),
            "email": email,
            "role": role,
            "iat": now,
            "exp": now + timedelta(milliseconds=self._expiration_ms),
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def getUserIdFromToken(self, token: str) -> str:
        payload = jwt.decode(token, self._secret, algorithms=["HS256"])
        return str(payload.get("sub"))

    def getRoleFromToken(self, token: str) -> str:
        payload = jwt.decode(token, self._secret, algorithms=["HS256"])
        return str(payload.get("role"))

    def validateToken(self, token: str) -> bool:
        try:
            jwt.decode(token, self._secret, algorithms=["HS256"])
            return True
        except jwt.PyJWTError:
            return False
