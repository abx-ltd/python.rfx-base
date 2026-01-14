from .message_inbox import message_inbox_view
from .message_outbox import message_outbox_view
from .message_box import message_box_view
from .message_thread import message_thread_view

ALL_VIEWS = [
    message_inbox_view,
    message_outbox_view,
    message_box_view,
    message_thread_view,
]
