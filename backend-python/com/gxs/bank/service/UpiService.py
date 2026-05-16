from com.gxs.bank.exception.BadRequestException import BadRequestException
from com.gxs.bank.model.UpiId import UpiId
from com.gxs.bank.repository.AccountRepository import AccountRepository
from com.gxs.bank.repository.UpiIdRepository import UpiIdRepository
from com.gxs.bank.repository.UserRepository import UserRepository


class UpiService:
    def __init__(self, db):
        self.db = db
        self.upiIdRepository = UpiIdRepository(db)
        self.userRepository = UserRepository(db)
        self.accountRepository = AccountRepository(db)

    def registerUpi(self, userId: str, accountId: str, requestedId: str):
        user = self.userRepository.findById(userId)
        account = self.accountRepository.findById(accountId)
        if user is None or account is None:
            raise BadRequestException("Unauthorized")
        if account.userId != userId:
            raise BadRequestException("Unauthorized")

        upi = UpiId(
            user=user,
            userId=user.id,
            account=account,
            accountId=account.id,
            upiAddress=f"{requestedId}@gxs",
            isPrimary=True,
            isActive=True,
        )
        self.upiIdRepository.save(upi)
        self.db.commit()
        self.db.refresh(upi)
        return upi

    def getUserUpis(self, userId: str):
        return self.upiIdRepository.findByUserId(userId)
