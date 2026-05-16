from com.gxs.bank.model.BillPayment import BillPayment
from com.gxs.bank.repository._base import BaseRepository


class BillPaymentRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, BillPayment)

    def findByUserId(self, userId: str):
        return self.db.query(BillPayment).filter(BillPayment.userId == userId).all()
