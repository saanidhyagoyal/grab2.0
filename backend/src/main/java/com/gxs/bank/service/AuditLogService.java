package com.gxs.bank.service;

import com.gxs.bank.model.AuditLog;
import com.gxs.bank.repository.AuditLogRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AuditLogService {
    private final AuditLogRepository auditLogRepository;

    public void logAction(UUID performedBy, AuditLog.Action action, String entityType, UUID entityId, String details) {
        AuditLog log = AuditLog.builder()
            .performedBy(performedBy)
            .action(action)
            .targetEntityType(entityType)
            .targetEntityId(entityId)
            .details(details)
            .build();
        auditLogRepository.save(log);
    }

    public List<AuditLog> getAllLogs() {
        return auditLogRepository.findAll();
    }
}
