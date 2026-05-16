from fastapi import APIRouter, Depends

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user
from com.gxs.bank.service.NotificationService import NotificationService


router = APIRouter(prefix="/api/notifications", tags=["Notification"])


@router.get("")
def getNotifications(current_user=Depends(get_current_user), db=Depends(get_db)):
    notifications = NotificationService(db).getNotifications(current_user.id)
    return ok(serialize(notifications))


@router.get("/unread-count")
def getUnreadCount(current_user=Depends(get_current_user), db=Depends(get_db)):
    count = NotificationService(db).getUnreadCount(current_user.id)
    return ok(count)


@router.put("/{notification_id}/read")
def markAsRead(notification_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    NotificationService(db).markAsRead(notification_id)
    return ok("Marked as read")
