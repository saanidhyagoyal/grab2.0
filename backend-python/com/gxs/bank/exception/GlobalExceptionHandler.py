from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from com.gxs.bank.dto.response.ApiResponse import error
from com.gxs.bank.exception.BadRequestException import BadRequestException
from com.gxs.bank.exception.ResourceNotFoundException import ResourceNotFoundException


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ResourceNotFoundException)
    async def handle_not_found(_: Request, exc: ResourceNotFoundException) -> JSONResponse:
        return JSONResponse(status_code=404, content=error(str(exc)))

    @app.exception_handler(BadRequestException)
    async def handle_bad_request(_: Request, exc: BadRequestException) -> JSONResponse:
        return JSONResponse(status_code=400, content=error(str(exc)))

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details: dict[str, str] = {}
        for item in exc.errors():
            loc = item.get("loc", [])
            key = str(loc[-1]) if loc else "request"
            details[key] = item.get("msg", "Invalid value")
        return JSONResponse(status_code=400, content=error("Validation failed", details))

    @app.exception_handler(Exception)
    async def handle_general(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content=error(f"An unexpected error occurred: {exc}"))
