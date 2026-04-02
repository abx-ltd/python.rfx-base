# from .message_box import message_box_view
# from .message_thread import message_thread_view
from .message_sender_detail import message_sender_detail_view
from .message_box import message_box_view

ALL_VIEWS = [
    message_box_view,
    # message_thread_view,
    message_sender_detail_view,
]
