from .mailbox import mailbox_view
from .message_mailbox_state import message_mailbox_state_view
from .message_mailbox import message_mailbox_view
from .message_tag import message_tag_view


ALL_VIEWS = [
    mailbox_view,
    message_mailbox_state_view,
    message_mailbox_view,
    message_tag_view,
]
