import logging
import uuid
from contextvars import ContextVar

from fastapi import HTTPException
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.exception import CustomException
from app.models.models import ErrorResponse

logger = logging.getLogger(__name__)
request_id_var: ContextVar[str] = ContextVar("request_id")


class Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Add a unique request ID to the request or headers
        request_id = "some_unique_id"
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id  # Example of modifying the response
        return response


# --- Middleware ---
async def request_id_middleware(request: Request, call_next):
    """
    Middleware to generate and set a unique request ID for each incoming request.
    This ID can be used for tracing requests across logs and services.
    """
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)  # Set request ID in context variable
    logger.info(f"Request started - Request ID: {request_id}, Method: {request.method}, URL: {request.url}")
    response = await call_next(request)
    logger.info(f"Request finished - Request ID: {request_id}, Status Code: {response.status_code}")
    response.headers["X-Request-ID"] = request_id  # Optional: Add request ID to response headers
    return response


async def exception_logging_middleware(request: Request, call_next):
    """
    Middleware to log exceptions and convert CustomException to standardized ErrorResponse.
    For unhandled exceptions, it logs critical errors and returns a generic 500 response.
    """
    request_id = request_id_var.get()  # Retrieve request ID from context
    try:
        response = await call_next(request)
        return response
    except CustomException as custom_exc:
        logger.warning(
            f"Request ID: {request_id} - Custom Exception: {custom_exc.detail}, Error Code: {custom_exc.error_code}",
            exc_info=False)
        return JSONResponse(
            status_code=custom_exc.status_code,
            content=ErrorResponse(error_code=custom_exc.error_code, message=custom_exc.detail).dict()
            # Use ErrorResponse model
        )
    except HTTPException as http_exc:  # Catch standard FastAPI HTTPExceptions for logging
        logger.error(f"Request ID: {request_id} - HTTP Exception: {http_exc.detail}", exc_info=False)
        return JSONResponse(status_code=http_exc.status_code,
                            content={"error": http_exc.detail})  # Keep basic error for HTTPExceptions
    except Exception as exc:  # Catch all other exceptions
        logger.critical(f"Request ID: {request_id} - Unhandled Exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(error_code="internal_server_error", message="Internal server error").dict()
            # Use ErrorResponse model
        )
