from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DeliveryResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationProvider(ABC):

    @property
    @abstractmethod
    def provider_type(self) -> str:
        pass

    @abstractmethod
    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        pass

    @abstractmethod
    async def validate_config(self) -> bool:
        pass
