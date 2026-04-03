from com.gxs.bank.model.AuditLog import AuditLog
from com.gxs.bank.repository.AuditLogRepository import AuditLogRepository


class AuditLogService:
    def __init__(self, db):
        self.db = db
        self.auditLogRepository = AuditLogRepository(db)

    def logAction(self, performedBy: str, action, entityType: str, entityId: str, details: str) -> None:
        log = AuditLog(
            performedBy=performedBy,
            action=action,
            targetEntityType=entityType,
            targetEntityId=entityId,
            details=details,
        )
        self.auditLogRepository.save(log)
        self.db.commit()

    def getAllLogs(self):
        return self.auditLogRepository.findAll()
