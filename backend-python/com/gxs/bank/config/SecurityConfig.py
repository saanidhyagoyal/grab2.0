from passlib.context import CryptContext


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def passwordEncoder(raw_password: str) -> str:
    return password_context.hash(raw_password)


def passwordMatches(raw_password: str, encoded_password: str) -> bool:
    return password_context.verify(raw_password, encoded_password)
