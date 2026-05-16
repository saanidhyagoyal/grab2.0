from sqlalchemy import func

from com.gxs.bank.model.Loan import Loan
from com.gxs.bank.repository._base import BaseRepository


class LoanRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Loan)

    def findByUserId(self, userId: str):
        return self.db.query(Loan).filter(Loan.userId == userId).all()

    def findByStatus(self, status):
        return self.db.query(Loan).filter(Loan.status == status).all()

    def findByUserIdAndStatus(self, userId: str, status):
        return self.db.query(Loan).filter(Loan.userId == userId, Loan.status == status).all()

    def countByStatus(self, status):
        return int(self.db.query(func.count(Loan.id)).filter(Loan.status == status).scalar() or 0)
