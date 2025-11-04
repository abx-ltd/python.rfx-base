from pipe import Pipe
from fluvius.worker import DomainWorker, DomainWorkerClient, export_task
from rfx_message import config


class MessageClient(DomainWorkerClient):
    # @TODO: Need config for queue name
    __queue_name__ = 'rfx-message'

@Pipe
def configure_message_client(app):
    """Configure the message client"""
    client = MessageClient()
    app.state.msg_client = client
    return app
