from ..domain import RFXMessageServiceDomain
from .. import datadef  # noqa: F401
from .. import helper  # noqa: F401
from .. import types  # noqa: F401

processor = RFXMessageServiceDomain.command_processor
Command = RFXMessageServiceDomain.Command

from .send_message import *
from .reply_message import *
from .message_category import *
from .read_message import *
from .archive_message import *
from .trash_message import *
from .restore_message import *
from .remove_message import *

# from .template import *
from .tag import *
from .message_tag import *
