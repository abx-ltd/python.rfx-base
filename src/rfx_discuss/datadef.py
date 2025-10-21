from typing import Optional

from pydantic import Field
from fluvius.data import DataModel, UUID_TYPE

from .types import Priority, Availability




# ---------- Comment Context ----------


class CreateCommentPayload(DataModel):
    content: str


class UpdateCommentPayload(DataModel):
    content: str
    sync_linear: bool = False
    
    
class DeleteCommentPayload(DataModel):
    sync_linear: bool = False

# ---------- Ticket Comment (Ticket Context) ----------


class CreateTicketCommentPayload(DataModel):
    content: str
    sync_linear: bool = False


class ReplyToCommentPayload(DataModel):
    content: str

# ---------- Status Context ----------


class CreateStatusPayload(DataModel):
    name: str
    description: Optional[str] = None
    entity_type: str
    is_active: bool = True


class CreateStatusKeyPayload(DataModel):
    key: str
    name: str
    description: Optional[str] = None
    is_initial: bool = False
    is_final: bool = False


class CreateStatusTransitionPayload(DataModel):
    src_status_key_id: UUID_TYPE
    dst_status_key_id: UUID_TYPE
    condition: Optional[dict] = None



#------------- Comment Integration----------
class CreateCommentIntegrationPayload(DataModel):
    """Payload for creating comment integration"""
    provider: str = "linear"
    external_id: str
    external_url: Optional[str] = None
    issue_id: Optional[str] = None  # Linear issue ID

class UpdateCommentIntegrationPayload(DataModel):
    """Payload for updating comment integration"""
    provider: str = "linear"
    external_id: str
    external_url: Optional[str] = None
class RemoveCommentIntegrationPayload(DataModel):
    """Payload for removing comment integration"""
    provider: str = "linear"
    external_id: str
    

class SyncCommentIntegrationPayload(DataModel):
    """Payload for syncing comment integration"""
    provider: str = "linear"
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    resource_type: str = "comment"
    issue_id: Optional[str] = None  # Linear issue ID


