package com.gxs.bank.repository;

import com.gxs.bank.model.KycDocument;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface KycDocumentRepository extends JpaRepository<KycDocument, UUID> {
    List<KycDocument> findByUserId(UUID userId);
    List<KycDocument> findByVerificationStatus(KycDocument.VerificationStatus status);
}
