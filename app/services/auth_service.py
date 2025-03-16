import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import Config
from app.core.exception import BadRequestError, AuthenticationError, InternalServerError, UnauthorizedError, \
    NotFoundError, ConflictError
from app.services import otp_service, user_service, token_service
from app.utils.security_utils import hash_password, verify_password

config = Config()
logger = logging.getLogger(__name__)


def verify_otp_and_login(db: Session, request_id: str, otp: str, email=None, country_code=None, phone_number=None):
    identifier = f"Email: {email}" if email else f"Phone Number: {country_code}{phone_number}"
    if not otp:
        logger.warning(f"Request ID: {request_id} - OTP verification failed for {identifier}: OTP is required")
        raise BadRequestError(detail="OTP is required", error_code="missing_otp")
    otp_entry = None
    if email:
        otp_entry = otp_service.get_otp_by_email(db=db, request_id=request_id, email=email)
    elif phone_number and country_code:
        otp_entry = otp_service.get_otp_by_phone(db=db, request_id=request_id, country_code=country_code,
                                                 phone_number=phone_number)

    if not otp_entry:
        logger.warning(
            f"Request ID: {request_id} - OTP verification failed for {identifier}: Invalid OTP request, OTP not found")
        raise BadRequestError(detail="Invalid OTP request. Please request OTP again.", error_code="invalid_otp_request")

    stored_otp_hash = otp_entry.otp_hash
    otp_expiry = otp_entry.otp_expiry

    if not stored_otp_hash or not otp_expiry:
        logger.warning(
            f"Request ID: {request_id} - OTP verification failed for {identifier}: Invalid OTP data in DB")
        raise BadRequestError(detail="Invalid OTP request. Please request OTP again.", error_code="invalid_otp_data")
    if datetime.now(timezone.utc) > otp_expiry:
        logger.warning(f"Request ID: {request_id} - OTP verification failed for {identifier}: OTP expired")
        otp_service.invalidate_otp(db=db, request_id=request_id, otp_entry=otp_entry, status="expired")
        raise AuthenticationError(detail="OTP expired. Please request OTP again.", error_code="otp_expired")
    if not verify_password(stored_otp_hash, otp):  # Verify OTP hash against provided OTP
        logger.warning(f"Request ID: {request_id} - OTP verification failed for {identifier}: Invalid OTP value")
        otp_service.increment_verification_attempts(db=db, request_id=request_id,
                                                    otp_entry=otp_entry)  # Increment failed attempts
        otp_service.invalidate_otp(db=db, request_id=request_id, otp_entry=otp_entry, status="invalid")
        raise AuthenticationError(detail="Invalid OTP", error_code="invalid_otp")

    user = None  # Fetch user after OTP verification for login
    if email:
        user = user_service.check_user_by_email(db=db, email=email)
    elif phone_number and country_code:
        user = user_service.check_user_by_phone(db=db, country_code=country_code, phone_number=phone_number)

    if not user:  # Double check user existence, should not happen but for safety
        logger.error(
            f"Request ID: {request_id} - OTP verification successful but user not found for {identifier} - potential data inconsistency")
        raise InternalServerError(detail="User not found after OTP verification",
                                  error_code="user_not_found_after_otp")

    access_token = token_service.generate_access_token(user_id=user.id)  # Use TokenService
    refresh_token = token_service.generate_refresh_token(user_id=user.id)  # Use TokenService

    user_service.update_user_login_info(user=user, last_login_at=datetime.now(timezone.utc),
                                        db=db)  # Use UserService to update login info
    otp_service.invalidate_otp(db=db, request_id=request_id, otp_entry=otp_entry, status="verified")

    logger.info(
        f"Request ID: {request_id} - OTP verification successful for {identifier}, User ID: {user.id}. Access token generated.")
    return {"access_token": access_token, "refresh_token": refresh_token}  # Return both tokens


def generate_access_token(user_id):  # Now takes user_id
    return token_service.generate_access_token(user_id=user_id)  # Delegate to TokenService


def generate_refresh_token(user_id):  # Now takes user_id
    return token_service.generate_refresh_token(user_id=user_id)  # Delegate to TokenService


def refresh_access_token(refresh_token, db: Session,
                         request_id: str = None):  # Inject database session and request_id
    logger.info(f"Request ID: {request_id} - Refresh token request initiated")
    try:
        payload = token_service.decode_token(token=refresh_token)  # Use TokenService to decode and verify token
        if payload.get("type") != "refresh":
            logger.warning(f"Request ID: {request_id} - Refresh token refresh failed: Invalid token type")
            raise UnauthorizedError(detail="Invalid token type", error_code="invalid_token_type")

        user_id = payload["sub"]  # Get user_id from token payload
        user = user_service.get_user_by_id(user_id=user_id, db=db)  # Use UserService to get user by ID

        if not user:
            logger.warning(
                f"Request ID: {request_id} - Refresh token refresh failed: User not found for user_id: {user_id}")
            raise NotFoundError(detail="User not found", error_code="user_not_found")

        access_token = token_service.generate_access_token(user_id=user.id)  # Generate new access token
        logger.info(
            f"Request ID: {request_id} - Refresh token refresh successful for user_id: {user_id}. New access token generated.")
        return access_token

    except AuthenticationError as e:  # Catch AuthenticationError from token service if token is invalid or expired
        logger.warning(
            f"Request ID: {request_id} - Refresh token refresh failed: {e.detail}, Error Code: {e.error_code}")
        raise e  # Re-raise the exception to be handled by controller
    except Exception as e:  # Catch unexpected token decode errors or user lookup errors
        logger.error(f"Request ID: {request_id} - Unexpected error during token refresh: {e}", exc_info=True)
        raise AuthenticationError(detail="Invalid refresh token", error_code="invalid_refresh_token")


def request_otp(db: Session, request_id: str = None, request_type: str = "login", email: str = None,
                country_code: str = None, phone_number: str = None):
    identifier = f"Email: {email}" if email else f"Phone Number: {country_code}{phone_number}"
    if not email and not (country_code and phone_number):
        logger.warning(
            f"Request ID: {request_id} - OTP request failed for {identifier}: Email or phone number is required")
        raise BadRequestError(detail="Email or phone number is required for OTP request",
                              error_code="missing_identifier")
    user = None
    if email:
        user = user_service.check_user_by_email(email=email, db=db)
    elif country_code and phone_number:
        user = user_service.check_user_by_phone(country_code=country_code, phone_number=phone_number, db=db)
    if not user:
        logger.warning(f"Request ID: {request_id} - OTP request failed for {identifier}: User not registered")
        raise NotFoundError(detail="User not registered", error_code="user_not_found")

    otp = otp_service.generate_otp()  # Use OTP service to generate OTP
    expiry_time = datetime.now(tz=timezone.utc) + timedelta(seconds=config.OTP_EXPIRY_SECONDS)

    otp_request_data = {  # Data for OTP request
        "user_id": user.id,
        "request_id": request_id,
        "email": email,
        "country_code": country_code,
        "phone_number": phone_number,
        "otp": otp,
        "otp_expiry": expiry_time,
        "request_type": request_type
    }
    otp_service.store_otp_in_db(otp_request_data=otp_request_data, db=db, request_id=request_id)

    if email:
        otp_service.send_otp(email=email, otp=otp, delivery_method="email", request_id=request_id)
        logger.info(f"Request ID: {request_id} - OTP requested successfully for email: {email}")
    elif phone_number and country_code:
        otp_service.send_otp(country_code=country_code, phone_number=phone_number, otp=otp, delivery_method="phone",
                             request_id=request_id)
        logger.info(f"Request ID: {request_id} - OTP requested successfully for phone number: {phone_number}")


def register_user(country_code, phone_number, email, first_name, last_name, password,
                  db: Session, request_id: str = None):  # Inject database session and request_id
    if not email or not password:
        logger.warning(f"Request ID: {request_id} - Registration attempt failed: Email and password are required")
        raise BadRequestError(detail="Email and password are required", error_code="missing_fields")

    existing_user = user_service.check_user_by_email(email=email, db=db)  # Use UserService to fetch user
    if existing_user:
        logger.warning(
            f"Request ID: {request_id} - Registration attempt failed: Email already registered - {email}")
        raise ConflictError(detail="Email already registered", error_code="email_already_registered")

    hashed_password = hash_password(password)

    user_create_data = {  # Use a dictionary for creating user, more flexible
        "country_code": country_code,
        "phone_number": phone_number,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password": hashed_password,  # Use hashed_password
    }

    new_user = user_service.create_user(user_data=user_create_data, db=db)  # Use UserService to create user
    logger.info(
        f"Request ID: {request_id} - User registered successfully: Email - {email}, User ID - {new_user.id}")
    return new_user
