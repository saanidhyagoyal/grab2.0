from sqlalchemy import func

from com.gxs.bank.model.Card import Card
from com.gxs.bank.repository._base import BaseRepository


class CardRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Card)

    def findByUserId(self, userId: str):
        return self.db.query(Card).filter(Card.userId == userId).all()

    def findByStatus(self, status):
        return self.db.query(Card).filter(Card.status == status).all()

    def findByUserIdAndStatus(self, userId: str, status):
        return self.db.query(Card).filter(Card.userId == userId, Card.status == status).all()

    def countByStatus(self, status):
        return int(self.db.query(func.count(Card.id)).filter(Card.status == status).scalar() or 0)
