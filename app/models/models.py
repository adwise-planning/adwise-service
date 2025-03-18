# --- Enums ---
import logging
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, field_validator, model_validator, constr, Field
from starlette import status

logger = logging.getLogger(__name__)


class OTPDeliveryPreference(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    BOTH = "both"


# --- Request and Response Models ---
class RegisterRequest(BaseModel):
    country_code: str
    phone_number: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    otp_delivery_preference: OTPDeliveryPreference = OTPDeliveryPreference.EMAIL  # Default to email

    @field_validator("password")
    def validate_password(cls, password: str):
        password_regex = re.compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
        if not password_regex.fullmatch(password):  # Use imported regex
            raise ValueError(
                "Password must be at least 8 characters long and include uppercase, lowercase, numbers, and special characters.")
        return password


class RequestOTP(BaseModel):
    email: Optional[EmailStr] = None
    country_code: Optional[constr(min_length=2, max_length=5)] = None
    phone_number: Optional[constr(min_length=4, max_length=15)] = None

    @model_validator(mode='before')
    def check_email_or_phone(cls, values):
        email, phone_number, country_code = values.get('email'), values.get('phone_number'), values.get('country_code')
        if not email and not (phone_number and country_code):
            logger.warning(
                "Invalid request body. Either email or both phoneNumber and countryCode must be provided for OTP request.")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail={"error_code": "UNPROCESSABLE_ENTITY",
                                        "message": "Invalid request body. Either email or both phoneNumber and countryCode must be provided for OTP request."},
                                )
            # raise ValueError("Either email or both phoneNumber and countryCode must be provided for OTP request.")
        if email and (phone_number or country_code):
            logger.warning("Invalid request body. Provide either email or phoneNumber and countryCode, but not both.")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail={"error_code": "UNPROCESSABLE_ENTITY",
                                        "message": "Invalid request body. Provide either email or phoneNumber and countryCode, but not both."},
                                )
            # raise ValueError("Provide either email or phoneNumber and countryCode, but not both.")
        return values


class VerifyOTP(BaseModel):
    email: Optional[EmailStr] = None
    country_code: Optional[constr(min_length=2, max_length=5)] = None
    phone_number: Optional[constr(min_length=4, max_length=15)] = None
    otp: str

    @model_validator(mode='before')
    def check_email_or_phone(cls, values):
        email, phone_number, country_code = values.get('email'), values.get('phone_number'), values.get('country_code')

        if not email and not (phone_number and country_code):
            logger.warning(
                "Invalid request body. Either email or both phoneNumber and countryCode must be provided for OTP request.")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail={"error_code": "UNPROCESSABLE_ENTITY",
                                        "message": "Invalid request body. Either email or both phoneNumber and countryCode must be provided for OTP request."},
                                )
            # raise ValueError("Either email or both phoneNumber and countryCode must be provided for OTP verification.")
        if email and (phone_number or country_code):
            logger.warning("Invalid request body. Provide either email or phoneNumber and countryCode, but not both.")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail={"error_code": "UNPROCESSABLE_ENTITY",
                                        "message": "Invalid request body. Provide either email or phoneNumber and countryCode, but not both."},
                                )
            # raise ValueError("Provide either email or phoneNumber and countryCode, but not both.")
        return values


class RefreshToken(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None


class ComponentStatus(BaseModel):
    status: str = Field(..., description="Status of the component (ok, error, warning)")
    details: Optional[str] = Field(None,
                                   description="Optional details about the component status, especially in case of errors")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall health status (ok, degraded, critical)")
    # version: str = Field(settings.APP_VERSION, description="Application version")  # Assuming APP_VERSION in settings
    uptime: str = Field(..., description="Application uptime in human-readable format")
    timestamp: datetime = Field(datetime.now(timezone.utc), description="Timestamp of the health check")
    database: ComponentStatus = Field(..., description="Database connection status")
    redis: Optional[ComponentStatus] = Field(None, description="Redis connection status (if applicable)")
    connections: dict = Field(..., description="Statistics on application connections")
    application: dict = Field(..., description="General application statistics")


class UserStatsResponse(BaseModel):
    logged_in_users: int = Field(..., description="Number of currently logged-in users (active sessions)")
    total_active_users_last_hour: int = Field(...,
                                              description="Total users active in the last hour (login or activity)")
    inactive_users_last_30_days: int = Field(...,
                                             description="Users inactive in the last 30 days (no login or activity)")
    valid_access_tokens_count: int = Field(..., description="Total number of valid, non-expired access tokens issued")
    top_10_failed_login_users: list[dict] = Field(...,
                                                  description="Top 10 users with the highest failed login attempts")
    total_failed_login_attempts_all_users: int = Field(..., description="Total failed login attempts across all users")
    new_users_last_24_hours: int = Field(..., description="Number of new users registered in the last 24 hours")
    user_roles_distribution: dict = Field(..., description="Distribution of users across different roles")
    security_events_last_hour: int = Field(..., description="Number of security-related events in the last hour")
    average_login_time_ms: float = Field(..., description="Average login time in milliseconds")
