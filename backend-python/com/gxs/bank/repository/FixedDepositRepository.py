from com.gxs.bank.model.FixedDeposit import FixedDeposit
from com.gxs.bank.repository._base import BaseRepository


class FixedDepositRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, FixedDeposit)

    def findByUserId(self, userId: str):
        return self.db.query(FixedDeposit).filter(FixedDeposit.userId == userId).all()
