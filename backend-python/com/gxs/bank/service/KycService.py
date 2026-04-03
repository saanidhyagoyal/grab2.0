from com.gxs.bank.exception.ResourceNotFoundException import ResourceNotFoundException
from com.gxs.bank.model.KycDocument import KycDocument
from com.gxs.bank.model.Notification import Notification
from com.gxs.bank.model.User import User
from com.gxs.bank.repository.KycDocumentRepository import KycDocumentRepository
from com.gxs.bank.repository.UserRepository import UserRepository
from com.gxs.bank.service.NotificationService import NotificationService


class KycService:
    def __init__(self, db):
        self.db = db
        self.kycDocumentRepository = KycDocumentRepository(db)
        self.userRepository = UserRepository(db)
        self.notificationService = NotificationService(db)

    def submitDocument(self, userId: str, documentType, documentNumber: str, fileUrl: str):
        user = self.userRepository.findById(userId)
        if user is None:
            raise ResourceNotFoundException("User not found")

        doc = KycDocument(
            user=user,
            userId=user.id,
            documentType=documentType,
            documentNumber=documentNumber,
            fileUrl=fileUrl,
            verificationStatus=KycDocument.VerificationStatus.UPLOADED,
        )
        self.kycDocumentRepository.save(doc)

        user.kycStatus = User.KycStatus.PENDING_REVIEW
        self.notificationService.createNotification(
            user,
            "KYC Submitted",
            f"Your {documentType.value} has been submitted for review.",
            Notification.Type.KYC,
            auto_commit=False,
        )
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def getUserDocuments(self, userId: str):
        return self.kycDocumentRepository.findByUserId(userId)
