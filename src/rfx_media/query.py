from .domain import RFXMediaDomain
from fluvius.data import UUID_TYPE, logger
from fluvius.query import DomainQueryManager, DomainQueryResource, endpoint
from fluvius.query.field import StringField, UUIDField, IntegerField, DatetimeField
from datetime import datetime
from . import scope
from fluvius.media import MediaManager


class RFXMediaQueryManager(DomainQueryManager):
    __data_manager__ = MediaManager

    class Meta(DomainQueryManager.Meta):
        prefix = RFXMediaDomain.Meta.prefix
        tags = RFXMediaDomain.Meta.tags


resource = RFXMediaQueryManager.register_resource
endpoint = RFXMediaQueryManager.register_endpoint


@resource("media")
class MediaQuery(DomainQueryResource):
    """Media queries"""

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        scope_required = scope.ResourceScope

        backend_model = "media-entry"

    @classmethod
    def base_query(cls, context, scope):
        logger.info(f"Scope: {scope}")
        return {"resource": scope["resource"], "resource__id": scope["resource_id"]}

    filename: str = StringField("Filename")
    filehash: str = StringField("File Hash")
    filemime: str = StringField("File MIME")
    fskey: str = StringField("FS Key")
    length: int = IntegerField("Length")
    fspath: str = StringField("FS Path")
    compress: str = StringField("Compress")
    resource: str = StringField("Resource")
    resource__id: UUID_TYPE = UUIDField("Resource ID")
    resource_sid: UUID_TYPE = UUIDField("Resource SID")
    resource_iid: UUID_TYPE = UUIDField("Resource IID")
    xattrs: str = StringField("XAttrs")
    cdn_exp: datetime = DatetimeField("CDN Exp")
    cdn_url: str = StringField("CDN URL")
