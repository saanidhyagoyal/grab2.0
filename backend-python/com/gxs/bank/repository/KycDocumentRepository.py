from com.gxs.bank.model.KycDocument import KycDocument
from com.gxs.bank.repository._base import BaseRepository


class KycDocumentRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, KycDocument)

    def findByUserId(self, userId: str):
        return self.db.query(KycDocument).filter(KycDocument.userId == userId).all()

    def findByVerificationStatus(self, status):
        return self.db.query(KycDocument).filter(KycDocument.verificationStatus == status).all()
