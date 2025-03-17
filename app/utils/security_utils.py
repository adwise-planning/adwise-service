import logging
import secrets

import bcrypt
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext  # For password hashing

from app.config import Config
from app.core.exception import AuthenticationError, InternalServerError

logger = logging.getLogger(__name__)
config = Config()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # bcrypt for password hashing
bearer_scheme = HTTPBearer()  # HTTP Bearer authentication scheme


# Generates a random salt for password hashing.
# Salts are used to protect against rainbow table attacks by making each password hash unique.
def generate_salt(length: int = config.PASSWORD_HASH_SALT_LENGTH) -> str:
    return secrets.token_hex(length)


# Hashes the provided password using a salt and the bcrypt algorithm.
# Uses passlib library with bcrypt for secure password hashing.
# Salting is implicitly handled by bcrypt, but we prepend an explicit salt for added measure and clarity.
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Verifies if the provided password matches the stored hashed password using bcrypt.
# Compares the hashed version of the provided password (using the same salt)
# with the stored hashed password.
def verify_password(stored_hashed_password: str, provided_password: str) -> bool:
    # salted_provided_password = salt.encode() + provided_password.encode()
    # return pwd_context.verify(salted_provided_password, stored_hashed_password)  # bcrypt verify
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_hashed_password.encode('utf-8'))


# Verifies a JWT access token from the Authorization header.
# Extracts the JWT token from the HTTP Bearer Authorization header, decodes it,
# and validates its signature, expiration, and token type.
async def verify_access_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    token = credentials.credentials  # Extract token string from Bearer credentials
    try:
        payload = decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])  # Decode and verify JWT
        if payload.get("type") != "access":  # Ensure token type is 'access'
            logger.warning(f"Invalid token type: {payload.get('type')}. Expected 'access'.")
            raise AuthenticationError(detail="Invalid token type",
                                      error_code="invalid_token_type")  # Use Custom Exception
        user_email = payload["sub"]  # Extract user identifier (subject) from payload
        return user_email  # Return user identifier if token is valid
    except IndexError:  # Credentials missing
        logger.warning("Authorization header is missing or empty.")
        raise AuthenticationError(detail="Token missing", error_code="missing_token")  # Use Custom Exception
    except ExpiredSignatureError:  # Token is expired
        logger.warning("Access token has expired.")
        raise AuthenticationError(detail="Token has expired", error_code="token_expired")  # Use Custom Exception
    except InvalidTokenError:  # Token is invalid (signature, format, etc.)
        logger.warning("Invalid access token format or signature.")
        raise AuthenticationError(detail="Invalid token", error_code="invalid_token")  # Use Custom Exception
    except Exception as e:  # Catch-all for unexpected errors during token verification
        logger.error(f"Unexpected error during access token verification: {e}", exc_info=True)
        raise InternalServerError(detail="Token verification failed",
                                  error_code="token_verification_error") from e  # Use InternalServerError for unexpected issues
