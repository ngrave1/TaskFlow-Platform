from pydantic import BaseModel


class UserDtoSchema(BaseModel):
    email: str


class NotificationDTO(BaseModel):
    recipient: str
    provider: str
    subject: str
    message: str
