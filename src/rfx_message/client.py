from pipe import Pipe
from fluvius.worker import DomainWorkerClient
from . import config

class MessageClient(DomainWorkerClient):
    __queue_name__ = config.WORKER_QUEUE_NAME


@Pipe
def configure_message_client(app):
    """Configure the message client"""
    client = MessageClient()
    app.state.msg_client = client
    return app
