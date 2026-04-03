from com.gxs.bank.model.Beneficiary import Beneficiary
from com.gxs.bank.repository._base import BaseRepository


class BeneficiaryRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Beneficiary)

    def findByUserId(self, userId: str):
        return self.db.query(Beneficiary).filter(Beneficiary.userId == userId).all()
