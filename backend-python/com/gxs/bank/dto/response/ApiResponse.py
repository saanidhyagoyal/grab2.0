from typing import Any, Optional


def ok(data: Any = None, message: Optional[str] = None) -> dict[str, Any]:
    response: dict[str, Any] = {"success": True}
    if message is not None:
        response["message"] = message
    if data is not None:
        response["data"] = data
    return response


def error(message: str, data: Any = None) -> dict[str, Any]:
    response: dict[str, Any] = {"success": False, "message": message}
    if data is not None:
        response["data"] = data
    return response
