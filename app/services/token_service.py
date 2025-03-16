import logging
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.config import Config
from app.core.exception import AuthenticationError, InternalServerError

logger = logging.getLogger(__name__)
config = Config()


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY,
                             algorithms=[config.JWT_ALGORITHM])  # Decode and verify JWT
        logger.debug("Token decoded and verified successfully.")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired.")
        raise AuthenticationError(detail="Token expired", error_code="token_expired")
    except jwt.InvalidTokenError:
        logger.warning("Invalid token.")
        raise AuthenticationError(detail="Invalid token", error_code="invalid_token")
    except Exception as e:
        logger.error(f"Error decoding token: {e}", exc_info=True)
        raise AuthenticationError(detail="Invalid token", error_code="token_decode_error") from e


def generate_refresh_token(user_id: uuid.UUID) -> str:
    try:
        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_EXPIRY_DAYS),  # Expiry from config
            "iat": datetime.now(timezone.utc),
            "sub": str(user_id),  # Subject (user identifier)
            "type": "refresh",  # Token type
        }
        refresh_token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)  # Encode JWT
        logger.debug(f"Refresh token generated for user ID: {user_id}")
        return refresh_token
    except Exception as e:
        logger.error(f"Error generating refresh token for user ID: {user_id}: {e}", exc_info=True)
        raise InternalServerError(detail="Failed to generate refresh token",
                                  error_code="refresh_token_generation_error") from e


def generate_access_token(user_id: uuid.UUID) -> str:
    try:
        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRY_MINUTES),
            # Expiry from config
            "iat": datetime.now(timezone.utc),
            "sub": str(user_id),  # Subject (user identifier)
            "type": "access",  # Token type
        }
        access_token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)  # Encode JWT
        logger.debug(f"Access token generated for user ID: {user_id}")
        return access_token
    except Exception as e:
        logger.error(f"Error generating access token for user ID: {user_id}: {e}", exc_info=True)
        raise InternalServerError(detail="Failed to generate access token",
                                  error_code="access_token_generation_error") from e
