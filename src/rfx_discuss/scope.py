from pydantic import BaseModel
from fluvius.query.field import UUIDField
from fluvius.data import UUID_TYPE


class CommentScopeSchema(BaseModel):
    resource_id: UUID_TYPE = UUIDField("Resource ID")


class CommentAttachmentScopeSchema(BaseModel):
    comment_id: UUID_TYPE = UUIDField("Comment ID")


class ReactionScopeSchema(BaseModel):
    comment_id: UUID_TYPE = UUIDField("Comment ID")


class FlagScopeSchema(BaseModel):
    comment_id: UUID_TYPE = UUIDField("Comment ID")
