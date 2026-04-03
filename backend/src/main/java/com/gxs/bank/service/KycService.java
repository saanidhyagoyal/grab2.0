package com.gxs.bank.service;

import com.gxs.bank.exception.ResourceNotFoundException;
import com.gxs.bank.model.KycDocument;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.KycDocumentRepository;
import com.gxs.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class KycService {
    private final KycDocumentRepository kycDocumentRepository;
    private final UserRepository userRepository;
    private final NotificationService notificationService;

    public KycDocument submitDocument(UUID userId, KycDocument.DocumentType type, String documentNumber, String fileUrl) {
        User user = userRepository.findById(userId).orElseThrow(() -> new ResourceNotFoundException("User not found"));
        
        KycDocument doc = KycDocument.builder()
            .user(user)
            .documentType(type)
            .documentNumber(documentNumber)
            .fileUrl(fileUrl)
            .verificationStatus(KycDocument.VerificationStatus.UPLOADED)
            .build();
            
        KycDocument saved = kycDocumentRepository.save(doc);
        
        user.setKycStatus(User.KycStatus.PENDING_REVIEW);
        userRepository.save(user);
        
        notificationService.createNotification(user, "KYC Submitted", "Your " + type + " has been submitted for review.", com.gxs.bank.model.Notification.Type.KYC);
        
        return saved;
    }

    public List<KycDocument> getUserDocuments(UUID userId) {
        return kycDocumentRepository.findByUserId(userId);
    }
}
