import uuid

from sqlalchemy import Column, Integer, String, DateTime, func, Index, UUID

from app.extensions import Base


class OTP(Base):
    __tablename__ = "otp"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                index=True)  # Generate UUIDs on application side
    user_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, index=True)
    country_code = Column(String(10), nullable=True, doc="Country code for phone number")
    phone_number = Column(String(20), nullable=True, doc="Recipient's phone number")
    email = Column(String(255), nullable=True, index=True, doc="Recipient's email address")
    otp_hash = Column(String(255), nullable=False, doc="Hashed OTP value")
    otp_expiry = Column(DateTime(timezone=True), nullable=False, doc="OTP expiry timestamp")
    request_type = Column(String(50), nullable=True, doc="Type of OTP request (e.g., registration, password_reset)")
    verification_attempts = Column(Integer, default=0, doc="Number of verification attempts")
    last_attempt_at = Column(DateTime(timezone=True), nullable=True, doc="Timestamp of last verification attempt")
    status = Column(String(20), default="pending", doc="Status of OTP request (pending, verified, expired, invalid)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), doc="Timestamp when record was created")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), doc="Timestamp when record was last updated")

    __table_args__ = (
        Index('ix_otp_user_status', user_id, status),
        Index('ix_otp_email_status', email, status),
        Index('ix_otp_phone_status', country_code, phone_number, status),
    )

    def __repr__(self):
        return f"<OTP(user_id='{self.user_id}', id={self.id}, status='{self.status}')>"

    def to_dict(self):
        """
        Returns a dictionary representation of the OTP object, suitable for API responses or logging.
        Excludes sensitive information like otp_hash.
        Ensures datetime objects are serialized to ISO format for consistent data exchange.
        """
        return {
            "id": str(self.id),  # Convert UUID to string for JSON serialization
            "user_id": str(self.user_id),
            "country_code": self.country_code,
            "phone_number": self.phone_number,
            "email": self.email,
            # Security: Do NOT expose the OTP hash in to_dict()
            "otp_expiry": self.otp_expiry.isoformat() if self.otp_expiry else None,
            "request_type": self.request_type,
            "verification_attempts": self.verification_attempts,
            "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
