from pydantic import BaseModel
from typing import Optional


class TaskCreateSchema(BaseModel):
    title: str
    content: str
    author_id: Optional[int] = None
