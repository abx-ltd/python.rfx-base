from fluvius.data import DataModel, UUID_TYPE
from typing import Optional
# ---------- Comment Context ----------


class CreateCommentPayload(DataModel):
    content: str
    resource: str
    resource_id: str


class UpdateCommentPayload(DataModel):
    content: str


class DeleteCommentPayload(DataModel):
    pass


class ReplyToCommentPayload(DataModel):
    content: str


class AttachFileToCommentPayload(DataModel):
    media_entry_id: UUID_TYPE
    attachment_type: Optional[str] = None  # 'document', 'image', 'video', 'audio'
    caption: Optional[str] = None
    is_primary: Optional[bool] = False


class UpdateAttachmentPayload(DataModel):
    caption: Optional[str] = None
    attachment_type: Optional[str] = None
    is_primary: Optional[bool] = None
    display_order: Optional[int] = None


class DeleteAttachmentPayload(DataModel):
    attachment_id: UUID_TYPE


class AddReactionPayload(DataModel):
    reaction_type: str  # e.g., like, helpful, insightful, funny


class FlagCommentPayload(DataModel):
    reason: Optional[str] = None
    description: Optional[str] = None


class ResolveFlagPayload(DataModel):
    flag_id: UUID_TYPE
    resolution_note: Optional[str] = None
    resolution_action: Optional[str] = None
