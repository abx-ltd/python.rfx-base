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


class AttachmentUploadPayload(DataModel):
    file_name: str
    file_type: str
    file_size: str


class AttachFileToCommentPayload(DataModel):
    file_url: str
    file_name: str
    file_type: str
    file_size: int
    file_extension: Optional[str] = None

    is_image: Optional[bool] = False
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    thumbnail_url: Optional[str] = None


class UpdateAttachmentPayload(DataModel):
    attachment_id: UUID_TYPE
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    upload_status: Optional[str] = None


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
