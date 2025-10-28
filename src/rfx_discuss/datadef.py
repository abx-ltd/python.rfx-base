from fluvius.data import DataModel


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
