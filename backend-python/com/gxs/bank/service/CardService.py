from decimal import Decimal
import random

from com.gxs.bank.dto.request.CardApplyRequest import CardApplyRequest
from com.gxs.bank.exception.BadRequestException import BadRequestException
from com.gxs.bank.exception.ResourceNotFoundException import ResourceNotFoundException
from com.gxs.bank.model.Card import Card
from com.gxs.bank.model.User import User
from com.gxs.bank.repository.CardRepository import CardRepository
from com.gxs.bank.repository.UserRepository import UserRepository


class CardService:
    def __init__(self, db):
        self.db = db
        self.cardRepository = CardRepository(db)
        self.userRepository = UserRepository(db)

    def applyForCard(self, userId: str, request: CardApplyRequest):
        user = self.userRepository.findById(userId)
        if user is None:
            raise ResourceNotFoundException("User not found")

        if user.kycStatus != User.KycStatus.VERIFIED:
            raise BadRequestException("KYC must be verified before applying for a card")

        try:
            cardType = Card.CardType(request.cardType.upper())
        except ValueError:
            raise BadRequestException("Invalid card type. Must be one of: DEBIT, CREDIT, PREPAID, FLEXI") from None

        creditLimit = {
            Card.CardType.CREDIT: Decimal("200000.00"),
            Card.CardType.FLEXI: Decimal("5000.00"),
            Card.CardType.PREPAID: Decimal("50000.00"),
        }.get(cardType, Decimal("0.00"))

        network = (
            Card.CardNetwork.MASTERCARD
            if cardType in {Card.CardType.CREDIT, Card.CardType.FLEXI}
            else Card.CardNetwork.VISA
        )

        card = Card(
            user=user,
            userId=user.id,
            cardNumberLast4=f"{random.randint(0, 9999):04d}",
            cardHolderName=user.fullName.upper(),
            cardType=cardType,
            cardNetwork=network,
            status=Card.Status.PENDING,
            creditLimit=creditLimit,
            currentBalance=Decimal("0.00"),
            cashbackEarned=Decimal("0.00"),
        )
        self.cardRepository.save(card)
        self.db.commit()
        self.db.refresh(card)
        return card

    def getUserCards(self, userId: str):
        return self.cardRepository.findByUserId(userId)

    def getCard(self, cardId: str, userId: str):
        card = self.cardRepository.findById(cardId)
        if card is None:
            raise ResourceNotFoundException("Card not found")
        if card.userId != userId:
            raise BadRequestException("Card does not belong to user")
        return card

    def toggleFreeze(self, cardId: str, userId: str):
        card = self.getCard(cardId, userId)
        if card.status == Card.Status.ACTIVE:
            card.status = Card.Status.FROZEN
        elif card.status == Card.Status.FROZEN:
            card.status = Card.Status.ACTIVE
        else:
            raise BadRequestException("Cannot toggle freeze on a cancelled card")
        self.db.commit()
        self.db.refresh(card)
        return card

    def updateSettings(self, cardId: str, userId: str, settings: dict):
        def _parse_bool(raw_value):
            if isinstance(raw_value, bool):
                return raw_value
            return str(raw_value).strip().lower() == "true"

        card = self.getCard(cardId, userId)
        if "isInternationalEnabled" in settings:
            card.isInternationalEnabled = _parse_bool(settings["isInternationalEnabled"])
        if "isOnlineEnabled" in settings:
            card.isOnlineEnabled = _parse_bool(settings["isOnlineEnabled"])
        if "isContactlessEnabled" in settings:
            card.isContactlessEnabled = _parse_bool(settings["isContactlessEnabled"])
        self.db.commit()
        self.db.refresh(card)
        return card
