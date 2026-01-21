from fluvius.query import DomainQueryResource
from fluvius.query.field import (
    StringField,
    BooleanField,
    DatetimeField,
    UUIDField,
    EnumField,
    ArrayField,
    IntegerField,
    JSONField,
)
from typing import Optional, List
from fluvius.data import UUID_TYPE
from .manager import resource, scope
from ..types import (
    PriorityLevelEnum,
    ContentTypeEnum,
    MessageTypeEnum,
)


@resource("message-thread")
class MessageThreadQuery(DomainQueryResource):
    """Query resource for message thread."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "thread_id": scope["thread_id"],
            "visible_profile_ids.ov": [profile_id],
            ".or": [
                {"sender_id": profile_id},
                {"recipient_id.ov": [profile_id]},
            ],
        }

    class Meta:
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        scope_required = scope.ThreadIdScope
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "_message_thread"

        default_order = ("_created.desc",)

    message_id: UUID_TYPE = UUIDField("Message ID")
    thread_id: Optional[UUID_TYPE] = UUIDField("Thread ID")
    sender_id: UUID_TYPE = UUIDField("Sender ID")
    sender_profile: Optional[dict] = JSONField("Sender Profile")
    recipient_id: List[UUID_TYPE] = ArrayField("Recipient ID", default=[])
    recipient_profile: Optional[dict] = JSONField("Recipient Profile")
    subject: Optional[str] = StringField("Subject")
    content: Optional[str] = StringField("Content")
    rendered_content: Optional[str] = StringField("Rendered Content")
    content_type: Optional[ContentTypeEnum] = EnumField(
        "Content Type", enum=ContentTypeEnum
    )
    is_important: Optional[bool] = BooleanField("Is Important")
    expirable: Optional[bool] = BooleanField("Is Expirable")
    expiration_date: Optional[str] = DatetimeField("Expiration Date")
    request_read_receipt: Optional[bool] = BooleanField("Request Read Receipt")
    priority: Optional[PriorityLevelEnum] = EnumField(
        "Priority Level", enum=PriorityLevelEnum
    )
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    delivery_status: Optional[str] = StringField("Delivery Status")
    data: Optional[dict] = JSONField("Data")
    context: Optional[dict] = JSONField("Context")
    template_key: Optional[str] = StringField("Template Key")
    template_version: Optional[int] = IntegerField("Template Version")
    template_locale: Optional[str] = StringField("Template Locale")
    template_engine: Optional[str] = StringField("Template Engine")
    template_data: Optional[dict] = JSONField("Template Data")
    render_strategy: Optional[str] = StringField("Render Strategy")
    render_status: Optional[str] = StringField("Render Status")
    rendered_at: Optional[str] = DatetimeField("Rendered At")
    render_error: Optional[str] = StringField("Render Error")
    message_count: Optional[int] = IntegerField("Message Count")
    visible_profile_ids: List[UUID_TYPE] = ArrayField("Visible Profile IDs", default=[])
