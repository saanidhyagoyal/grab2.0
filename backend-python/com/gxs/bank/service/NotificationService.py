from com.gxs.bank.model.Notification import Notification
from com.gxs.bank.repository.NotificationRepository import NotificationRepository


class NotificationService:
    def __init__(self, db):
        self.db = db
        self.notificationRepository = NotificationRepository(db)

    def createNotification(self, user, title: str, message: str, notificationType, auto_commit: bool = True):
        notification = Notification(
            user=user,
            userId=user.id,
            title=title,
            message=message,
            type=notificationType,
            isRead=False,
        )
        self.notificationRepository.save(notification)
        if auto_commit:
            self.db.commit()
            self.db.refresh(notification)
        return notification

    def getNotifications(self, userId: str):
        return self.notificationRepository.findByUserIdOrderByCreatedAtDesc(userId)

    def getUnreadCount(self, userId: str):
        return self.notificationRepository.countByUserIdAndIsReadFalse(userId)

    def markAsRead(self, notificationId: str):
        notification = self.notificationRepository.findById(notificationId)
        if notification is not None:
            notification.isRead = True
            self.db.commit()
