from com.gxs.bank.model.SavingsAccount import SavingsAccount
from com.gxs.bank.repository._base import BaseRepository


class AccountRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, SavingsAccount)

    def findByUserId(self, userId: str):
        return self.db.query(SavingsAccount).filter(SavingsAccount.userId == userId).all()

    def findByAccountNumber(self, accountNumber: str):
        return (
            self.db.query(SavingsAccount)
            .filter(SavingsAccount.accountNumber == accountNumber)
            .first()
        )

    def existsByAccountNumber(self, accountNumber: str) -> bool:
        return self.findByAccountNumber(accountNumber) is not None

    def findByUserIdAndAccountType(self, userId: str, accountType):
        return (
            self.db.query(SavingsAccount)
            .filter(SavingsAccount.userId == userId, SavingsAccount.accountType == accountType)
            .all()
        )

    def findByStatus(self, status):
        return self.db.query(SavingsAccount).filter(SavingsAccount.status == status).all()
