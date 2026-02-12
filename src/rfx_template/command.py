from fluvius.data import serialize_mapping
from . import datadef
from .domain import TemplateServiceDomain

Command = TemplateServiceDomain.Command

class CreateTemplate(Command):
    """Create a new template."""

    class Meta:
        key = "create-template"
        resource_init = True
        resources = ("template", )
        tags = ["template"]
        auth_required = True
        policy_required = False

    Data = datadef.CreateTemplatePayload

    async def _process(self, agg, stm, payload):
        # Convert payload to dict
        data = serialize_mapping(payload)

        # Call aggregate
        result = await agg.create_template(data)

        # Yield response
        yield agg.create_response(
            result,
            _type="template-service-response",
        )

class UpdateTemplate(Command):
    """Update an existing template."""

    class Meta:
        key = "update-template"
        tags = ["template"]
        resources = ("template", )
        auth_required = True
        policy_required = False

    Data = datadef.UpdateTemplatePayload

    async def _process(self, agg, stm, payload):
        data = serialize_mapping(payload)
        await agg.update_template(data)
        yield agg.create_response({"status": "success"}, _type="template-service-response")


class RenderTemplate(Command):
    """Render a template with provided data."""

    class Meta:
        key = "render-template"
        tags = ["template"]
        resource_init = True
        resources = ("template", )
        auth_required = True
        policy_required = False

    Data = datadef.RenderTemplatePayload

    async def _process(self, agg, stm, payload):
        data = serialize_mapping(payload)
        rendered_result = await agg.render_template(data)

        yield agg.create_response(
            rendered_result,  # Dict with 'body' and optional metadata fields like 'subject'
            _type="template-service-response"
        )
