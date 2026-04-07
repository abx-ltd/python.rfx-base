from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR, UUID_TYPE
from fluvius.error import BadRequestError
from typing import Optional, Dict, Any
from .types import RenderStatusEnum

class RFX2DMessageAggregate(Aggregate):
    def _normalize_member_ids(self, sender_id, recipients=None):
        """Build a unique ordered member list from sender and recipients."""
        member_ids = [sender_id, *(recipients or [])]
        return [member_id for member_id in dict.fromkeys(member_ids) if member_id]

    async def find_members_by_box_id(self, box_id, member_ids):
        """Check whether the box contains exactly the requested members."""
        memberships = await self.statemgr.find_all(
            "message_box_user",
            where={"box_id": box_id},
        )
        box_member_ids = {membership.user_id for membership in memberships}
        return box_member_ids == set(member_ids)

    async def get_or_create_member_box(self, sender_id, recipients=None):
        """Get an existing exact-match member box or create a new one."""
        unique_member_ids = self._normalize_member_ids(sender_id, recipients)

        sender_box_users = await self.statemgr.find_all(
            "message_box_user",
            where={"user_id": sender_id},
        )

        for box_user in sender_box_users:
            if await self.find_members_by_box_id(box_user.box_id, unique_member_ids):
                return await self.statemgr.find_one(
                    "message_box",
                    where={"_id": box_user.box_id},
                )

        box_type = "GROUP" if len(unique_member_ids) >= 2 else "SINGLE"
        box = self.init_resource(
            "message_box",
            {"name": None, "key": None, "type": box_type},
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(box)

        box_users = []
        for member_id in unique_member_ids:
            box_user = self.init_resource(
                "message_box_user",
                {"user_id": member_id, "box_id": box._id},
                _id=UUID_GENR(),
            )
            box_users.append(serialize_mapping(box_user))

        await self.statemgr.insert_data("message_box_user", *box_users)
        return box
    
    @action("get-message-sender-by-message-id", resources="message")
    async def get_message_sender_by_message_id(self, message_id):
        """Get message sender by message id."""
        return await self.statemgr.find_one(
            "message_sender",
            where={"message_id": message_id},
        )
    
    @action("get-message-recipient", resources="message")
    async def get_message_recipient(self, message_id, profile_id):
        """Get message recipient."""
        return await self.statemgr.find_one(
            "message_recipient",
            where={"message_id": message_id, "recipient_id": profile_id},
        )
    
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
            parent_id=message._id,
        )

        await self.statemgr.insert(reply_message)

        return reply_message

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

        # If message has direct content, no template rendering needed
        if message.content:
            await self.statemgr.update(
                message,
                render_status=RenderStatusEnum.COMPLETED.value
            )
            return serialize_mapping(message)

        # If message has template_key, render via rfx-template domain
        if message.template_key:
            try:
                from rfx_user import config as userconf
                template_client = getattr(self.context.service_proxy, userconf.SERVICE_CLIENT, None)
                if not template_client:
                    raise RuntimeError("Template client not found")

                # Call rfx-template:render-template
                response = await template_client.request(
                    "rfx-template:render-template",
                    command="render-template",
                    resource="template",
                    payload={
                        "key": message.template_key,
                        "data": context or {},
                        "tenant_id": str(self.context.tenant_id) if hasattr(self.context, 'tenant_id') else None,
                        "app_id": getattr(self.context, 'app_id', None),
                        "locale": message.locale or "en",
                        "channel": message.channel,
                    },
                    _headers={},
                    _context={
                        "audit": {
                            "user_id": str(self.context.user_id) if self.context.user_id else None,
                            "profile_id": str(self.context.profile_id) if self.context.profile_id else None,
                        },
                        "source": "rfx-message",
                    },
                )

                # Extract rendered content from template-service-response
                service_response = response.get("template-service-response", response)
                rendered_content = service_response.get('body', '')

                # Update message with rendered content
                await self.statemgr.update(
                    message,
                    content=rendered_content,
                    render_status=RenderStatusEnum.COMPLETED.value
                )

                # Refetch updated message
                message = await self.statemgr.fetch("message", message_id)

            except Exception as e:
                # Mark rendering as failed
                await self.statemgr.update(
                    message,
                    render_status=RenderStatusEnum.FAILED.value,
                    render_error=str(e)
                )
                raise ValueError(f"Template rendering failed: {str(e)}")

        return serialize_mapping(message)

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

    # @action("get-all-message-in-thread-from-message", resources="message")
    # async def get_all_message_view_in_thread_from_message(self, message_id):
    #     """Get all messages in a thread."""
    #     message = self.rootobj
    #     return await self.statemgr.find_all(
    #         "_message_box",
    #         where={"thread_id": message.thread_id},
    #     )

    @action("change-all-sender-box-id-of-same-thread", resources="message")
    async def change_all_sender_box_id_of_same_thread(self, box_id, profile_id):
        """Change all sender box id of same thread."""

        message = self.rootobj
        messages = await self.statemgr.find_all(
            "message",
            where={"thread_id": message.thread_id},
        )
        for message in messages:
            sender = await self.statemgr.exist(
                "message_sender",
                where={"message_id": message._id, "sender_id": profile_id},
            )
            if sender:
                await self.statemgr.update(sender, box_id=box_id)

    @action("change-all-recipient-box-id-of-same-thread", resources="message")
    async def change_all_recipient_box_id_of_same_thread(self, box_id, profile_id):
        """Change all recipient box id of same thread."""
        message = self.rootobj
        messages = await self.statemgr.find_all(
            "message",
            where={"thread_id": message.thread_id},
        )
        for message in messages:
            recipient = await self.statemgr.exist(
                "message_recipient",
                where={"message_id": message._id, "recipient_id": profile_id},
            )
            if recipient:
                await self.statemgr.update(recipient, box_id=box_id)
    

    @action("sender-added", resources=("message", "message_sender"))
    async def add_sender(self, *, message_id, sender_id, recipients):
        """Action to add sender to a message."""
        box = await self.get_or_create_member_box(sender_id=sender_id, recipients=recipients)

        sender_data = {
            "message_id": message_id,
            "sender_id": sender_id,
            "box_id": box._id,
            "direction": "OUTBOUND",
        }

        sender = self.init_resource("message_sender", sender_data)
        await self.statemgr.insert(sender)

        return {"message_id": message_id, "sender_id": sender_id, "box_id": box._id}
    
    @action("recipients-added", resources=("message", "message_recipient"))
    async def add_recipients(self, *, data, message_id, box_id):
        """Action to add recipients to a message."""
        recipients = data

        records = []
        for recipient_id in recipients:
            recipient_data = {
                "message_id": message_id,
                "recipient_id": recipient_id,
                "read": False,
                "box_id": box_id,
                "direction": "INBOUND",
            }

            if self.get_context().profile_id == recipient_id:
                recipient_data["read"] = True
                recipient_data["direction"] = "OUTBOUND"

            recipient = self.init_resource("message_recipient", recipient_data)
            records.append(serialize_mapping(recipient))

        await self.statemgr.insert_data("message_recipient", *records)

        return {"message_id": message_id, "recipients_count": len(recipients)}

    @action("remove-message-sender", resources="message")
    async def remove_message_sender(self, message_id, profile_id):
        """Remove message sender."""
        message_sender = await self.statemgr.find_one(
            "message_sender",
            where={"message_id": message_id, "sender_id": profile_id},
        )
        await self.statemgr.invalidate(message_sender)

    @action("remove-message-recipient", resources="message")
    async def remove_message_recipient(self, message_id, profile_id):
        """Remove message recipient."""

        message_recipient = await self.statemgr.find_one(
            "message_recipient",
            where={"message_id": message_id, "recipient_id": profile_id},
        )
        await self.statemgr.invalidate(message_recipient)

    @action("update-message-sender", resources="message")
    async def update_message_sender(self, message_id, profile_id, data):
        """Update message sender"""

        message_sender = await self.statemgr.find_one(
            "message_sender",
            where={"message_id": message_id, "sender_id": profile_id},
        )
        
        is_archived = None
        is_starred = None
        if data.is_archived is not None:
            is_archived = data.is_archived
            await self.statemgr.update(message_sender, is_archived=is_archived)
        
        if data.is_starred is not None:
            is_starred = data.is_starred
            await self.statemgr.update(message_sender, is_starred=is_starred)

        # message_sender_updated = await self.statemgr.fetch("message_sender", message_sender._id)
        # return

    @action("update-message-recipient", resources="message")
    async def update_message_recipient(self, message_id, profile_id, data):
        """Update message recipient"""

        message_recipient = await self.statemgr.find_one(
            "message_recipient",
            where={"message_id": message_id, "recipient_id": profile_id},
        )

        is_archived = None
        is_starred = None
        if data.is_archived is not None:
            is_archived = data.is_archived
            await self.statemgr.update(message_recipient, is_archived=is_archived)
        
        if data.is_starred is not None:
            is_starred = data.is_starred
            await self.statemgr.update(message_recipient, is_starred=is_starred)

        # message_recipient_updated = await self.statemgr.fetch("message_sender", message_recipient._id)

    @action("tag-created", resources="tag")
    async def create_tag(self, *, data):
        """Create a new tag."""
        tag = self.init_resource(
            "tag",
            serialize_mapping(data),
            _id=UUID_GENR(),
            profile_id=self.get_context().profile_id,
        )
        await self.statemgr.insert(tag)
        return tag

    @action("tag-updated", resources="tag")
    async def update_tag(self, *, data):
        """Update a tag."""
        tag = self.rootobj
        await self.statemgr.update(tag, **serialize_mapping(data))

    @action("tag-removed", resources="tag")
    async def remove_tag(self):
        """Remove a tag."""
        tag = self.rootobj
        await self.statemgr.invalidate(tag)

    @action("add-message-tag", resources="message")
    async def add_message_tag(
        self, *, resource: str, resource_id: str, tag_id: UUID_TYPE
    ):
        """Action to add a tag to a message."""
        existing_tag = await self.statemgr.exist(
            "message_tag",
            where={"resource": resource, "resource_id": resource_id, "tag_id": tag_id},
        )
        if existing_tag:
            return

   
        message_tag = self.init_resource(
            "message_tag",
            {
                "resource": resource,
                "resource_id": resource_id,
                "tag_id": tag_id,
            },
        )
        await self.statemgr.insert(message_tag)

    @action("message-tag-removed-from-resource", resources="message")
    async def remove_message_tag_from_resource(
        self, *, resource: str, resource_id: str, tag_id: UUID_TYPE
    ):
        """Action to remove a tag from a message."""
        message_tag = await self.statemgr.find_one(
            "message_tag",
            where={"resource": resource, "resource_id": resource_id, "tag_id": tag_id},
        )
        await self.statemgr.invalidate(message_tag)

    @action("create-category", resources="category")
    async def create_category(self, data, profile_id):

        
        category = self.init_resource(
            "category",
            serialize_mapping(data),
            _id=UUID_GENR(),
            profile_id=profile_id    
        )

        await self.statemgr.insert(category)

        return category

    @action("remove-category", resources="category")
    async def remove_category(self, category_id, profile_id):
        # Remove category by category_id and profile_id
        category = await self.statemgr.find_one(
            "category",
            where={"_id": category_id, "profile_id": profile_id},
        )
        await self.statemgr.invalidate(category)

        # Delete all message-category associations for this category
        message_category = await self.statemgr.find_all(
            "message_category",
            where={"category_id": category_id}
        )
        for mc in message_category:
            await self.statemgr.invalidate(mc)

    @action("create-mailbox", resources="mailbox")
    async def create_mailbox(self, data, profile_id):
        mailbox = self.init_resource(
            "mailbox",
            serialize_mapping(data),
            _id=UUID_GENR(),
            profile_id=profile_id,
        )

        await self.statemgr.insert(mailbox)

        return mailbox

    @action("remove-mailbox", resources="mailbox")
    async def remove_mailbox(self, mailbox_id, profile_id):
        mailbox = await self.statemgr.find_one(
            "mailbox",
            where={"_id": mailbox_id, "profile_id": profile_id},
        )
        await self.statemgr.invalidate(mailbox)

        mailbox_messages = await self.statemgr.find_all(
            "mailbox_message",
            where={"mailbox_id": mailbox_id},
        )
        for m in mailbox_messages:
            await self.statemgr.invalidate(m)

        return mailbox

    # @action("create-mailbox-message", resources="mailbox")
    # async def create_mailbox_message(self, data, mailbox_id, profile_id):
    #     message_id = data.get("message_id")
    #     if not message_id:
    #         raise BadRequestError("D00.452", "message_id is required for mailbox_message")

    #     source = data.get("source")
    #     source_id = data.get("source_id")
    #     if source and source_id:
    #         existing = await self.statemgr.exist(
    #             "mailbox_message",
    #             where={"mailbox_id": mailbox_id, "source": source, "source_id": source_id, "_deleted": None},
    #         )
    #         if existing:
    #             raise BadRequestError(
    #                 "D00.451",
    #                 f"Mailbox message already exists for source={source} source_id={source_id}"
    #             )

    #     mailbox_message = self.init_resource(
    #         "mailbox_message",
    #         serialize_mapping(data),
    #         _id=UUID_GENR(),
    #         mailbox_id=mailbox_id,
    #         profile_id=profile_id,
    #     )

    #     await self.statemgr.insert(mailbox_message)

    #     return mailbox_message

    # @action("remove-mailbox-message", resources="mailbox")
    # async def remove_mailbox_message(self, mailbox_message_id, profile_id):
    #     mailbox_message = await self.statemgr.find_one(
    #         "mailbox_message",
    #         where={"_id": mailbox_message_id, "profile_id": profile_id},
    #     )
    #     await self.statemgr.invalidate(mailbox_message)

    #     return mailbox_message

    @action("add-message-to-category", resources="category")
    async def add_message_to_category(self, data, category_id, profile_id):
        messages = data.pop("message_id", [])

        categories = await self.statemgr.find_all(
            "category",
            where={"profile_id": profile_id, "_deleted": None},
        )

        message_category_exists = []
        
        for message_id in messages:
            # Check if message is already in any category for this profile (non-deleted)
            # First, find all categories for this profile
            mc_exist = False
            for cat in categories:
                # Then check if message is associated with any of these categories
                existing_mc = await self.statemgr.exist(
                    "message_category",
                    where={"message_id": message_id, "category_id": cat._id, "_deleted": None},
                )
                if existing_mc:
                    message_category_exists.append(message_id)
                    mc_exist = True
                    break
                    # raise BadRequestError("D00.450", f"Message {message_id} is already assigned to a category for this profile. A message can only belong to one category per profile.")

            if mc_exist:
                continue

            mc_data = self.init_resource(
                "message_category",
                _id=UUID_GENR(),
                message_id=message_id,
                category_id=category_id
            )

            await self.statemgr.insert(mc_data)
        
        if len(message_category_exists) > 0:
            return {
                "message_category_exists": message_category_exists,
                "message_category_added": list(set(messages) - set(message_category_exists))
            }
        else:
            return {
                "message_category_added": messages
            }
        
    # @action("remove-message-from-category", resource="category")
    # async def 