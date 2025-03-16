import logging
import re

logger = logging.getLogger(__name__)


def validate_email(email):
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")  # Pre-compile regex for performance
    is_valid = re.fullmatch(email_regex, email) is not None
    if not is_valid:
        logger.debug(f"Email validation failed for: {email}")  # Log invalid emails at DEBUG level
    return is_valid


def is_valid_email_format(email: str) -> bool:
    return validate_email(email)
