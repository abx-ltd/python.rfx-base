from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping


class TemplateMixin:
    @action("template-created", resources="message_template")
    async def create_template(self, *, data):
        """Create a new message template."""
        template_data = serialize_mapping(data)

        old_template = await self.statemgr.find_one(
            "message_template",
            where=dict(
                tenant_id=getattr(data, "tenant_id", None),
                app_id=getattr(data, "app_id", None),
                key=getattr(data, "key", None),
                locale=getattr(data, "locale", None),
                channel=getattr(data, "channel", None),
            ),
        )

        if old_template:
            template_data["version"] = old_template.version + 1
        else:
            template_data["version"] = 1

        template = self.init_resource(
            "message_template", template_data, _id=self.aggroot.identifier
        )
        await self.statemgr.insert(template)

        return {
            "template_id": template._id,
            "key": template.key,
        }

    @action("template-updated", resources="message_template")
    async def update_template(self, *, data):
        """Update an existing message template."""
        template = self.statemgr.fetch("message_template", self.aggroot.identifier)
        if template:
            return ValueError(f"Template not found: {self.aggroot.identifier}")

        await self.statemgr.update(template, **data)

        return {
            "template_id": template._id,
            "key": template.key,
            "version": template.version,
        }

    @action("template-published", resources="message_template")
    async def publish_template(self):
        """Publish a template to make it available for use."""
        template = await self.statemgr.fetch(
            "message_template", self.aggroot.identifier
        )
        if not template:
            raise ValueError(f"Template not found: {self.aggroot.identifier}")

        await self.statemgr.update(template, status="PUBLISHED")

        # Invalidate cache if using content processor
        if hasattr(self, "_content_processor") and self._content_processor:
            await self._content_processor.template_service.invalidate_template_cache(
                template.key, template.version
            )

        return {
            "template_id": template._id,
            "key": template.key,
            "version": template.version,
            "status": "PUBLISHED",
        }
