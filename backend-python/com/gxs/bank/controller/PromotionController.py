from fastapi import APIRouter, Depends

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.service.PromotionService import PromotionService


router = APIRouter(prefix="/api/promotions", tags=["Promotion"])


@router.get("")
def getActivePromotions(db=Depends(get_db)):
    promotions = PromotionService(db).getActivePromotions()
    return ok(serialize(promotions))


@router.get("/{promotion_id}")
def getPromotion(promotion_id: str, db=Depends(get_db)):
    promotion = PromotionService(db).getPromotion(promotion_id)
    return ok(serialize(promotion))
