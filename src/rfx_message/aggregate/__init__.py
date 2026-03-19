"""
RFX Messaging Domain Aggregate - Business Logic and State Management
"""

from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, timestamp, UUID_GENR
from typing import Optional, Dict, Any


from .message import MessageMixin
from .message_sender import MessageSenderMixin
from .message_recipient import MessageRecipientMixin
from .message_box import MessageBoxMixin
from .read_message import ReadMessageMixin

from .tag import TagMixin
from .message_tag import MessageTagMixin
from .message_category import MessageCategoryMixin


class MessageAggregate(
    Aggregate,
    MessageMixin,
    MessageSenderMixin,
    MessageRecipientMixin,
    MessageBoxMixin,
    ReadMessageMixin,
    TagMixin,
    MessageTagMixin,
    MessageCategoryMixin,
):
    """
    Aggregate for managing message-related operations.
    This includes actions on messages, recipients, attachments, embedded content, and references.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


__all__ = [
    "MessageAggregate",
]
