from pipe import Pipe
from fluvius.worker import DomainWorkerClient


class MessageClient(DomainWorkerClient):
    # @TODO: Need config for queue name
    __queue_name__ = "cpo_portal_worker"


@Pipe
def configure_message_client(app):
    """Configure the message client"""
    client = MessageClient()
    app.state.msg_client = client
    return app
