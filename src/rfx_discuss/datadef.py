from typing import Optional

from pydantic import Field
from fluvius.data import DataModel, UUID_TYPE

from .types import Priority, Availability




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

