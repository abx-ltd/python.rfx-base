from .manager import RFXMessageServiceQueryManager

from .message_inbox import MessageInboxQuery
from .message_outbox import MessageOutboxQuery
from .message_archived import MessageArchivedQuery
from .message_trashed import MessageTrashedQuery
from .message_thread import MessageThreadQuery

# from .message_template import MessageTemplateQuery
from .tag import TagQuery

__all__ = [
    "RFXMessageServiceQueryManager",
    "MessageInboxQuery",
    "MessageOutboxQuery",
    "MessageArchivedQuery",
    "MessageTrashedQuery",
    "MessageThreadQuery",
    # "MessageTemplateQuery",
    "TagQuery",
]
