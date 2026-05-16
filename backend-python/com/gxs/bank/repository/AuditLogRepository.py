from com.gxs.bank.model.AuditLog import AuditLog
from com.gxs.bank.repository._base import BaseRepository


class AuditLogRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, AuditLog)
