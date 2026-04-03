from com.gxs.bank.exception.ResourceNotFoundException import ResourceNotFoundException
from com.gxs.bank.model.Beneficiary import Beneficiary
from com.gxs.bank.repository.BeneficiaryRepository import BeneficiaryRepository
from com.gxs.bank.repository.UserRepository import UserRepository


class BeneficiaryService:
    def __init__(self, db):
        self.db = db
        self.beneficiaryRepository = BeneficiaryRepository(db)
        self.userRepository = UserRepository(db)

    def addBeneficiary(self, userId: str, request: Beneficiary):
        user = self.userRepository.findById(userId)
        if user is None:
            raise ResourceNotFoundException("User not found")
        request.user = user
        request.userId = user.id
        self.beneficiaryRepository.save(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def getUserBeneficiaries(self, userId: str):
        return self.beneficiaryRepository.findByUserId(userId)

    def deleteBeneficiary(self, beneficiaryId: str, userId: str):
        beneficiary = self.beneficiaryRepository.findById(beneficiaryId)
        if beneficiary is None:
            raise ResourceNotFoundException("Beneficiary not found")
        if beneficiary.userId != userId:
            raise RuntimeError("Unauthorized")
        self.beneficiaryRepository.delete(beneficiary)
        self.db.commit()
