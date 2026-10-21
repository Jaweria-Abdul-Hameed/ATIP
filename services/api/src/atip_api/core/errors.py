"""Standardized API exceptions and error response envelope."""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorDetail(BaseModel):
    loc: list[str | int] | None = None
    msg: str
    type: str | None = None


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = Field(default=None)
    request_id: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorPayload


class APIException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: list[ErrorDetail] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class BadRequestError(APIException):
    def __init__(self, message: str = "Bad request", details: list[ErrorDetail] | None = None):
        super().__init__(
            code="BAD_REQUEST",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class NotFoundError(APIException):
    def __init__(
        self, message: str = "Resource not found", details: list[ErrorDetail] | None = None
    ):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class UnauthorizedError(APIException):
    def __init__(
        self, message: str = "Authentication required", details: list[ErrorDetail] | None = None
    ):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class SessionExpiredError(APIException):
    def __init__(
        self,
        message: str = "Session has expired. Please sign in again.",
        details: list[ErrorDetail] | None = None,
    ):
        super().__init__(
            code="SESSION_EXPIRED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class UnauthenticatedError(APIException):
    def __init__(
        self,
        message: str = "Authentication required to access this resource",
        details: list[ErrorDetail] | None = None,
    ):
        super().__init__(
            code="UNAUTHENTICATED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenError(APIException):
    def __init__(self, message: str = "Access forbidden", details: list[ErrorDetail] | None = None):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ConflictError(APIException):
    def __init__(
        self, message: str = "Resource conflict", details: list[ErrorDetail] | None = None
    ):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ValidationError(APIException):
    def __init__(
        self, message: str = "Validation failed", details: list[ErrorDetail] | None = None
    ):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details=details,
        )


class TenantMismatchError(APIException):
    def __init__(
        self,
        message: str = "Cross-tenant access prohibited",
        details: list[ErrorDetail] | None = None,
    ):
        super().__init__(
            code="TENANT_MISMATCH",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    envelope = ErrorEnvelope(
        error=ErrorPayload(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        )
    )
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    details = [
        ErrorDetail(
            loc=list(err.get("loc", [])),
            msg=err.get("msg", "Validation error"),
            type=err.get("type", "value_error"),
        )
        for err in exc.errors()
    ]
    envelope = ErrorEnvelope(
        error=ErrorPayload(
            code="VALIDATION_ERROR",
            message="Request input validation failed",
            details=details,
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=envelope.model_dump(),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        408: "TIMEOUT",
        409: "CONFLICT",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    envelope = ErrorEnvelope(
        error=ErrorPayload(
            code=code,
            message=str(exc.detail),
            request_id=request_id,
        )
    )
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    envelope = ErrorEnvelope(
        error=ErrorPayload(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred",
            request_id=request_id,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=envelope.model_dump(),
    )
