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
from .manager import resource
from ..types import (
    PriorityLevelEnum,
    ContentTypeEnum,
    MessageTypeEnum,
    MessageCategoryEnum,
    BoxTypeEnum,
    DirectionTypeEnum,
)


@resource("message-trashed")
class MessageTrashedQuery(DomainQueryResource):
    """Query resource for message trashed."""

    @classmethod
    def base_query(cls, context, scope):
        profile_id = context.profile._id
        return {
            "target_profile_id": profile_id,
            "box_key": "trashed",
            "message_type": MessageTypeEnum.USER.value,
        }

    class Meta(DomainQueryResource.Meta):
        include_all = True
        allow_item_view = True
        allow_list_view = True
        allow_meta_view = True
        # allow_text_search = True
        # allow_path_query = True

        backend_model = "_message_box"

        # policy_required = True  # Enable access control
        # scope_optional = ResourceScope

        default_order = ("_created.desc",)

    message_id: UUID_TYPE = UUIDField("Message ID")
    thread_id: Optional[UUID_TYPE] = UUIDField("Thread ID")
    sender_id: UUID_TYPE = UUIDField("Sender ID")
    sender_profile: Optional[dict] = JSONField("Sender Profile")
    recipient_id: List[UUID_TYPE] = ArrayField("Recipient ID", default=[])
    recipient_profile: Optional[dict] = JSONField("Recipient Profile")
    subject: Optional[str] = StringField("Subject")
    content: Optional[str] = StringField("Content")
    content_type: Optional[ContentTypeEnum] = EnumField(
        "Content Type", enum=ContentTypeEnum
    )
    expirable: Optional[bool] = BooleanField("Is Expirable")
    priority: Optional[PriorityLevelEnum] = EnumField(
        "Priority Level", enum=PriorityLevelEnum
    )
    message_type: Optional[MessageTypeEnum] = EnumField(
        "Message Type", enum=MessageTypeEnum
    )
    category: Optional[MessageCategoryEnum] = EnumField(
        "Category", enum=MessageCategoryEnum
    )
    is_read: Optional[bool] = BooleanField("Is Read", default=False)
    recipient_read_at: Optional[str] = DatetimeField("Recipient Read At")
    box_key: Optional[str] = StringField("Box Key")
    box_name: Optional[str] = StringField("Box Name")
    box_type_enum: Optional[BoxTypeEnum] = EnumField("Box Type", enum=BoxTypeEnum)
    target_profile_id: UUID_TYPE = UUIDField("Target Profile ID")
    message_count: Optional[int] = IntegerField("Message Count")
    root_type: str = StringField("Root Type")
    direction: Optional[DirectionTypeEnum] = EnumField(
        "Direction", enum=DirectionTypeEnum
    )
    tags: Optional[List[str]] = ArrayField("Tags", default=[])
