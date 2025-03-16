from sqlalchemy.orm import Session

from app.services.otp_service import otp_service, RequestOTPRequest, VerifyOTPRequest
from app.services.token_service import token_service, RefreshAccessTokenRequest, generate_refresh_token
from app.services.user_service import user_service, RegisterUserRequest


class AuthService:
    """
    Facade class to simplify authentication operations.

    This class acts as a facade, providing a simplified interface to the
    underlying authentication services (user service, OTP service, token service).
    It decouples the API controllers from the complexities of managing user registration,
    OTP handling, and token generation/refresh, promoting separation of concerns
    and making the codebase more maintainable and easier to understand.

    Each method in this facade directly delegates the call to the corresponding
    method in the appropriate service, effectively acting as a single entry point
    for authentication-related functionalities from the controllers.
    """

    def register_user(self, request: RegisterUserRequest, db: Session):
        """
        Registers a new user using the user service.

        Delegates the user registration request to the user_service.register_user method.

        Args:
            request (RegisterUserRequest): User registration request data.
            db (Session): SQLAlchemy database session.

        Returns:
            Any: Returns the result from user_service.register_user.
                 (The actual return type depends on the implementation of user_service.register_user)
        """
        return user_service.register_user(request, db)

    def request_otp(self, request: RequestOTPRequest, db: Session):
        """
        Requests an OTP using the OTP service.

        Delegates the OTP request to the otp_service.request_otp method.

        Args:
            request (RequestOTPRequest): OTP request data (email or phone number).
            db (Session): SQLAlchemy database session.

        Returns:
            Any: Returns the result from otp_service.request_otp.
                 (The actual return type depends on the implementation of otp_service.request_otp)
        """
        return otp_service.request_otp(request, db)

    def verify_otp(self, request: VerifyOTPRequest, db: Session):
        """
        Verifies an OTP using the OTP service.

        Delegates the OTP verification request to the otp_service.verify_otp method.

        Args:
            request (VerifyOTPRequest): OTP verification request data (email/phone and OTP).
            db (Session): SQLAlchemy database session.

        Returns:
            Any: Returns the result from otp_service.verify_otp.
                 (The actual return type depends on the implementation of otp_service.verify_otp)
        """
        return otp_service.verify_otp(request, db)

    def refresh_access_token(self, request: RefreshAccessTokenRequest, db: Session):
        """
        Refreshes an access token using the token service.

        Delegates the refresh token request to the token_service.refresh_access_token method.

        Args:
            request (RefreshAccessTokenRequest): Refresh token request data.
            db (Session): SQLAlchemy database session.

        Returns:
            Any: Returns the result from token_service.refresh_access_token.
                 (The actual return type depends on the implementation of token_service.refresh_access_token)
        """
        return token_service.refresh_access_token(request, db)

    def generate_access_token(self, user_email):
        """
        Generates a new access token using the token service.

        Delegates the access token generation to the token_service.generate_access_token method.

        Args:
            user_email (str): User's email address for whom to generate the token.

        Returns:
            str: The generated access token.
        """
        return generate_access_token(user_email)

    def generate_refresh_token(self, user_email):
        """
        Generates a new refresh token using the token service.

        Delegates the refresh token generation to the token_service.generate_refresh_token method.

        Args:
            user_email (str): User's email address for whom to generate the refresh token.

        Returns:
            str: The generated refresh token.
        """
        return generate_refresh_token(user_email)


auth_service = AuthService()  # Instantiate AuthService (Facade)
