from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import  String, Integer, text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import TableBase, SCHEMA
from .types import MediaTypeEnum

if TYPE_CHECKING:
    from .message import Message



class MessageAttachment(TableBase):
    """Files linked to a message."""
    from ..rfx_media.media import MediaEntry

    __tablename__ = "message_attachment"

    # _iid: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.message._id"), primary_key=True
    )
    media_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(MediaEntry._id, name="fk_media", ondelete="RESTRICT"),
        nullable=False,
    )
    # file_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    # file_name: Mapped[Optional[str]] = mapped_column(String(255))
    # storage_key: Mapped[Optional[str]] = mapped_column(String(1024))

    media_type: Mapped[Optional[MediaTypeEnum]] = mapped_column(
        SQLEnum(MediaTypeEnum, name="mediatypeenum", schema=SCHEMA),
        default=MediaTypeEnum.DOCUMENT,
        nullable=False,
    )    

    # Fixed: Match DDL exactly - nullable=True, server_default
    display_order: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        server_default=text("0"),
    )
    is_primary: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        server_default=text("false"),
    )

    # size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String)

    # download_policy: Mapped[str] = mapped_column(String, nullable=True)

    message: Mapped["Message"] = relationship("Message",back_populates="attachments")
