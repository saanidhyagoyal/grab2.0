from fastapi import APIRouter, Depends

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.model.Beneficiary import Beneficiary
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user
from com.gxs.bank.service.BeneficiaryService import BeneficiaryService


router = APIRouter(prefix="/api/beneficiaries", tags=["Beneficiary"])


@router.post("")
def addBeneficiary(request: dict, current_user=Depends(get_current_user), db=Depends(get_db)):
    ben = Beneficiary(**request)
    saved = BeneficiaryService(db).addBeneficiary(current_user.id, ben)
    return ok(serialize(saved), "Beneficiary added successfully")


@router.get("")
def getBeneficiaries(current_user=Depends(get_current_user), db=Depends(get_db)):
    beneficiaries = BeneficiaryService(db).getUserBeneficiaries(current_user.id)
    return ok(serialize(beneficiaries))


@router.delete("/{beneficiary_id}")
def deleteBeneficiary(beneficiary_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    BeneficiaryService(db).deleteBeneficiary(beneficiary_id, current_user.id)
    return ok("Beneficiary deleted successfully")
