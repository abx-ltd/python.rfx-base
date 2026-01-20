from . import datadef
from . import Command
from fluvius.data import serialize_mapping


class CreateTemplate(Command):
    """Create a new message template."""

    Data = datadef.CreateTemplatePayload

    class Meta:
        key = "create-template"
        new_resource = True
        resources = ("message_template",)
        tags = ["template", "create"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.create_template(data=serialize_mapping(payload))

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-service-response",
        )


class UpdateTemplate(Command):
    """Update a template"""

    Data = datadef.CreateTemplatePayload

    class Meta:
        key = "update-template"
        resource = "message_template"
        tags = ["template", "create"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.update_template(data=serialize_mapping(payload))

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-service-response",
        )


class PublishTemplate(Command):
    """Publish a template to make it available."""

    # Data = datadef.PublishTemplatePayload

    class Meta:
        key = "publish-template"
        resources = ("message_template",)
        tags = ["template", "publish"]
        auth_required = True
        policy_required = False

    async def _process(self, agg, stm, payload):
        result = await agg.publish_template()

        yield agg.create_response(
            serialize_mapping(result),
            _type="message-service-response",
        )
