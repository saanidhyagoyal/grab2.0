from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.request.CardApplyRequest import CardApplyRequest
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user
from com.gxs.bank.service.CardService import CardService


router = APIRouter(prefix="/api/cards", tags=["Card"])


@router.post("/apply")
def applyForCard(request: CardApplyRequest, current_user=Depends(get_current_user), db=Depends(get_db)):
    card = CardService(db).applyForCard(current_user.id, request)
    return JSONResponse(
        status_code=201,
        content=ok(serialize(card), "Card application submitted for approval"),
    )


@router.get("")
def getCards(current_user=Depends(get_current_user), db=Depends(get_db)):
    cards = CardService(db).getUserCards(current_user.id)
    return ok(serialize(cards))


@router.get("/{card_id}")
def getCard(card_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    card = CardService(db).getCard(card_id, current_user.id)
    return ok(serialize(card))


@router.put("/{card_id}/freeze")
def toggleFreeze(card_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    card = CardService(db).toggleFreeze(card_id, current_user.id)
    return ok(serialize(card), "Card status updated")


@router.put("/{card_id}/settings")
def updateSettings(card_id: str, settings: dict, current_user=Depends(get_current_user), db=Depends(get_db)):
    card = CardService(db).updateSettings(card_id, current_user.id, settings)
    return ok(serialize(card), "Card settings updated")
