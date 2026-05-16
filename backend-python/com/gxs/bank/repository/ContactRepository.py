from com.gxs.bank.model.ContactSubmission import ContactSubmission
from com.gxs.bank.repository._base import BaseRepository


class ContactRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, ContactSubmission)

    def findByEmailOrderByCreatedAtDesc(self, email: str):
        return (
            self.db.query(ContactSubmission)
            .filter(ContactSubmission.email == email)
            .order_by(ContactSubmission.createdAt.desc())
            .all()
        )

    def findAllByOrderByCreatedAtDesc(self):
        return self.db.query(ContactSubmission).order_by(ContactSubmission.createdAt.desc()).all()
