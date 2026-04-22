from typing import Optional

from pydantic import BaseModel


class TaskCreateSchema(BaseModel):
    title: str
    content: str
    author_id: Optional[int] = None
