from com.gxs.bank.exception.ResourceNotFoundException import ResourceNotFoundException
from com.gxs.bank.repository.PromotionRepository import PromotionRepository


class PromotionService:
    def __init__(self, db):
        self.db = db
        self.promotionRepository = PromotionRepository(db)

    def getActivePromotions(self):
        return self.promotionRepository.findByIsActiveTrueOrderByValidFromDesc()

    def getPromotion(self, promotionId: str):
        promotion = self.promotionRepository.findById(promotionId)
        if promotion is None:
            raise ResourceNotFoundException("Promotion not found")
        return promotion
