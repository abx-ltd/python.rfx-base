"""
RFX Messaging Domain Aggregate - Business Logic and State Management
"""

from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, timestamp, UUID_GENR
from typing import Optional, Dict, Any

from ..processor import MessageContentProcessor
from .message import MessageMixin
from .message_sender import MessageSenderMixin
from .message_recipient import MessageRecipientMixin
from .message_box import MessageBoxMixin
from .read_message import ReadMessageMixin
from .template import TemplateMixin
from .tag import TagMixin
from .message_tag import MessageTagMixin


class MessageAggregate(
    Aggregate,
    MessageMixin,
    MessageSenderMixin,
    MessageRecipientMixin,
    MessageBoxMixin,
    ReadMessageMixin,
    TemplateMixin,
    TagMixin,
    MessageTagMixin,
):
    """
    Aggregate for managing message-related operations.
    This includes actions on messages, recipients, attachments, embedded content, and references.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content_processor = None

    @property
    def content_processor(self) -> MessageContentProcessor:
        """Lazy-loaded content processor."""
        if self._content_processor is None:
            self._content_processor = MessageContentProcessor(self.statemgr)
        return self._content_processor


__all__ = [
    "MessageAggregate",
]
