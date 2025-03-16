import logging
from abc import ABC, abstractmethod

import sendgrid

from app.config import Config
from app.core.exception import InternalServerError

logger = logging.getLogger(__name__)
config = Config()  # Assuming Config is already instantiated elsewhere


class EmailSender(ABC):
    """
    Abstract base class for email senders.
    Defines the interface for sending emails, allowing for different email provider implementations.
    """

    @abstractmethod
    def send_email(self, recipient_email: str, subject: str, body: str, request_id: str = None):
        """
        Abstract method to send an email.

        Args:
            recipient_email (str): Email address of the recipient.
            subject (str): Subject of the email.
            body (str): HTML body of the email.
            request_id (str, optional): Request ID for logging and tracing. Defaults to None.

        Raises:
            NotImplementedError: If the method is not implemented in a concrete subclass.
            InternalServerError: If there's an error sending the email.
        """
        raise NotImplementedError("Subclasses must implement send_email method")


class SMTPEmailSender(EmailSender):
    """
    Email sender implementation using SMTP protocol directly.
    Suitable for simple setups or when direct SMTP access is preferred.
    """

    def __init__(self):
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.smtp_username = config.SMTP_USERNAME
        self.smtp_password = config.SMTP_PASSWORD
        self.sender_email = config.EMAIL_SENDER_ADDRESS

    def send_email(self, recipient_email: str, subject: str, body: str, request_id: str = None):
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        message = MIMEMultipart()
        message['From'] = self.sender_email
        message['To'] = recipient_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'html'))  # Send as HTML email

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Upgrade to secure connection
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
            logger.info(f"Request ID: {request_id} - Email sent successfully to {recipient_email} via SMTP.")
        except Exception as e:
            logger.error(f"Request ID: {request_id} - Error sending email to {recipient_email} via SMTP: {e}",
                         exc_info=True)
            raise InternalServerError(detail="Failed to send email via SMTP", error_code="email_smtp_failure") from e


class SendGridEmailSender(EmailSender):
    """
    Email sender implementation using SendGrid API.
    Suitable for scalable and reliable email delivery with features like tracking and analytics.
    Requires SendGrid API key configuration.
    """

    def __init__(self):
        self.sendgrid_api_key = config.SENDGRID_API_KEY
        self.sender_email = config.EMAIL_SENDER_ADDRESS

    def send_email(self, recipient_email: str, subject: str, body: str, request_id: str = None):
        if not self.sendgrid_api_key:
            logger.error(f"Request ID: {request_id} - SendGrid API Key not configured.")
            raise InternalServerError(detail="SendGrid API Key not configured", error_code="sendgrid_config_error")

        sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
        # from_email = From(self.sender_email)
        # to_email = To(recipient_email)
        # subject_obj = Subject(subject)
        # content = Content("text/html", body)  # Send as HTML email
        # mail = Mail(from_email, to_email, subject_obj, content)

        try:
            response = sg.client.mail.send.post(request_body=config.OTP_EMAIL_TEMPLATE)
            if response.status_code == 202:  # 202 Accepted is success for SendGrid
                logger.info(
                    f"Request ID: {request_id} - Email sent successfully to {recipient_email} via SendGrid. Status Code: {response.status_code}")
            else:
                logger.warning(
                    f"Request ID: {request_id} - SendGrid email sending failed for {recipient_email}. Status Code: {response.status_code}, Body: {response.body}, Headers: {response.headers}")
                raise InternalServerError(detail=f"SendGrid email sending failed. Status Code: {response.status_code}",
                                          error_code="email_sendgrid_failure")
        except Exception as e:
            logger.error(f"Request ID: {request_id} - Error sending email to {recipient_email} via SendGrid: {e}",
                         exc_info=True)
            raise InternalServerError(detail="Failed to send email via SendGrid",
                                      error_code="email_sendgrid_failure") from e


class MockEmailSender(EmailSender):
    """
    Mock email sender for development and testing purposes.
    Does not actually send emails, but logs the email content.
    """

    def send_email(self, recipient_email: str, subject: str, body: str, request_id: str = None):
        logger.info(f"Request ID: {request_id} - Mock Email Sender - Sending email to: {recipient_email}")
        logger.info(f"Request ID: {request_id} - Mock Email Sender - Subject: {subject}")
        logger.info(f"Request ID: {request_id} - Mock Email Sender - Body: {body}")
        logger.info(f"Request ID: {request_id} - Mock Email Sender - (Email not actually sent in mock mode)")


class EmailService:
    """
    Service class for sending emails, abstracting the underlying email sender implementation.
    Uses a configured EmailSender (SMTP, SendGrid, Mock) to dispatch emails.
    """

    def __init__(self, email_sender: EmailSender):
        """
        Initializes EmailService with a specific EmailSender implementation.

        Args:
            email_sender (EmailSender): An instance of EmailSender (e.g., SMTPEmailSender, SendGridEmailSender).
        """
        self.email_sender = email_sender
        self.sender_name = config.EMAIL_SENDER_NAME  # Optional sender name
        self.otp_email_subject = config.OTP_EMAIL_SUBJECT  # Subject from config
        self.otp_email_template = config.OTP_EMAIL_TEMPLATE  # HTML template from config

    def send_otp_email(self, recipient_email: str, otp: str, request_id: str = None):
        """
        Sends an OTP email to the specified recipient.
        Uses the configured EmailSender to dispatch the email.

        Args:
            recipient_email (str): Email address of the OTP recipient.
            otp (str): One-Time Password to be sent.
            request_id (str, optional): Request ID for logging and tracing. Defaults to None.
        """
        subject = self.otp_email_subject.format(sender_name=self.sender_name)  # Use subject from config and format
        body = self.otp_email_template.format(otp=otp,
                                              sender_name=self.sender_name)  # Use HTML template from config and format

        try:
            self.email_sender.send_email(recipient_email, subject, body, request_id)  # Delegate to EmailSender
            logger.info(
                f"Request ID: {request_id} - OTP email sending process initiated for {recipient_email} using {type(self.email_sender).__name__}")
        except InternalServerError as e:  # Catch EmailSender specific InternalServerError
            logger.error(
                f"Request ID: {request_id} - Failed to send OTP email to {recipient_email} using {type(self.email_sender).__name__}: {e.detail}",
                exc_info=True)
            raise e  # Re-raise the exception to be handled upstream
        except Exception as e:  # Catch any unexpected errors during email sending setup
            logger.error(
                f"Request ID: {request_id} - Unexpected error preparing to send OTP email to {recipient_email}: {e}",
                exc_info=True)
            raise InternalServerError(detail="Unexpected error preparing OTP email",
                                      error_code="email_preparation_error") from e


# --- Configuration and Instance Creation ---

def create_email_service():
    """
    Factory function to create and configure EmailService based on configuration.
    Selects the EmailSender implementation based on EMAIL_PROVIDER in Config.
    """
    email_provider = config.EMAIL_PROVIDER.lower()

    if email_provider == "smtp":
        sender = SMTPEmailSender()
        logger.info("EmailService configured to use SMTP Email Sender.")
    elif email_provider == "sendgrid":
        sender = SendGridEmailSender()
        logger.info("EmailService configured to use SendGrid Email Sender.")
    elif email_provider == "mock":
        sender = MockEmailSender()
        logger.info("EmailService configured to use Mock Email Sender (for development/testing).")
    else:
        sender = MockEmailSender()  # Default to mock if invalid or missing config. Safer default.
        logger.warning(
            f"Invalid or missing EMAIL_PROVIDER configuration: '{config.EMAIL_PROVIDER}'. Defaulting to Mock Email Sender.")

    return EmailService(sender)


email_service = create_email_service()  # Instantiate EmailService using factory function
