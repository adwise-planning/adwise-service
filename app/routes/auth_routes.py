import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import Config
from app.core.exception import CustomException
from app.extensions import get_db
from app.models import models
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

limiter = Limiter(key_func=get_remote_address)  # Rate limiter instance
logger = logging.getLogger(__name__)
config = Config()  # Instantiate Config once for efficiency


# --- API Endpoints ---
def generate_request_id():
    return str(uuid.uuid4())  # Generate a random UUID as the request ID


@router.post("/register", response_model=models.MessageResponse, status_code=status.HTTP_201_CREATED,
             responses={status.HTTP_400_BAD_REQUEST: {"model": models.ErrorResponse},
                        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": models.ErrorResponse}, })
# @limiter.limit(config.REGISTER_RATE_LIMIT)  # Apply rate limit to registration
async def register_user(register_request: models.RegisterRequest, db: Session = Depends(get_db), ):
    request_id = generate_request_id()
    email = register_request.email
    phone_number = register_request.phone_number
    country_code = register_request.country_code
    otp_delivery_preference = register_request.otp_delivery_preference
    logger.info(f"Request ID: {request_id} - Registration attempt for email: {email}, phone: {phone_number}")
    try:
        auth_service.register_user(phone_number=phone_number, country_code=country_code, email=email,
                                   first_name=register_request.first_name, last_name=register_request.last_name,
                                   password=register_request.password, db=db)
        if otp_delivery_preference == models.OTPDeliveryPreference.EMAIL:
            auth_service.request_otp(db=db, request_id=request_id, email=str(email))
            message = "User registered successfully. OTP sent to email for verification."
        elif otp_delivery_preference == models.OTPDeliveryPreference.PHONE:
            auth_service.request_otp(db=db, request_id=request_id, phone_number=phone_number, country_code=country_code)
            message = "User registered successfully. OTP sent to phone for verification."
        elif otp_delivery_preference == models.OTPDeliveryPreference.BOTH:
            auth_service.request_otp(email=email, phone_number=phone_number, country_code=country_code,
                                     request_id=request_id, db=db)
            message = "User registered successfully. OTPs sent to email and phone for verification."
        else:
            message = "User registered successfully. OTP verification not requested."
        logger.info(f"Request ID: {request_id} - Registration successful for email: {email}, message: {message}")
        return {"message": message}
    except CustomException as e:  # Catch custom exceptions for application logic errors
        logger.warning(
            f"Request ID: {request_id} - Registration failed for email {email}: {e.detail}, Error Code: {e.error_code}")
        raise HTTPException(status_code=e.status_code, detail={"error_code": e.error_code, "message": e.detail})
    except Exception as e:  # Catch unexpected exceptions
        logger.error(f"Request ID: {request_id} - Unexpected error during registration for email {email}: {e}",
                     exc_info=True)  # Log full exception details
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error_code": "internal_server_error",
                                    "message": "Registration failed - Internal Server Error"})


@router.post("/request_otp", response_model=models.MessageResponse, responses={
    status.HTTP_400_BAD_REQUEST: {"model": models.ErrorResponse},
    status.HTTP_429_TOO_MANY_REQUESTS: {"model": models.ErrorResponse},  # For rate limiting
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": models.ErrorResponse},
})
# @limiter.limit(config.OTP_RATE_LIMIT)  # Use config instance for rate limit
async def request_otp(request_otp_req: models.RequestOTP, db: Session = Depends(get_db)):
    """
    Requests an OTP for login/verification via email or phone.
    """
    request_id = generate_request_id()  # Generate request ID for tracing
    email = request_otp_req.email
    country_code = request_otp_req.country_code
    phone_number = request_otp_req.phone_number

    identifier = f"Email: {email}" if email else f"Phone Number: {country_code}{phone_number}"
    logger.info(f"Request ID: {request_id} - OTP request initiated for {identifier}")

    try:
        if email:
            auth_service.request_otp(db=db, request_id=request_id, email=str(email))
        elif phone_number and country_code:
            auth_service.request_otp(db=db, request_id=request_id, phone_number=phone_number, country_code=country_code)
        else:
            # Should not reach here due to Pydantic validation, but for extra safety
            logger.warning(f"Request ID: {request_id} - Invalid OTP request: Neither email nor phone number provided.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"error_code": "bad_request",
                                        "message": "Invalid OTP request. Provide email or phone number."})
        message = "OTP sent successfully. Please verify within 5 minutes."
        logger.info(f"Request ID: {request_id} - OTP sent successfully to {identifier}")
        return {"message": message}
    except CustomException as e:
        logger.warning(
            f"Request ID: {request_id} - OTP request failed for {identifier}: {e.detail}, Error Code: {e.error_code}")
        raise HTTPException(status_code=e.status_code, detail={"error_code": e.error_code, "message": e.detail})
    except Exception as e:
        logger.error(f"Request ID: {request_id} - Unexpected error during OTP request for {identifier}: {e}",
                     exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error_code": "internal_server_error",
                                    "message": "Failed to send OTP - Internal Server Error"})


@router.post("/verify_otp", response_model=models.TokenResponse, responses={
    status.HTTP_400_BAD_REQUEST: {"model": models.ErrorResponse},
    status.HTTP_401_UNAUTHORIZED: {"model": models.ErrorResponse},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": models.ErrorResponse},
})
async def verify_otp(
        verify_otp_req: models.VerifyOTP,
        db: Session = Depends(get_db),  # Inject the database session here
):
    """
    Verifies OTP for login/verification via email or phone and logs in user.
    """
    request_id = generate_request_id()  # Generate request ID for tracing
    country_code = verify_otp_req.country_code
    phone_number = verify_otp_req.phone_number
    email = verify_otp_req.email
    otp = verify_otp_req.otp

    identifier = f"Email: {email}" if email else f"Phone Number: {country_code}{phone_number}"
    logger.info(f"Request ID: {request_id} - OTP verification attempt for {identifier}")

    try:
        if email:
            tokens = auth_service.verify_otp_and_login(db=db, request_id=request_id, email=email, otp=otp)
        elif phone_number and country_code:
            tokens = auth_service.verify_otp_and_login(db=db, request_id=request_id, country_code=country_code,
                                                       phone_number=phone_number, otp=otp)
        else:
            logger.warning(
                f"Request ID: {request_id} - Invalid OTP verification request: Neither email nor phone number provided.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "bad_request",
                                                                                 "message": "Invalid OTP verification request. Provide email or phone number."}, )
        logger.info(f"Request ID: {request_id} - OTP verification successful for {identifier}")
        return tokens  # Directly return token response from service
    except CustomException as e:
        logger.warning(
            f"Request ID: {request_id} - OTP verification failed for {identifier}: {e.detail}, Error Code: {e.error_code}")
        raise HTTPException(status_code=e.status_code, detail={"error_code": e.error_code, "message": e.detail})
    except Exception as e:
        logger.error(f"Request ID: {request_id} - Unexpected error during OTP verification for {identifier}: {e}",
                     exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "internal_server_error",
                    "message": "OTP verification failed - Internal Server Error"})


@router.post("/refresh_token", response_model=models.TokenResponse, responses={
    status.HTTP_401_UNAUTHORIZED: {"model": models.ErrorResponse},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": models.ErrorResponse},
})
async def refresh_access_token(refresh_token_req: models.RefreshToken, db: Session = Depends(get_db)):
    """
    Refreshes access token using refresh token.
    """
    request_id = generate_request_id()  # Generate request ID for tracing
    logger.info(f"Request ID: {request_id} - Token refresh request initiated")
    try:
        access_token = auth_service.refresh_access_token(db=db, request_id=request_id,
                                                         refresh_token=refresh_token_req.refresh_token)
        logger.info(f"Request ID: {request_id} - Token refresh successful")
        return models.TokenResponse(access_token=access_token)
    except CustomException as e:
        logger.warning(
            f"Request ID: {request_id} - Token refresh failed due to: {e.detail}, Error Code: {e.error_code}")
        raise HTTPException(status_code=e.status_code, detail={"error_code": e.error_code, "message": e.detail})
    except Exception as e:
        logger.error(f"Request ID: {request_id} - Unexpected error during token refresh: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail={"error_code": "internal_server_error",
                                    "message": "Token refresh failed - Internal Server Error"})
