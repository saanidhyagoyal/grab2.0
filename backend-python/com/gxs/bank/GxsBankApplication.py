from fastapi import FastAPI

from com.gxs.bank.config.CorsConfig import configure_cors
from com.gxs.bank.config.DataSeeder import seed_data
from com.gxs.bank.config.database import Base, SessionLocal, engine
from com.gxs.bank.controller.AccountController import router as account_router
from com.gxs.bank.controller.AdminController import router as admin_router
from com.gxs.bank.controller.AuthController import router as auth_router
from com.gxs.bank.controller.BeneficiaryController import router as beneficiary_router
from com.gxs.bank.controller.BillPaymentController import router as bill_router
from com.gxs.bank.controller.CardController import router as card_router
from com.gxs.bank.controller.ContactController import router as contact_router
from com.gxs.bank.controller.FixedDepositController import router as fd_router
from com.gxs.bank.controller.KycController import router as kyc_router
from com.gxs.bank.controller.LoanController import router as loan_router
from com.gxs.bank.controller.NotificationController import router as notification_router
from com.gxs.bank.controller.PromotionController import router as promotion_router
from com.gxs.bank.exception.GlobalExceptionHandler import register_exception_handlers

# Register model metadata.
from com.gxs.bank.model import AuditLog  # noqa: F401
from com.gxs.bank.model import Beneficiary  # noqa: F401
from com.gxs.bank.model import BillPayment  # noqa: F401
from com.gxs.bank.model import Card  # noqa: F401
from com.gxs.bank.model import ContactSubmission  # noqa: F401
from com.gxs.bank.model import FixedDeposit  # noqa: F401
from com.gxs.bank.model import KycDocument  # noqa: F401
from com.gxs.bank.model import Loan  # noqa: F401
from com.gxs.bank.model import Notification  # noqa: F401
from com.gxs.bank.model import Promotion  # noqa: F401
from com.gxs.bank.model import SavingsAccount  # noqa: F401
from com.gxs.bank.model import Transaction  # noqa: F401
from com.gxs.bank.model import UpiId  # noqa: F401
from com.gxs.bank.model import User  # noqa: F401


app = FastAPI(title="gxs-bank")
configure_cors(app)
register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(account_router)
app.include_router(card_router)
app.include_router(loan_router)
app.include_router(beneficiary_router)
app.include_router(kyc_router)
app.include_router(bill_router)
app.include_router(fd_router)
app.include_router(notification_router)
app.include_router(promotion_router)
app.include_router(contact_router)
app.include_router(admin_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


def main():
    import uvicorn

    uvicorn.run("com.gxs.bank.GxsBankApplication:app", host="0.0.0.0", port=8081, reload=False)


if __name__ == "__main__":
    main()
