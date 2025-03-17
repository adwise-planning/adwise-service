import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exception import InternalServerError, BadRequestError, ConflictError, NotFoundError
from app.models.user import User  # Import User model
from app.utils.security_utils import generate_salt, hash_password

logger = logging.getLogger(__name__)


# Updates a user's last login information.
def update_user_login_info(user: User, last_login_at: datetime, db: Session):
    try:
        user.last_login_at = last_login_at
        db.add(user)
        db.commit()
        logger.debug(f"User login info updated for user ID: {user.id}, Last login at: {last_login_at}")
    except Exception as e:
        logger.error(f"Error updating user login info for user ID: {user.id}: {e}", exc_info=True)
        db.rollback()
        raise InternalServerError(detail="Failed to update user login info",
                                  error_code="user_login_update_error") from e


def create_user(user_data: dict, db: Session) -> User:
    email = user_data.get("email")
    password = user_data.get("password")

    if not email or not password:
        logger.warning("Required fields (email, password) missing for user creation.")
        raise BadRequestError(detail="Email and password are required for registration",
                              error_code="missing_fields")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        logger.warning(f"Attempt to register with existing email: {email}")
        raise ConflictError(detail="Email already registered", error_code="email_already_registered")

    try:
        salt = generate_salt()
        hashed_password_value = hash_password(password)

        new_user = User(country_code=user_data.get("country_code"), phone_number=user_data.get("phone_number"),
                        email=email, first_name=user_data.get("first_name"), last_name=user_data.get("last_name"),
                        hashed_password=hashed_password_value,
                        # Add other fields from user_data as needed, ensuring they are valid User model attributes
                        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)  # Refresh to get the generated ID
        logger.info(f"User created successfully. User ID: {new_user.id}, Email: {email}")
        return new_user
    except Exception as e:
        logger.error(f"Error creating user in database: {e}", exc_info=True)
        db.rollback()
        raise InternalServerError(detail="Failed to create user", error_code="user_creation_error") from e


def get_user_by_id(user_id: str, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.debug(f"User not found for ID: {user_id}")
        raise NotFoundError(detail="User not found", error_code="user_not_found")
    return user


def get_user_by_phone(phone_number: str, country_code: str, db: Session) -> User:
    user = db.query(User).filter(User.phone_number == phone_number, User.country_code == country_code).first()
    if not user:
        logger.debug(f"User not found for phone number: {phone_number}, country code: {country_code}")
        raise NotFoundError(detail="User not found", error_code="user_not_found")
    return user


def get_user_by_email(email: str, db: Session) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.debug(f"User not found for email: {email}")
        raise NotFoundError(detail="User not found", error_code="user_not_found")
    return user


def check_user_by_phone(phone_number: str, country_code: str, db: Session) -> User:
    return db.query(User).filter(User.phone_number == phone_number, User.country_code == country_code).first()


def check_user_by_email(email: str, db: Session) -> User:
    return db.query(User).filter(User.email == email).first()
