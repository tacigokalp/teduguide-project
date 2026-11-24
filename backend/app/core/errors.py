"""Every error leaves the server in the same JSON shape (see docs/api-contract.md):

{"error": {"code": "NOT_FOUND", "message": "...", "details": {}}}
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException  # also covers FastAPI's HTTPException and plain 404s

CODES = {400: "VALIDATION_ERROR", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND",
         409: "CONFLICT", 429: "RATE_LIMITED"}


def error_response(status: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"error": {"code": code, "message": message, "details": details or {}}})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        return error_response(exc.status_code, CODES.get(exc.status_code, "INTERNAL_ERROR"), str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(422, "VALIDATION_ERROR", "The request is not valid.",
                              {"errors": [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]})

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        # Never show internal details to the user.
        return error_response(500, "INTERNAL_ERROR", "Something went wrong on the server.")
