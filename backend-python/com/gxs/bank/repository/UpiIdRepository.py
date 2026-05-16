from com.gxs.bank.model.UpiId import UpiId
from com.gxs.bank.repository._base import BaseRepository


class UpiIdRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, UpiId)

    def findByUserId(self, userId: str):
        return self.db.query(UpiId).filter(UpiId.userId == userId).all()
