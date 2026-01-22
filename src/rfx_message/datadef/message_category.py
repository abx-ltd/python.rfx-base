from pydantic import Field
from fluvius.data import DataModel
from ..types import MessageCategoryEnum


class UpdateMessageCategoryPayload(DataModel):
    """Payload for updating the category of a message."""

    category: MessageCategoryEnum = Field(
        default=MessageCategoryEnum.INFORMATION, description="Message category"
    )