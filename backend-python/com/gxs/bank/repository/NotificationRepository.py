from sqlalchemy import func

from com.gxs.bank.model.Notification import Notification
from com.gxs.bank.repository._base import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Notification)

    def findByUserIdOrderByCreatedAtDesc(self, userId: str):
        return (
            self.db.query(Notification)
            .filter(Notification.userId == userId)
            .order_by(Notification.createdAt.desc())
            .all()
        )

    def countByUserIdAndIsReadFalse(self, userId: str):
        return int(
            self.db.query(func.count(Notification.id))
            .filter(Notification.userId == userId, Notification.isRead.is_(False))
            .scalar()
            or 0
        )
