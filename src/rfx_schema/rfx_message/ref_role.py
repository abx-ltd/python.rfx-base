from . import TableBase
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class RefRole(TableBase):
    """Reference role catalog used by the messaging service."""

    __tablename__ = "ref__role"

    key: Mapped[str] = mapped_column(String(255), primary_key=True, unique=True)
