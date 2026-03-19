from typing import Optional
from pydantic import Field
from fluvius.data import DataModel
from ..types import MessageCategoryEnum, DirectionTypeEnum



class ArchiveMessagePayload(DataModel):
    """Payload for archiving a message."""

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to archive: INBOUND (inbox) or OUTBOUND (outbox). If None, archive both if user sent to themselves.",
    )


class TrashMessagePayload(DataModel):
    """Payload for trashing a message.

    Note: Trash will move all records (both sender and recipient if user sent to themselves)
    to trashed box. No direction needed.
    """

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to trash: INBOUND (inbox) or OUTBOUND (outbox). If None, trash both if user sent to themselves.",
    )


class RestoreMessagePayload(DataModel):
    """Payload for restoring a message from trashed/archived to inbox/outbox."""

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to restore: INBOUND (to inbox) or OUTBOUND (to outbox). If None, restore both if user sent to themselves.",
    )


class RemoveMessagePayload(DataModel):
    """Payload for removing a message."""

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to remove: INBOUND (inbox) or OUTBOUND (outbox). If None, remove both if user sent to themselves.",
    )

