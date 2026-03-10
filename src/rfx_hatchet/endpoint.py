from fluvius.media import FsSpecCompressionMethod
from pydantic import BaseModel


class HatchetWorkflowRunMetadata(BaseModel):
    fs_key: str = None
    compress: FsSpecCompressionMethod = None
    resource: str
    resource_id: str
