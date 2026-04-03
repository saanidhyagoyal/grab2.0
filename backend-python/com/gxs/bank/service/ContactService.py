from com.gxs.bank.dto.request.ContactRequest import ContactRequest
from com.gxs.bank.model.ContactSubmission import ContactSubmission
from com.gxs.bank.repository.ContactRepository import ContactRepository


class ContactService:
    def __init__(self, db):
        self.db = db
        self.contactRepository = ContactRepository(db)

    def submit(self, request: ContactRequest):
        submission = ContactSubmission(
            name=request.name,
            email=request.email,
            subject=request.subject,
            message=request.message,
            status=ContactSubmission.Status.NEW,
        )
        self.contactRepository.save(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def getByEmail(self, email: str):
        return self.contactRepository.findByEmailOrderByCreatedAtDesc(email)

    def getAll(self):
        return self.contactRepository.findAllByOrderByCreatedAtDesc()
