from typing import Optional
from pydantic import Field
from fluvius.data import DataModel
from ..types import DirectionTypeEnum


class CreateTagPayload(DataModel):
    """Payload for creating a new tag."""

    name: str = Field(..., description="Name of the tag")
    background_color: Optional[str] = Field(
        None, description="Background color of the tag"
    )
    font_color: Optional[str] = Field(None, description="Font color of the tag")
    description: Optional[str] = Field(None, description="Description of the tag")


class UpdateTagPayload(DataModel):
    """Payload for updating a tag."""

    name: Optional[str] = Field(None, description="Name of the tag")
    background_color: Optional[str] = Field(
        None, description="Background color of the tag"
    )
    font_color: Optional[str] = Field(None, description="Font color of the tag")
    description: Optional[str] = Field(None, description="Description of the tag")


class AddMessageTagPayload(DataModel):
    """Payload for adding a tag to a message."""

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to add tag: INBOUND (inbox) or OUTBOUND (outbox). If None, add tag for both if user sent to themselves.",
    )
    key: str = Field(..., description="Key of the tag")


class RemoveMessageTagPayload(DataModel):
    """Payload for removing a tag from a message."""

    direction: Optional[DirectionTypeEnum] = Field(
        default=DirectionTypeEnum.INBOUND,
        description="Direction to remove tag: INBOUND (inbox) or OUTBOUND (outbox). If None, remove tag for both if user sent to themselves.",
    )
    key: str = Field(..., description="Key of the tag")

