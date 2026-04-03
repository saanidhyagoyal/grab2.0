from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from com.gxs.bank.config.database import get_db
from com.gxs.bank.config.serialization import serialize
from com.gxs.bank.dto.request.ContactRequest import ContactRequest
from com.gxs.bank.dto.response.ApiResponse import ok
from com.gxs.bank.security.JwtAuthenticationFilter import get_current_user
from com.gxs.bank.service.ContactService import ContactService


router = APIRouter(prefix="/api/contact", tags=["Contact"])


@router.post("")
def submitContact(request: ContactRequest, db=Depends(get_db)):
    submission = ContactService(db).submit(request)
    return JSONResponse(
        status_code=201,
        content=ok(serialize(submission), "Message sent successfully"),
    )


@router.get("")
def getSubmissions(current_user=Depends(get_current_user), db=Depends(get_db)):
    service = ContactService(db)
    if current_user.role == current_user.Role.EMPLOYEE:
        submissions = service.getAll()
    else:
        submissions = service.getByEmail(current_user.email)
    return ok(serialize(submissions))
