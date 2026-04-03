from com.gxs.bank.model.Promotion import Promotion
from com.gxs.bank.repository._base import BaseRepository


class PromotionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Promotion)

    def findByIsActiveTrueOrderByValidFromDesc(self):
        return (
            self.db.query(Promotion)
            .filter(Promotion.isActive.is_(True))
            .order_by(Promotion.validFrom.desc())
            .all()
        )
