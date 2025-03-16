import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Index, UUID

from app.extensions import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4,
                doc="Unique user identifier")  # Generate UUIDs on application side
    country_code = Column(String(10), nullable=False, doc="Country code for phone number")
    phone_number = Column(String(20), nullable=False, doc="User's phone number")
    email = Column(String(255), unique=True, nullable=False, index=True, doc="User's email address")
    hashed_password = Column(String(255), nullable=False, doc="Hashed user password")
    first_name = Column(String(100), nullable=False, doc="User's first name")
    middle_name = Column(String(100), nullable=True, doc="User's middle name (optional)")
    last_name = Column(String(100), nullable=False, doc="User's last name")
    display_name = Column(String(255), nullable=True, doc="User's display name (optional)")
    role = Column(String(50), nullable=True, default="user", doc="User's role or permissions level")
    is_email_verified = Column(Boolean, default=False, doc="Flag indicating if email is verified")
    is_phone_verified = Column(Boolean, default=False, doc="Flag indicating if phone is verified")
    email_verified_at = Column(DateTime(timezone=True), nullable=True, doc="Timestamp of email verification")
    phone_verified_at = Column(DateTime(timezone=True), nullable=True, doc="Timestamp of phone verification")
    failed_login_attempts = Column(Integer, default=0, doc="Count of failed login attempts")
    account_locked_until = Column(DateTime(timezone=True), nullable=True, doc="Timestamp until account is locked")
    refresh_token = Column(String(255), nullable=True, doc="Refresh token for session persistence")
    reset_token = Column(String(255), nullable=True, doc="Password reset token")
    reset_token_expiry = Column(DateTime(timezone=True), nullable=True, doc="Expiry timestamp for password reset token")
    google_id = Column(String(255), nullable=True, doc="Google ID for social login")
    facebook_id = Column(String(255), nullable=True, doc="Facebook ID for social login")
    twitter_id = Column(String(255), nullable=True, doc="Twitter ID for social login")
    last_login_at = Column(DateTime(timezone=True), nullable=True, doc="Timestamp of last login")
    last_login_ip = Column(String(50), nullable=True, doc="IP address of last login")
    is_active = Column(Boolean, default=True, doc="Indicates if the user's account is active")
    is_deleted = Column(Boolean, default=False, doc="Indicates if the user's account is soft deleted")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), doc="Timestamp when record was created")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), doc="Timestamp when record was last updated")

    __table_args__ = (
        Index('ix_user_id', id),
        Index('ix_user_email', email),
        Index('ix_user_phone', country_code, phone_number),
        Index('ix_user_role', role),  # Example: Index for role
        Index('ix_user_email_phone', email, country_code, phone_number),
        # Add more indexes as needed based on your application's query patterns
    )

    def __repr__(self):
        return f"<User(email='{self.email}', id={self.id}, role='{self.role}')>"

    def to_dict(self):
        """
        Returns a dictionary representation of the User object, suitable for API responses or logging.
        Excludes sensitive information like 'password_hash', 'refresh_token', and 'reset_token'.
        Ensures datetime objects are serialized to ISO format for consistent data exchange.
        Converts UUID to string for JSON serialization compatibility.
        """
        return {
            "id": str(self.id),  # Convert UUID to string for JSON serialization
            "country_code": self.country_code,
            "phone_number": self.phone_number,
            "email": self.email,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "display_name": self.display_name,
            "role": self.role,
            "is_email_verified": self.is_email_verified,
            "is_phone_verified": self.is_phone_verified,
            "email_verified_at": self.email_verified_at.isoformat() if self.email_verified_at else None,
            "phone_verified_at": self.phone_verified_at.isoformat() if self.phone_verified_at else None,
            "failed_login_attempts": self.failed_login_attempts,
            "account_locked_until": self.account_locked_until.isoformat() if self.account_locked_until else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "last_login_ip": self.last_login_ip,
            "is_active": self.is_active,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # Exclude sensitive fields: password_hash, refresh_token, reset_token
        }
