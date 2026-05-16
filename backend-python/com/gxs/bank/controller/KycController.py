from fastapi import APIRouter, Depends

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.model.KycDocument import KycDocument
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user
from com.gxs.bank.service.KycService import KycService


router = APIRouter(prefix="/api/kyc", tags=["KYC"])


@router.post("/submit")
def submitKyc(payload: dict, current_user=Depends(get_current_user), db=Depends(get_db)):
    document_type = KycDocument.DocumentType(payload.get("documentType", "").upper())
    document_number = payload.get("documentNumber")
    file_url = payload.get("fileUrl", "dummy_url")

    doc = KycService(db).submitDocument(current_user.id, document_type, document_number, file_url)
    return ok(serialize(doc), "KYC submitted successfully")


@router.get("/documents")
def getDocuments(current_user=Depends(get_current_user), db=Depends(get_db)):
    docs = KycService(db).getUserDocuments(current_user.id)
    return ok(serialize(docs))
