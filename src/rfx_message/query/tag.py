from fluvius.query import DomainQueryResource
from fluvius.query.field import (
    StringField,
)
from typing import Optional
from .manager import resource


@resource("tag")
class TagQuery(DomainQueryResource):
    """Query resource for tags."""

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
