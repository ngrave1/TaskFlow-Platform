import uuid
from email.message import EmailMessage
from typing import Optional

import aiosmtplib
import structlog

from .base_notification_provider import DeliveryResult, NotificationProvider

logger = structlog.getLogger(__name__)


class EmailProvider(NotificationProvider):
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = False,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_email = from_email

    @property
    def provider_type(self) -> str:
        return "email"

    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        message: str,
    ) -> DeliveryResult:
        try:
            email = EmailMessage()
            email["From"] = self.from_email
            email["To"] = recipient
            email["Subject"] = subject or "Task notification"
            email.set_content(message)

            async with aiosmtplib.SMTP(
                hostname=self.host, 
                port=self.port, 
                use_tls=True,
                start_tls=False
            ) as smtp:
                if self.username and self.password:
                    await smtp.login(self.username, self.password)
                await smtp.send_message(email)
            logger.info(
                "email.send.attempt",
                recipient=recipient,
                subject=subject,
                message_length=len(message) if message else 0,
            )

            unique_id = uuid.uuid4().hex[:16]
        
            return DeliveryResult(
                success=True, 
                message_id=f"email_{recipient}_{unique_id}"
            )

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return DeliveryResult(success=False, error=str(e))

    async def validate_config(self) -> bool:
        try:
            async with aiosmtplib.SMTP(hostname=self.host, port=self.port, timeout=5) as smtp:
                await smtp.noop()
                return True
        except Exception:
            return False
