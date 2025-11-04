from fluvius.data import DataModel, serialize_mapping
from .domain import RFXClientDomain
from . import config

# from cpo_portal.integration import get_worker_client


class NotiMessageData(DataModel):
    command: str = "send-message"
    payload: dict = {}
    context: dict = {}


class NotiMessage(RFXClientDomain.Message):
    Data = NotiMessageData

    async def _dispatch(msg):
        data = msg.data

        # await get_worker_client().send(
        #     f"{config.MESSAGE_NAMESPACE}:{data.command}",
        #     command=data.command,
        #     resource="message",
        #     payload=serialize_mapping(data.payload),
        #     _headers={},
        #     _context=dict(
        #         audit=data.context,
        #     ),
        # )
