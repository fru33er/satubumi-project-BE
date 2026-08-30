from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean
)

from app.core.database import Base


class TeamMember(Base):

    __tablename__ = "team_members"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    role = Column(
        String(150),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    image_url = Column(
        String(500),
        nullable=True
    )

    order = Column(
        Integer,
        default=0
    )

    is_active = Column(
        Boolean,
        default=True
    )