from pydantic import BaseModel
from typing import Optional


class TeamMemberBase(BaseModel):

    name: str
    role: str
    description: Optional[str] = None
    order: int = 0
    is_active: bool = True


class TeamMemberCreate(TeamMemberBase):
    pass


class TeamMemberUpdate(BaseModel):

    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class TeamMemberResponse(TeamMemberBase):

    id: int
    image_url: Optional[str] = None

    class Config:
        from_attributes = True