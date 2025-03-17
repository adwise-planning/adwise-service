import os
import secrets
from typing import Optional, Literal


class Config:
    def __init__(self):
        self.PORT = os.getenv('PORT', 10000)  # Default to '8000' if the environment variable is not set
        self.HOST = os.getenv('HOST', '0.0.0.0')  # Default to '127.0.0.1' if the environment variable is not set

    """
    Configuration class for the application.

    Loads configuration from environment variables with sensible defaults.
    Ensures type conversion and provides easy access to configuration settings.

    For local development, you can set environment variables directly or use a `.env` file.
    For production, environment variables are the recommended approach for configuration management.
    """

    # --- General Application Settings ---
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    ENVIRONMENT: Literal["development", "staging", "production"] = os.environ.get("ENVIRONMENT", "development").lower()

    # --- Database Configuration ---
    DATABASE_URL = os.environ.get("DATABASE_URL",
                                  "postgresql://admin:npg_Lxe83skfqKTg@ep-steep-sound-a5jr9vda-pooler.us-east-2.aws.neon.tech:5432/data")  # PostgreSQL connection string
    DATABASE_POOL_SIZE: int = int(os.environ.get("DATABASE_POOL_SIZE", "5"))
    DATABASE_MAX_OVERFLOW: int = int(os.environ.get("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_POOL_RECYCLE: int = int(os.environ.get("DATABASE_POOL_RECYCLE", "600"))  # 10 minutes in seconds
    DATABASE_POOL_TIMEOUT: int = int(os.environ.get("DATABASE_POOL_TIMEOUT", "30"))  # 30 seconds
    DATABASE_ECHO_LOGGING: bool = os.environ.get("DATABASE_ECHO_LOGGING", "False").lower() == "true"

    # --- Logging Configuration ---
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()
    """
    Default logging level for the application.
    Possible values: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    Set to INFO in production and DEBUG for more verbose output during development.
    """
    LOG_FORMAT: Literal["json", "text"] = os.environ.get("LOG_FORMAT", "text").lower()
    """
    Format for application logs. Can be 'json' for structured logging (recommended for production) or 'text' for plain text (for development).
    'json' format is suitable for parsing and analysis by log aggregation tools.
    """
    LOG_HANDLERS: str = os.environ.get("LOG_HANDLERS", "console")
    """
    Comma-separated list of log handlers to use.
    Possible values (configurable in logging_config.py): 'console', 'file', 'syslog'.
    Example: 'console,file' to log to both console and a file.
    """
    LOG_FILE_PATH: str = os.environ.get("LOG_FILE_PATH", "app.log")

    # --- Authentication and Security Settings ---
    PASSWORD_HASH_SALT_LENGTH: int = int(os.environ.get("PASSWORD_HASH_SALT_LENGTH", "16"))
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", secrets.token_hex(32))
    JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRY_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRY_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRY_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRY_DAYS", "7"))
    OTP_LENGTH: int = int(os.environ.get("OTP_LENGTH", "6"))
    OTP_EXPIRY_SECONDS: int = int(os.environ.get("OTP_EXPIRY_SECONDS", "180"))  # 3 minutes

    # --- Rate Limiting Configuration ---
    OTP_RATE_LIMIT: str = os.environ.get("OTP_RATE_LIMIT", "20 per minute")
    REGISTER_RATE_LIMIT: str = os.environ.get("REGISTER_RATE_LIMIT", "5 per minute")
    LOGIN_RATE_LIMIT: str = os.environ.get("LOGIN_RATE_LIMIT", "100 per hour")

    # --- Email Service Configuration ---
    EMAIL_PROVIDER: Literal["smtp", "sendgrid", "mock"] = os.environ.get("EMAIL_PROVIDER", "mock").lower()
    """
    Email service provider to use for sending emails.
    Possible values: 'smtp' (direct SMTP), 'sendgrid' (SendGrid API), 'mock' (for development/testing - no actual sending).
    """
    EMAIL_SENDER_ADDRESS: str = os.environ.get("EMAIL_SENDER_ADDRESS", "noreply@example.com")
    EMAIL_SENDER_NAME: str = os.environ.get("EMAIL_SENDER_NAME", "Your App Name")
    OTP_EMAIL_SUBJECT: str = os.environ.get("OTP_EMAIL_SUBJECT", "[{sender_name}] Your One-Time Password (OTP)")
    OTP_EMAIL_TEMPLATE: str = os.environ.get("OTP_EMAIL_TEMPLATE", """
    <html>
    <body>
        <p>Dear User,</p>
        <p>Your One-Time Password (OTP) for [{sender_name}] is:</p>
        <h2>{otp}</h2>
        <p>This OTP will expire in 5 minutes. Please do not share it with anyone.</p>
        <p>Thank you,<br/>The {sender_name} Team</p>
    </body>
    </html>
    """).strip()  # Strip whitespace from multiline template

    # --- SMTP Configuration (Required if EMAIL_PROVIDER is 'smtp') ---
    SMTP_SERVER: str = os.environ.get("SMTP_SERVER", "localhost")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))  # Default SMTP port with TLS
    SMTP_USERNAME: str = os.environ.get("SMTP_USERNAME")  # Optional, depending on SMTP server
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD")  # Optional, depending on SMTP server

    # --- SendGrid Configuration (Required if EMAIL_PROVIDER is 'sendgrid') ---
    SENDGRID_API_KEY: Optional[str] = os.environ.get("SENDGRID_API_KEY")
