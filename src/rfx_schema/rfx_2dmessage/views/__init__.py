from .mailbox import mailbox_view
from .message_detail import message_detail_view
from .message_mailbox import message_mailbox_view
from .message_tag import message_tag_view
# from .message_category import message_category_view
from .mailbox_folder import mailbox_folder_view
from .mailbox_member import mailbox_member_view


ALL_VIEWS = [
    mailbox_view,
    message_detail_view,
    message_mailbox_view,
    message_tag_view,
    mailbox_member_view,
    # message_category_view,
    mailbox_folder_view,
]
