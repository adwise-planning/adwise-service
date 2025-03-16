import logging
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel, constr
from sqlalchemy.orm import Session

from app.config import Config
from app.models.user import User

config = Config()
logger = logging.getLogger(__name__)


class RefreshAccessTokenRequest(BaseModel):  # Keep RefreshAccessTokenRequest if needed
    refresh_token: constr(min_length=1)  # Example validation


class TokenService:
    def generate_access_token(self, user_email):
        payload = {"exp": datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRY_MINUTES),
                   "iat": datetime.utcnow(), "sub": user_email, "type": "access", }
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    def generate_refresh_token(self, user_email):
        payload = {"exp": datetime.utcnow() + timedelta(days=config.REFRESH_TOKEN_EXPIRY_DAYS),
                   "iat": datetime.utcnow(), "sub": user_email, "type": "refresh", }
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    def refresh_access_token(self, request: RefreshAccessTokenRequest,
                             db: Session):  # Use Pydantic model for validation
        refresh_token = request.refresh_token
        try:
            payload = jwt.decode(refresh_token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                logger.warning(f"TokenService: Refresh token failed: Invalid token type in refresh token")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type", )
            user_email = payload["sub"]
            user = (db.query(User).filter(User.email == user_email).first())
            if not user:
                logger.warning(f"TokenService: Refresh token failed: User not found for email: {user_email}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            access_token = self.generate_access_token(user_email)
            logger.info(f"TokenService: Access token refreshed successfully for email: {user_email}")
            return access_token
        except jwt.ExpiredSignatureError:
            logger.warning(f"TokenService: Refresh token failed: Refresh token expired")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
        except jwt.InvalidTokenError:
            logger.warning(f"TokenService: Refresh token failed: Invalid refresh token format")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        except Exception as e:
            logger.error(f"TokenService: Refresh token failed: Unexpected error: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid refresh token")


token_service = TokenService()  # Instantiate TokenService
