from fastapi import HTTPException
from starlette import status


class CustomException(HTTPException):
    """
    Base class for custom application exceptions.
    Inherits from HTTPException to allow FastAPI to automatically handle these exceptions
    and return appropriate HTTP responses.
    """

    def __init__(self, status_code: int, detail: str, error_code: str = None):
        self.error_code = error_code  # Optional machine-readable error code
        super().__init__(status_code=status_code, detail=detail)


class BadRequestError(CustomException):
    def __init__(self, detail="Invalid request", error_code="bad_request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, error_code=error_code)


class AuthenticationError(CustomException):
    def __init__(self, detail="Invalid credentials", error_code="authentication_failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, error_code=error_code)


class NotFoundError(CustomException):
    def __init__(self, detail="Resource not found", error_code="resource_not_found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, error_code=error_code)


class AuthorizationError(CustomException):
    def __init__(self, detail="Unauthorized access", error_code="authorization_failed"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, error_code=error_code)


class InternalServerError(CustomException):
    def __init__(self, detail="Internal server error", error_code="internal_server_error"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail, error_code=error_code)


class ConflictError(CustomException):
    def __init__(self, detail="Conflict error", error_code="conflict_error"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, error_code=error_code)


class UnauthorizedError(CustomException):
    def __init__(self, detail="Unauthorized access", error_code="unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, error_code=error_code)
