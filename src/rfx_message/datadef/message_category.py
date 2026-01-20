from typing import Optional
from pydantic import Field
from fluvius.data import DataModel
from ..types import MessageCategoryEnum, DirectionTypeEnum


class SetMessageCategoryPayload(DataModel):
    """Payload for setting the category of a message."""

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to set category: INBOUND (inbox) or OUTBOUND (outbox). If None, set category for both if user sent to themselves.",
    )
    category: MessageCategoryEnum = Field(
        default=MessageCategoryEnum.INFORMATION, description="Message category"
    )


class RemoveMessageCategoryPayload(DataModel):
    """Payload for removing the category of a message."""

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to remove category: INBOUND (inbox) or OUTBOUND (outbox). If None, remove category for both if user sent to themselves.",
    )
