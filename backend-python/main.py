"""
GXS Bank – FastAPI Application Entry Point
"""
import os
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from com.gxs.bank.config.database import Base, engine, SessionLocal
from com.gxs.bank.config.runtime import settings
from com.gxs.bank.config.DataSeeder import seed_data

# ── Model imports — must happen before Base.metadata.create_all() ─────────────
from com.gxs.bank.model.AgentReasoningLog import AgentReasoningLog  # noqa: F401

# ── Routers ──────────────────────────────────────────────────────────────────
from com.gxs.bank.controller.AuthController import router as auth_router
from com.gxs.bank.controller.AccountController import router as account_router
from com.gxs.bank.controller.AdminController import router as admin_router
from com.gxs.bank.controller.BeneficiaryController import router as beneficiary_router
from com.gxs.bank.controller.BillPaymentController import router as bill_router
from com.gxs.bank.controller.CardController import router as card_router
from com.gxs.bank.controller.ContactController import router as contact_router
from com.gxs.bank.controller.FixedDepositController import router as fd_router
from com.gxs.bank.controller.KycController import router as kyc_router
from com.gxs.bank.controller.LoanController import router as loan_router
from com.gxs.bank.controller.NotificationController import router as notification_router
from com.gxs.bank.controller.PromotionController import router as promotion_router
from com.gxs.bank.controller.AgentController import router as agent_router

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GXS Bank API",
    description="GXS Bank backend with AI agents for Grab drivers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(account_router)
app.include_router(admin_router)
app.include_router(beneficiary_router)
app.include_router(bill_router)
app.include_router(card_router)
app.include_router(contact_router)
app.include_router(fd_router)
app.include_router(kyc_router)
app.include_router(loan_router)
app.include_router(notification_router)
app.include_router(promotion_router)
app.include_router(agent_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from com.gxs.bank.agents.audit_logger import clear_logs
        clear_logs(db)
        seed_data(db)
        print("[OK] Database initialised and seeded.")
        # Log active LLM provider for transparency
        try:
            from com.gxs.bank.agents.llm_config import get_active_provider
            print(f"[LLM] Active provider: {get_active_provider()}")
        except Exception:
            pass
        try:
            from com.gxs.bank.agents.fraud_stream import start_worker
            start_worker()
        except Exception:
            pass
    finally:
        db.close()


@app.on_event("shutdown")
def on_shutdown():
    try:
        from com.gxs.bank.agents.fraud_stream import shutdown_worker
        shutdown_worker()
    except Exception:
        pass


@app.get("/")
def root():
    return {"status": "ok", "message": "GXS Bank API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    reload_enabled = os.getenv("APP_RELOAD", "false").strip().lower() in {"1", "true", "yes", "on"}
    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=reload_enabled)
