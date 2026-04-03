from sqlalchemy import func

from com.gxs.bank.model.User import User
from com.gxs.bank.repository._base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, User)

    def findByEmail(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def existsByEmail(self, email: str) -> bool:
        return self.findByEmail(email) is not None

    def findByRole(self, role):
        return self.db.query(User).filter(User.role == role).all()

    def countByRole(self, role):
        return int(self.db.query(func.count(User.id)).filter(User.role == role).scalar() or 0)

    def findByKycStatus(self, kycStatus):
        return self.db.query(User).filter(User.kycStatus == kycStatus).all()

    def findByRoleAndKycStatus(self, role, kycStatus):
        return self.db.query(User).filter(User.role == role, User.kycStatus == kycStatus).all()

    def countByKycStatus(self, kycStatus):
        return int(self.db.query(func.count(User.id)).filter(User.kycStatus == kycStatus).scalar() or 0)
