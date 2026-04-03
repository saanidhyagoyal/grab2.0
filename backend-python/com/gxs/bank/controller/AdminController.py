from datetime import datetime

from fastapi import APIRouter, Depends

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.model.AuditLog import AuditLog
from com.gxs.bank.model.Card import Card
from com.gxs.bank.model.Loan import Loan
from com.gxs.bank.model.User import User
from com.gxs.bank.repository.CardRepository import CardRepository
from com.gxs.bank.repository.LoanRepository import LoanRepository
from com.gxs.bank.repository.UserRepository import UserRepository
from com.gxs.bank.security.JwtAuthenticationFilter import require_employee
from com.gxs.bank.service.AuditLogService import AuditLogService


router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/pending-approvals")
def getPendingApprovals(employee=Depends(require_employee), db=Depends(get_db)):
    cardRepo = CardRepository(db)
    loanRepo = LoanRepository(db)
    userRepo = UserRepository(db)
    payload = {
        "cards": serialize(cardRepo.findByStatus(Card.Status.PENDING)),
        "loans": serialize(loanRepo.findByStatus(Loan.Status.PENDING)),
        "kyc": serialize(userRepo.findByKycStatus(User.KycStatus.PENDING_REVIEW)),
    }
    return ok(payload)


@router.get("/pending-cards")
def getPendingCards(employee=Depends(require_employee), db=Depends(get_db)):
    cards = CardRepository(db).findByStatus(Card.Status.PENDING)
    return ok(serialize(cards))


@router.get("/pending-loans")
def getPendingLoans(employee=Depends(require_employee), db=Depends(get_db)):
    loans = LoanRepository(db).findByStatus(Loan.Status.PENDING)
    return ok(serialize(loans))


@router.post("/cards/{card_id}/approve")
def approveCard(card_id: str, employee=Depends(require_employee), db=Depends(get_db)):
    cardRepo = CardRepository(db)
    card = cardRepo.findById(card_id)
    if card is None:
        raise RuntimeError("Card not found")
    card.status = Card.Status.ACTIVE
    card.approvedBy = employee.id
    card.approvedAt = datetime.utcnow()
    db.commit()
    AuditLogService(db).logAction(employee.id, AuditLog.Action.CARD_APPROVED, "CARD", card_id, "Approved card")
    return ok("Card approved")


@router.post("/cards/{card_id}/reject")
def rejectCard(card_id: str, employee=Depends(require_employee), db=Depends(get_db)):
    cardRepo = CardRepository(db)
    card = cardRepo.findById(card_id)
    if card is None:
        raise RuntimeError("Card not found")
    card.status = Card.Status.REJECTED
    card.approvedBy = employee.id
    card.approvedAt = datetime.utcnow()
    db.commit()
    AuditLogService(db).logAction(employee.id, AuditLog.Action.CARD_APPROVED, "CARD", card_id, "Rejected card")
    return ok("Card rejected")


@router.post("/loans/{loan_id}/approve")
def approveLoan(loan_id: str, employee=Depends(require_employee), db=Depends(get_db)):
    loanRepo = LoanRepository(db)
    loan = loanRepo.findById(loan_id)
    if loan is None:
        raise RuntimeError("Loan not found")
    loan.status = Loan.Status.ACTIVE
    loan.approvedBy = employee.id
    loan.approvedAt = datetime.utcnow()
    db.commit()
    AuditLogService(db).logAction(employee.id, AuditLog.Action.LOAN_APPROVED, "LOAN", loan_id, "Approved loan")
    return ok("Loan approved")


@router.post("/loans/{loan_id}/reject")
def rejectLoan(loan_id: str, employee=Depends(require_employee), db=Depends(get_db)):
    loanRepo = LoanRepository(db)
    loan = loanRepo.findById(loan_id)
    if loan is None:
        raise RuntimeError("Loan not found")
    loan.status = Loan.Status.REJECTED
    loan.approvedBy = employee.id
    loan.approvedAt = datetime.utcnow()
    db.commit()
    AuditLogService(db).logAction(employee.id, AuditLog.Action.LOAN_APPROVED, "LOAN", loan_id, "Rejected loan")
    return ok("Loan rejected")


@router.get("/audit-logs")
def getAuditLogs(employee=Depends(require_employee), db=Depends(get_db)):
    logs = AuditLogService(db).getAllLogs()
    return ok(serialize(logs))
