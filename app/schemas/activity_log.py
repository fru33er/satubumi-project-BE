from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ActivityLogResponse(BaseModel):

    id: int

    user_id: int | None

    user_name: str | None = None

    user_email: str | None = None

    action: str

    module: str

    target_id: int | None

    target_name: str | None

    description: str | None

    created_at: datetime


    class Config:
        from_attributes = True

class ActivityLogMyResponse(BaseModel):

    id: int

    user_id: Optional[int]

    action: str

    module: str

    target_id: Optional[int]

    target_name: Optional[str]

    description: Optional[str]

    created_at: datetime


    class Config:
        from_attributes = True