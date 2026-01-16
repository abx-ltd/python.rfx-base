"""
RFX Messaging Domain Aggregate - Business Logic and State Management
"""

from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, timestamp, UUID_GENR
from typing import Optional, Dict, Any

from .processor import MessageContentProcessor
from .types import ProcessingModeEnum, RenderStatusEnum, MessageCategoryEnum


class MessageAggregate(Aggregate):
    """
    Aggregate for managing message-related operations.
    This includes actions on messages, recipients, attachments, embedded content, and references.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content_processor = None

    @property
    def content_processor(self) -> MessageContentProcessor:
        """Lazy-loaded content processor."""
        if self._content_processor is None:
            self._content_processor = MessageContentProcessor(self.statemgr)
        return self._content_processor

    # ========================================================================
    # MESSAGE OPERATIONS
    # ========================================================================

    @action("message-generated", resources="message")
    async def generate_message(self, *, data, sender_id):
        """Action to create a new message."""
        message_data = data
        message_data["render_status"] = "PENDING"

        message = self.init_resource(
            "message",
            message_data,
            _id=UUID_GENR(),
            sender_id=sender_id,
            thread_id=UUID_GENR(),
        )

        await self.statemgr.insert(message)

        return message

    @action("message-replied", resources="message")
    async def reply_message(self, *, data):
        """Action to reply to a message."""
        message = self.rootobj
        reply_message = self.init_resource(
            "message",
            serialize_mapping(data),
            _id=UUID_GENR(),
            thread_id=message.thread_id,
            sender_id=self.context.profile_id,
            subject=f"Re: {message.subject}",
        )

        await self.statemgr.insert(reply_message)

        return reply_message

    @action(
        "message-category-set",
        resources=("message", "message_recipient", "message_category"),
    )
    async def set_message_category(
        self, *, resource: str, resource_id: str, category: MessageCategoryEnum
    ):
        """Action to set the category of a message."""
        message_category = self.init_resource(
            "message_category",
            {
                "resource": resource,
                "resource_id": resource_id,
                "category": category,
            },
        )
        await self.statemgr.insert(message_category)

    @action("message-recipient-get", resources="message")
    async def get_message_recipient(self, *, message_id: str):
        """Action to get a message recipient."""
        message_recipient = await self.statemgr.find_one(
            "message_recipient",
            where={"message_id": message_id, "recipient_id": self.context.profile_id},
        )
        return message_recipient

    @action("message-content-processed", resources="message")
    async def process_message_content(
        self,
        *,
        message_id: str,
        context: Optional[Dict[str, Any]] = None,
        mode: str = "sync",
    ):
        """Process message content (template resolution and rendering)."""
        message = await self.statemgr.fetch("message", message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")

        processing_mode = ProcessingModeEnum(mode)

        # Process content
        processed_message = await self.content_processor.process_message_content(
            message, mode=processing_mode, context=context or {}
        )

        return processed_message

    @action("message-ready-for-delivery", resources="message")
    async def mark_ready_for_delivery(self, message_id):
        """Mark message as ready for delivery."""
        message = await self.statemgr.fetch("message", message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")

        if message.render_status.value not in [
            RenderStatusEnum.COMPLETED.value,
            RenderStatusEnum.CLIENT_RENDERING.value,
        ]:
            raise ValueError(
                f"Message {message_id} is not ready for delivery (status: {message.render_status})"
            )

        await self.statemgr.update(message, delivery_status="PENDING")

        return {"message_id": message_id, "status": "PENDING"}

    @action("recipients-added", resources=("message", "message_recipient"))
    async def add_recipients(self, *, data, message_id):
        """Action to add recipients to a message."""
        recipients = data
        # Get the inbox box
        inbox = await self.statemgr.find_one(
            "message_box",
            where={"key": "inbox"},
        )

        records = []
        for recipient_id in recipients:
            recipient_data = {
                "message_id": message_id,
                "recipient_id": recipient_id,
                "read": False,
                "box_id": inbox._id,
                "direction": "INBOUND",
            }

            recipient = self.init_resource("message_recipient", recipient_data)
            records.append(serialize_mapping(recipient))

        await self.statemgr.insert_data("message_recipient", *records)

        return {"message_id": message_id, "recipients_count": len(recipients)}

    @action("sender-added", resources=("message", "message_sender"))
    async def add_sender(self, *, message_id, sender_id):
        """Action to add sender to a message."""
        # Get the outbox box
        outbox = await self.statemgr.find_one(
            "message_box",
            where={"key": "outbox"},
        )

        sender_data = {
            "message_id": message_id,
            "sender_id": sender_id,
            "box_id": outbox._id,
            "direction": "OUTBOUND",
        }

        sender = self.init_resource("message_sender", sender_data)
        await self.statemgr.insert(sender)

        return {"message_id": message_id, "sender_id": sender_id}

    @action("message-read", resources="message")
    async def mark_message_read(self):
        """Action to mark a message as read for a specific user."""
        # Find the recipient record
        message = self.rootobj
        message_recipient = await self.statemgr.find_one(
            "message_recipient",
            where={"message_id": message._id, "recipient_id": self.context.profile_id},
        )
        await self.statemgr.update(
            message_recipient, read=True, mark_as_read=timestamp()
        )

    @action("all-messages-read", resources="message")
    async def mark_all_messages_read(self):
        """Action to mark all messages as read for a user."""
        message_recipients = await self.statemgr.find_all(
            "message_recipient",
            where={"recipient_id": self.context.profile_id},
        )

        read_count = 0
        for recipient in message_recipients:
            await self.statemgr.update(recipient, read=True, mark_as_read=timestamp())
            if not recipient.read:
                read_count += 1
        return {"read_count": read_count}

    @action("message-archived", resources="message")
    async def archive_message(self, /, data):
        """Action to archive a message for a specific user."""
        message = self.rootobj
        profile_id = self.context.profile_id

        # Get archived box
        archived_box = await self.statemgr.find_one(
            "message_box",
            where={"key": "archived"},
        )
        message_box_record = await self.statemgr.find_one(
            "_message_box",
            where={"message_id": message._id, "target_profile_id": profile_id},
        )

        if message_box_record.root_type == "RECIPIENT":
            message_recipient = await self.statemgr.fetch(
                "message_recipient", message_box_record._id
            )
            if message_recipient:
                await self.statemgr.update(
                    message_recipient, box_id=archived_box._id
                )
                message_archived = self.init_resource(
                    "message_archived",
                    {
                        "resource": "message_recipient",
                        "resource_id": message_recipient._id,
                        "archived": True,
                    },
                )
                await self.statemgr.insert(message_archived)
        elif message_box_record.root_type == "SENDER":
            message_sender = await self.statemgr.fetch("message_sender", message_box_record._id)
            if message_sender:
                await self.statemgr.update(message_sender, box_id=archived_box._id)
                message_archived = self.init_resource(
                    "message_archived",
                    {
                        "resource": "message",
                        "resource_id": message._id,
                        "archived": True,
                    },
                )
                await self.statemgr.insert(message_archived)

    @action("message-trashed", resources="message")
    async def trash_message(self, /, data):
        """Action to trash a message for a specific user."""
        message = self.rootobj
        profile_id = self.context.profile_id

        # Get trashed box
        trashed_box = await self.statemgr.find_one(
            "message_box",
            where={"key": "trashed"},
        )

        message_box_record = await self.statemgr.find_one(
            "_message_box",
            where={"message_id": message._id, "target_profile_id": profile_id},
        )


        if message_box_record.root_type == "RECIPIENT":
            message_recipient = await self.statemgr.fetch(
                "message_recipient", message_box_record._id
            )
            if message_recipient:
                await self.statemgr.update(
                    message_recipient, box_id=trashed_box._id
                )
                message_trashed = self.init_resource(
                    "message_trashed",
                    {
                        "resource": "message_recipient",
                        "resource_id": message_recipient._id,
                        "trashed": True,
                    },
                )
                await self.statemgr.insert(message_trashed)
        elif message_box_record.root_type == "SENDER":
            message_sender = await self.statemgr.fetch("message_sender", message_box_record._id)
            if message_sender:
                await self.statemgr.update(message_sender, box_id=trashed_box._id)
                message_trashed = self.init_resource(
                    "message_trashed",
                    {
                        "resource": "message",
                        "resource_id": message._id,
                        "trashed": True,
                    },
                )
                await self.statemgr.insert(message_trashed)

    @action("message-restored", resources="message")
    async def restore_message(self, /, data):
        """Action to restore a message to inbox/outbox for a specific user."""
        message = self.rootobj
        profile_id = self.context.profile_id

        message_box_record = await self.statemgr.find_one(
            "_message_box",
            where={"message_id": message._id, "target_profile_id": profile_id},
        )

        if message_box_record.root_type == "RECIPIENT":
            inbox_box = await self.statemgr.find_one(
                "message_box",
                where={"key": "inbox"},
            )
            message_recipient = await self.statemgr.fetch(
                "message_recipient", message_box_record._id
            )
            if message_recipient:
                await self.statemgr.update(message_recipient, box_id=inbox_box._id)
        elif message_box_record.root_type == "SENDER":
            outbox_box = await self.statemgr.find_one(
                "message_box",
                where={"key": "outbox"},
            )
            message_sender = await self.statemgr.fetch(
                "message_sender", message_box_record._id
            )
            if message_sender:
                await self.statemgr.update(message_sender, box_id=outbox_box._id)

    # ========================================================================
    # TEMPLATE OPERATIONS
    # ========================================================================

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
