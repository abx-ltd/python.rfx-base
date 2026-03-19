from fluvius.query import DomainQueryResource
from fluvius.query.field import (
    StringField,
    UUIDField,
)
from typing import Optional
from .manager import resource
from fluvius.data import UUID_TYPE


@resource("tag")
class TagQuery(DomainQueryResource):
    """Query resource for tags."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "profile_id": profile_id,
        }

    class Meta:
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True

        backend_model = "tag"

    key: str = StringField("Tag Key")
    name: str = StringField("Tag Name")
    background_color: Optional[str] = StringField("Background Color")
    font_color: Optional[str] = StringField("Font Color")
    description: Optional[str] = StringField("Description")
    profile_id: Optional[UUID_TYPE] = UUIDField("Profile ID")
