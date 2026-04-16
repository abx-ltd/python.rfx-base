from pyexpat.errors import messages
from httpx import AsyncClient
from datetime import datetime

from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR, UUID_TYPE
from fluvius.error import BadRequestError
from typing import Optional, Dict, Any
from .types import RenderStatusEnum, PriorityLevelEnum, ActionExecutionStatus, ActionTypeEnum, ExecutionModeEnum

class RFX2DMessageAggregate(Aggregate):
    @action("get-all-member-in-mailbox", resources="message")
    async def get_all_members_in_mailbox(self, *, mailbox_id):
        """Get all members in a mailbox."""
        members = await self.statemgr.find_all(
            "mailbox_member",
            where={"mailbox_id": mailbox_id}
        )
        return members

    @action("check-owner-contributor-mailboxes", resources="message")
    async def check_owner_contributor_mailbox(self, *, mailbox_id, profile_id):
        """Check if a profile is the owner or contributor of a mailbox."""
        mailbox_member = await self.statemgr.find_one(
            "mailbox_member",
            where={"mailbox_id": mailbox_id,"member_id": profile_id})   
        
        if mailbox_member.role == "VIEWER":
            raise ValueError(f"Profile {profile_id} is not the owner of mailbox {mailbox_id}.")
        
        return mailbox_member


    @action("message-generated", resources="message")
    async def generate_message(self, *, data, mailbox_id):
        """Action to create a new message."""
        message_data = data

        message = self.init_resource(
            "message",
            message_data,
            _id=UUID_GENR(),
            sender_mailbox_id=mailbox_id,
        )

        await self.statemgr.insert(message)

        return message

    @action("sender-added", resources=("message", "message_sender"))
    async def add_sender(self, message_id, sender_id):
        """Action to add sender to a message."""
        sender_data = {
            "message_id": message_id,
            "sender_id": sender_id,
            "direction": "OUTBOUND",
        }

        sender = self.init_resource("message_sender", sender_data)
        await self.statemgr.insert(sender)

        return {"message_id": message_id, "sender_id": sender_id}
    
    @action("recipients-added", resources=("message"))
    async def add_message_recipient(self, message_id, mailbox_id):
        message_recipient = self.init_resource(
            "message_recipient",
            {
                "message_id": message_id,
                "mailbox_id": mailbox_id,
            },
            _id=UUID_GENR(),
        )

        await self.statemgr.insert(message_recipient)
    
    @action("message-recipient-assign", resources=("message"))
    async def assign_message_recipient(self, recipients, message_id, mailbox_id):
        """Create message_recipient and message_mailbox_state records for each recipient."""

        # Then, create message_mailbox_state records for each recipient
        for recipient_id in recipients:
            mailbox_state = self.init_resource(
                "message_mailbox_state", 
                {
                    "message_id": message_id,
                    "mailbox_id": mailbox_id,
                    "assigned_to_profile_id": recipient_id,
                    "read": False,
                    "folder": "inbox",
                    "is_starred": False,
                    "status": "NEW",
                },
                _id=UUID_GENR(),
            )
            await self.statemgr.insert(mailbox_state)

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

    @action("message-assigned", resources="message")
    async def assign_message(self, message_id, mailbox_id, assignee_profile_id, reason=None):
        """Assign message handling for a mailbox."""
        message_mailbox_state_exist = await self.statemgr.exist(
            "message_mailbox_state",
            where={"message_id": message_id, "mailbox_id": mailbox_id, "assigned_to_profile_id": assignee_profile_id, "_deleted": None}
        )
        if message_mailbox_state_exist:
            raise ValueError(f"Message {message_id} in mailbox {mailbox_id} is already assigned to profile {assignee_profile_id}.")

        mailbox_state = self.init_resource(
            "message_mailbox_state",
            {
                "mailbox_id": mailbox_id,
                "message_id": message_id,
                "folder": "INBOX",
                "is_starred": False,
                "assigned_to_profile_id": assignee_profile_id,
                "status": "NEW"
            },
            _id=UUID_GENR(),
        )

        await self.statemgr.insert(mailbox_state,)

        return {
            "message_id": message_id,
            "mailbox_id": mailbox_id,
            "assigned_to_profile_id": assignee_profile_id,
            "reason": reason,
        }

    @action("message-status-updated", resources="message")
    async def set_message_status(self, message_id, message_status, mailbox_id, profile_id):
        """Update the canonical status of a message."""

        message = await self.statemgr.find_one(
            "message_mailbox_state",
            where={"mailbox_id": mailbox_id, "message_id": message_id, "assigned_to_profile_id": profile_id},
        )
        if message is None:
            raise ValueError("D00.461", f"Message not found: {message_id}")

        await self.statemgr.update(message, status=message_status)

        return {"message_id": message_id, "message_status": message_status}

    @action("message-moved", resources="message")
    async def move_message(self, message_id, mailbox_id, folder, profile_id):
        """Move a message into a mailbox folder."""

        folder_value = folder.strip().lower()
        if folder_value not in ("inbox", "starred", "archived", "trash"):
            raise ValueError(
                "D00.462",
                f"Unsupported folder: {folder}. Supported folders are inbox, starred, archived, and trash.",
            )

        mailbox_state = await self.statemgr.find_one(
            "message_mailbox_state",
            where={"message_id": message_id, "mailbox_id": mailbox_id, "assigned_to_profile_id": profile_id, "_deleted": None},
        )
        if mailbox_state is None:
            raise ValueError(
                "D00.463",
                f"Message {message_id} is not present in mailbox {mailbox_id}.",
            )

        await self.statemgr.update(mailbox_state, folder=folder_value)
        return {"message_id": message_id, "mailbox_id": mailbox_id, "folder": folder_value}

    @action("message-star-updated", resources="message")
    async def set_message_star(self, message_id, mailbox_id, starred, profile_id):
        """Toggle starred state for a message within a mailbox."""

        mailbox_state = await self.statemgr.find_one(
            "message_mailbox_state",
            where={"message_id": message_id, "mailbox_id": mailbox_id, "assigned_to_profile_id": profile_id, "_deleted": None},
        )
        if mailbox_state is None:
            raise ValueError(
                "D00.464",
                f"Message {message_id} is not present in mailbox {mailbox_id}.",
            )

        await self.statemgr.update(mailbox_state, is_starred=starred)
        return {"message_id": message_id, "mailbox_id": mailbox_id, "is_starred": starred}

    @action("message-priority-updated", resources="message")
    async def set_priority(self, message_id, priority, profile_id):
        """Update a message priority."""

        # Check if message is sent by profile_id
        # message = await self.statemgr.find_one(
        #     "message_sender",
        #     where={"message_id": message_id, "sender_id": profile_id},
        # )
        # if message is None:
        #     raise ValueError("D00.466", f"Message not found or not sent by profile: {message_id}")

        if isinstance(priority, str):
            priority = priority.strip().upper()

        if priority not in {p.value for p in PriorityLevelEnum}:
            raise ValueError(
                "D00.465",
                f"Unsupported priority: {priority}. Supported values are HIGH, MEDIUM, LOW.",
            )

        message = await self.statemgr.find_one(
            "message",
            where={"_id": message_id},
        )
        if message is None:
            raise ValueError("D00.466", f"Message not found: {message_id}")

        await self.statemgr.update(message, priority=priority)
        return {"message_id": message_id, "priority": priority}

    @action("message-related-linked", resources="message")
    async def link_related_message(self, message_id, related_message_id, link_type="related"):
        """Link two messages as related."""

        existing = await self.statemgr.exist(
            "message_reference",
            where={
                "message_id": message_id,
                "resource": "message",
                "resource_id": related_message_id,
                "kind": link_type,
                "_deleted": None,
            },
        )
        if existing:
            return {
                "message_id": message_id,
                "related_message_id": related_message_id,
                "link_type": link_type,
                "linked": False,
            }

        message_reference = self.init_resource(
            "message_reference",
            {
                "message_id": message_id,
                "resource": "message",
                "resource_id": related_message_id,
                "kind": link_type,
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(message_reference)

        reverse_exists = await self.statemgr.exist(
            "message_reference",
            where={
                "message_id": related_message_id,
                "resource": "message",
                "resource_id": message_id,
                "kind": link_type,
                "_deleted": None,
            },
        )
        if not reverse_exists:
            reverse_reference = self.init_resource(
                "message_reference",
                {
                    "message_id": related_message_id,
                    "resource": "message",
                    "resource_id": message_id,
                    "kind": link_type,
                },
                _id=UUID_GENR(),
            )
            await self.statemgr.insert(reverse_reference)

        return {
            "message_id": message_id,
            "related_message_id": related_message_id,
            "link_type": link_type,
            "linked": True,
        }

    @action("attachment-metadata-uploaded", resources="message")
    async def upload_attachment_metadata(self, message_id, data):
        """Register uploaded attachment metadata for a message."""

        # Check if message is sent by profile_id
        # message = await self.statemgr.find_one(
        #     "message_sender",
        #     where={"message_id": message_id, "sender_id": profile_id},
        # )
        # if message is None:
        #     raise ValueError("D00.466", f"Message not found or not sent by profile: {message_id}")

        attachment = self.init_resource(
            "message_attachment",
            {
                "message_id": message_id,
                "file_id": getattr(data, "file_id", None),
                "file_name": data.filename,
                "storage_key": data.storage_key,
                "media_type": data.media_type,
                "size_bytes": data.size_bytes,
                "checksum": data.checksum,
                "download_policy": getattr(data, "download_policy", None),
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(attachment)

        return serialize_mapping(attachment)

    @action("tag-created", resources="tag")
    async def create_tag(self, *, data):
        """Create a new tag."""
        tag = self.init_resource(
            "tag",
            serialize_mapping(data),
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(tag)
        return tag

    @action("tag-updated", resources="tag")
    async def update_tag(self, *, data):
        """Update a tag."""
        tag = self.rootobj
        tag_result = await self.statemgr.update(tag, **serialize_mapping(data))

        return tag_result

    @action("tag-removed", resources="tag")
    async def remove_tag(self, tag_id):
        """Remove a tag."""
        tag = await self.statemgr.find_one(
            "tag",
            where={"_id": tag_id},
        )
        await self.statemgr.invalidate(tag)

    @action("message-tag-removed-by-tag", resources="tag")
    async def remove_message_tag_from_tag(self, tag_id):
        """Remove all message tags associated with a tag."""
        message_tags = await self.statemgr.find_all(
            "message_tag",
            where={"tag_id": tag_id},
        )
        for message_tag in message_tags:
            await self.statemgr.invalidate(message_tag)

    @action("add-message-tag", resources="message")
    async def add_message_tag(
        self, tag_ids, message_id
    ):
        """Action to add a tag to a message."""
        for tag_id in tag_ids:
            message_tag = self.init_resource(
                "message_tag",
                {
                    "tag_id": tag_id,
                    "message_id": message_id,
                },
            )
            await self.statemgr.insert(message_tag)

    @action("message-tag-removed", resources="message")
    async def remove_message_tag(self, message_id, tag_ids):
        """Action to remove a tag from a message."""
        for tag_id in tag_ids:
            message_tag = await self.statemgr.find_one(
                "message_tag",
                where={"message_id": message_id, "tag_id": tag_id},
            )
            await self.statemgr.invalidate(message_tag)

    @action("create-category", resources="category")
    async def create_category(self, data, profile_id):
        category = self.init_resource(
            "category",
            serialize_mapping(data),
            _id=UUID_GENR(),
        )

        await self.statemgr.insert(category)

        return category

    @action("remove-category", resources="category")
    async def remove_category(self, category_id, profile_id):
        # Delete all message-category associations for this category
        messages = await self.statemgr.find_all(
            "message",
            where={"category_id": category_id}
        )
        for message in messages:
            await self.statemgr.update(message, category_id=None)

        # Remove category by category_id
        category = await self.statemgr.find_one(
            "category",
            where={"_id": category_id},
        )
        await self.statemgr.invalidate(category)

    # ======================================================
    # MAILBOX METHODS
    # ======================================================

    @action("create-mailbox", resources="mailbox")
    async def create_mailbox(self, data, profile_id):
        profile_ids = data.get("profile_ids", [])
        profile_ids.append(profile_id)  # Ensure creator always has access

        mailbox_record = self.init_resource(
            "mailbox",
            _id=UUID_GENR(),
            name=data.get("name"),
            profile_id=profile_id,
            telecom_phone=data.get("telecom_phone"),
            telecom_email=data.get("telecom_email"),
            description=data.get("description"),
            url=data.get("url"),
            mailbox_type=data.get("mailbox_type"),
        )

        await self.statemgr.insert(mailbox_record)

        for pid in profile_ids:
            if pid != profile_id:
                mailbox_member = self.init_resource(
                    "mailbox_member",
                    _id=UUID_GENR(),
                    mailbox_id=mailbox_record._id, 
                    member_id=pid,
                    role="VIEWER"
                )
                await self.statemgr.insert(mailbox_member)
            else:
                mailbox_member = self.init_resource(
                    "mailbox_member",
                    _id=UUID_GENR(),
                    mailbox_id=mailbox_record._id, 
                    member_id=pid,
                    role="OWNER"
                )
                await self.statemgr.insert(mailbox_member)

        return mailbox_record

    @action("remove-mailbox", resources="mailbox")
    async def remove_mailbox(self, mailbox_id, profile_id):
        mailbox_member = await self.statemgr.find_one(
            "mailbox_member",
            where={"mailbox_id": mailbox_id, "profile_id": profile_id},
        )

        if mailbox_member is None:
            raise ValueError("Mailbox not found or access denied")
        
        # if the user is not the owner, just invalidate their membership. If they are the owner, invalidate all memberships and the mailbox itself.
        if mailbox_member.role != "OWNER":
            await self.statemgr.invalidate(mailbox_member)
        else:
            mailbox_members = await self.statemgr.find_all(
                "mailbox_member",
                where={"mailbox_id": mailbox_id},
            )
            for member in mailbox_members:
                await self.statemgr.invalidate(member)
        
            mailbox = await self.statemgr.find_one(
                "mailbox",
                where={"_id": mailbox_id, "profile_id": profile_id},
            )
            await self.statemgr.invalidate(mailbox)

        # mailbox_messages = await self.statemgr.find_all(
        #     "message_mailbox_state",
        #     where={"mailbox_id": mailbox_id},
        # )
        # for m in mailbox_messages:
        #     await self.statemgr.invalidate(m)

        return mailbox
    
    @action("add-member-to-mailbox", resources="mailbox")
    async def add_member_to_mailbox(self, mailbox_id, profile_id, member_added_ids):

        # check if profile_id is owner of the mailbox
        mailbox_owner = await self.statemgr.find_one(
            "mailbox_member",
            where={"mailbox_id": mailbox_id, "member_id": profile_id, "role": "OWNER"},
        )
        if mailbox_owner is None:
            raise ValueError("Only mailbox owner can add members")
        
        for member_id in member_added_ids:
            # check if member added is already a member of the mailbox
            mailbox_member_exists = await self.statemgr.exist(
                "mailbox_member",
                where={"mailbox_id": mailbox_id, "member_id": member_id},
            )
            if mailbox_member_exists:    
                member_added_ids.remove(mailbox_member_exists.member_id)        
                continue

            mailbox_member = self.init_resource(
                "mailbox_member",
                _id=UUID_GENR(),
                mailbox_id=mailbox_id,
                member_id=member_id,
                role="VIEWER"
            )

            await self.statemgr.insert(mailbox_member)
        
        await self.sync_to_message_mailbox_state(mailbox_id, member_added_ids, True)

    # @action("remove-mailbox-message", resources="mailbox")
    # async def remove_mailbox_message(self, mailbox_message_id, profile_id):
    #     mailbox_message = await self.statemgr.find_one(
    #         "message_mailbox_state",
    #         where={"_id": mailbox_message_id, "profile_id": profile_id},
    #     )
    #     await self.statemgr.invalidate(mailbox_message)

    #     return mailbox_message

    @action("add-message-to-category", resources="category")
    async def add_message_to_category(self, mailbox_id, category_id, message_ids):
        message_category_exist = []
        for message_id in message_ids:
            message = await self.statemgr.find_one(
                "message",
                where={"_id": message_id,"sender_mailbox_id": mailbox_id, "_deleted": None},
            )
            if message.category_id is None:
                await self.statemgr.update(message, category_id=category_id)
            else:
                message_category_exist.append(message_id)
        
        return {
            "message_category": category_id,
            "message_category_exist": message_category_exist,
            "message_category_added": list(set(message_ids) - set(message_category_exist))
        }
        
    @action("remove-message-from-category", resources="category")
    async def remove_message_from_category(self, mailbox_id, category_id, profile_id, message_ids):
        for message_id in message_ids:
            message = await self.statemgr.find_one(
                "message",
                where={"_id": message_id, "_deleted": None},
            )
            if message:
                await self.statemgr.update(message, category_id=None)
        
    async def sync_to_message_mailbox_state(self, mailbox_id, member_ids, add):
        """
            Sync message mailbox state for messages in the mailbox.
            If have new member added to the mailbox, add message mailbox state for the member for all messages in the mailbox.
            If have member removed from the mailbox, remove message mailbox state for the member for all messages in the mailbox.   
        """
        # This is a placeholder for the actual implementation of syncing message mailbox state.
        # The actual implementation would depend on the specific requirements and data model of the application.
        all_message_of_mailbox = await self.statemgr.find_all(
            "message",
            where={"sender_mailbox_id": mailbox_id, "_deleted": None},
        )

        if add == False:
            for member_id in member_ids:
                message_mailbox_states = await self.statemgr.find_all(
                    "message_mailbox_state",
                    where={"mailbox_id": mailbox_id, "_deleted": None, "assigned_to_profile_id": member_id},
                )
                for message in message_mailbox_states:
                    await self.statemgr.invalidate(message)
        else:
            for member_id in member_ids:
                # find all messages in the mailbox
                for message in all_message_of_mailbox:
                    new_message_mailbox_state = self.init_resource(
                        "message_mailbox_state",
                        _id=UUID_GENR(),
                        mailbox_id=mailbox_id,
                        message_id=message._id,
                        assigned_to_profile_id=member_id,
                    )
                    await self.statemgr.insert(new_message_mailbox_state)


    # =======================================
    # ACTION METHODS
    # =======================================

    @action("register-action", resources="mailbox")
    async def register_action(self, mailbox_id, action_data, profile_id):
        """Register or update an action definition for a mailbox."""

        # Validate action payload structure
        action_key = action_data["action_key"]
        action_type = action_data["action_type"]
        execution_mode = action_data["execution_mode"]

        # Validate action type and execution mode constraints
        if action_type == ActionTypeEnum.ATOMIC:
            if execution_mode != ExecutionModeEnum.API:
                raise ValueError("Atomic actions must use API execution mode")
            
            if "endpoint" not in action_data:
                raise ValueError("Atomic actions require an endpoint")
            
        elif action_type == ActionTypeEnum.FORM:
            if execution_mode != ExecutionModeEnum.API:
                raise ValueError("Form actions must use API execution mode")
            if "schema" not in action_data:
                raise ValueError("Form actions require a schema")
            if "endpoint" not in action_data:
                raise ValueError("Form actions require an endpoint")
        elif action_type == ActionTypeEnum.EMBEDDED:
            if execution_mode != ExecutionModeEnum.EMBED:
                raise ValueError("Embedded actions must use embed execution mode")
            if "embedded" not in action_data:
                raise ValueError("Embedded actions require embedded content")
        else:
            raise ValueError(f"Invalid action type: {action_type}")

        # Check if action already exists
        existing_action = await self.statemgr.exist(
            "message_action",
            where={
                "mailbox_id": mailbox_id,
                "action_key": action_key,
                "_deleted": None
            }
        )

        if existing_action:
            # # Update existing action
            # action_data["execution_mode"] = ExecutionModeEnum(execution_mode)
            # action_data["action_type"] = ActionTypeEnum(action_type)

            # # Handle nested JSON fields
            # if "endpoint" in execution:
            #     action_data["endpoint_json"] = execution["endpoint"]
            #     action_data["embedded_json"] = None
            # elif "embed" in execution:
            #     action_data["embedded_json"] = execution["embedded"]
            #     action_data["endpoint_json"] = None

            # if "authorization" in execution:
            #     action_data["authorization"] = execution["authorization"]

            # await self.statemgr.update(existing_action, action_data)
            # action = existing_action
            raise ValueError(f"Action with key {action_key} already exists for mailbox {mailbox_id}. Use update action endpoint to modify the action.")
        else:
            # Create new action
            action = self.init_resource(
                "message_action",
                _id=UUID_GENR(),
                mailbox_id=mailbox_id,
                action_key=action_key,
                name=action_data["name"],
                action_type=action_type.value,
                description=action_data.get("description"),
                execution_mode=execution_mode.value,
                endpoint_json=action_data.get("endpoint", None),
                embedded_json=action_data.get("embedded", None),
                authorization=action_data.get("authorization", None),
                schema_json=action_data.get("schema", None),
                response_json=action_data["response"]
            )
            await self.statemgr.insert(action)

        return {
            "action_id": action._id,
            "action_key": action_key,
            "status": "registered"
        }

    @action("execute-atomic-action", resources="message")
    async def execute_atomic_action(self, message_id, action_id, profile_id, mailbox_id):
        """Execute an atomic action for a message."""
        # Get the action definition
        action = await self.statemgr.find_one(
            "message_action",
            where={"_id": action_id, "_deleted": None}
        )
        if not action:
            raise ValueError("Action not found")

        if action.action_type.value != "ATOMIC":
            raise ValueError("Action is not an atomic action")

        # Create action execution record
        execution = self.init_resource(
            "message_action_execute",
            _id=UUID_GENR(),
            message_id=message_id,
            action_id=action_id,
            profile_id=profile_id,
            context_mailbox_id=mailbox_id,
            execution_mode=action.execution_mode,
            status=ActionExecutionStatus.PENDING.value
        )
        await self.statemgr.insert(execution)

        # Execute the action (server-side API call)
        result = await self._execute_action_api(action, {})

        # Update execution record
        status_result = ActionExecutionStatus.COMPLETED.value if result["status"] == "success" else ActionExecutionStatus.FAILED.value
        response_payload_json_result = result
        completed_at = datetime.utcnow()
        await self.statemgr.update(execution,
                                   status=status_result,
                                   response_payload_json=response_payload_json_result,
                                   completed_at=completed_at
                                   )

        return result

    @action("submit-form-action", resources="message")
    async def submit_form_action(self, message_id, action_id, form_data, client_context, profile_id):
        """Submit a form action for a message."""
        # Get the action definition
        action = await self.statemgr.find_one(
            "message_action",
            where={"_id": action_id, "_deleted": None}
        )
        if not action:
            raise ValueError("Action not found")

        if action.action_type.name != "FORM":
            raise ValueError("Action is not a form action")

        # Validate form data against schema
        if action.schema_json:
            await self._validate_form_data(form_data, action.schema_json)

        # Create action execution record
        execution = self.init_resource(
            "message_action_execute",
            _id=UUID_GENR(),
            message_id=message_id,
            action_id=action_id,
            profile_id=profile_id,
            execution_mode=action.execution_mode,
            status=ActionExecutionStatus.PENDING.value,
            input_payload_json=form_data
        )
        await self.statemgr.insert(execution)

        # Execute the action
        result = await self._execute_action_api(action, form_data)

        # Update execution record
        status_result = ActionExecutionStatus.COMPLETED.value if result["status"] == "success" else ActionExecutionStatus.FAILED.value
        response_payload_json_result = result
        completed_at = datetime.utcnow()
        await self.statemgr.update(execution,
                                   status=status_result,
                                   response_payload_json=response_payload_json_result,
                                   completed_at=completed_at)

        return result

    @action("create-action-execution", resources="message")
    async def create_action_execution(self, message_id, action_id, profile_id, mailbox_id):
        """Execute an embedded action for a message (creates pending execution and returns handoff payload)."""
        # Get the action definition
        action = await self.statemgr.find_one(
            "message_action",
            where={"_id": action_id, "_deleted": None}
        )
        if not action:
            raise ValueError("Action not found")

        if action.action_type.value != "EMBEDDED":
            raise ValueError("Action is not an embedded action")

        if action.execution_mode.value != "EMBED":
            raise ValueError("Action execution mode is not EMBED")

        if not action.embedded_json:
            raise ValueError("Embedded action is missing embedded configuration")

        if "url" not in action.embedded_json or not action.embedded_json["url"]:
            raise ValueError("Embedded action has no URL configured")

        callback_method = action.embedded_json.get("callback_method")
        if not callback_method or "mode" not in callback_method:
            raise ValueError("Embedded action callback configuration is missing or invalid")

        # Create action execution record (pending)
        execution_id = UUID_GENR()
        execution = self.init_resource(
            "message_action_execute",
            _id=execution_id,
            message_id=message_id,
            action_id=action_id,
            profile_id=profile_id,
            context_mailbox_id=mailbox_id,
            execution_mode=action.execution_mode,
            status=ActionExecutionStatus.PENDING.value
        )
        await self.statemgr.insert(execution)

        # Build embedded URL with execution_id parameter for backend validation
        base_url = action.embedded_json["url"]
        separator = "&" if "?" in base_url else "?"
        embedded_url = f"{base_url}{separator}execution_id={execution_id}"

        # Return handoff payload
        handoff = {
            "execution_id": str(execution_id),
            "embedded_url": embedded_url,
            "display": action.embedded_json.get("display", {}),
            "callback": action.embedded_json.get("callback_method", {})
        }

        return handoff

    @action("record-embedded-action-result", resources="message")
    async def record_embedded_action_result(self, message_id, action_id, execution_id, callback_payload, profile_id):
        """Record the result of an embedded action."""

        # Get the execution record
        execution = await self.statemgr.find_one(
            "message_action_execute",
            where={"_id": execution_id, "_deleted": None}
        )
        if not execution:
            raise ValueError("Action execution not found")

        # Validate that execution belongs to the message
        if str(execution.message_id) != str(message_id):
            raise ValueError("Execution does not belong to the specified message")

        # Validate action_id matches
        if str(execution.action_id) != str(action_id):
            raise ValueError("Action ID does not match execution record")

        # Get the action definition
        action = await self.statemgr.find_one(
            "message_action",
            where={"_id": action_id, "_deleted": None}
        )
        if not action:
            raise ValueError("Action definition not found")

        if not action.embedded_json:
            raise ValueError("Embedded action definition is missing embedded configuration")

        callback_config = action.embedded_json.get("callback_method", {})
        if not callback_config or "mode" not in callback_config:
            raise ValueError("Embedded action callback configuration is missing or invalid")

        result = self._normalize_embedded_callback(callback_payload, callback_config)

        # Update execution record
        status_result = ActionExecutionStatus.COMPLETED.value if result["status"] == "success" else ActionExecutionStatus.FAILED.value
        response_payload_json_result = result
        completed_at = datetime.utcnow()
        await self.statemgr.update(execution,
                                   status=status_result,
                                   response_payload_json=response_payload_json_result,
                                   completed_at=completed_at)

        return result

    async def _execute_action_api(self, action, payload):
        """Execute an action via API call."""

        if action.execution_mode.value != "API":
            raise ValueError("Action execution mode is not API")

        if not action.endpoint_json:
            raise ValueError("Action has no endpoint configuration")

        endpoint = action.endpoint_json
        url = endpoint["url"]
        method = endpoint.get("method", "POST")
        headers = endpoint.get("headers", {})

        # Add authorization
        if action.authorization:
            auth = action.authorization
            if auth["type"] == "bearer":
                headers["Authorization"] = f"Bearer {auth['token']}"
            elif auth["type"] == "apiKey":
                headers[auth["header"]] = auth["value"]
            elif auth["type"] == "basic":
                # Basic auth would need username/password
                pass

        try:
            async with AsyncClient(timeout=5.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=payload)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=payload)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=payload)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, headers=headers, json=payload)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code >= 200 and response.status_code < 300:
                    response_data = response.json()
                    return {
                        "status": "success",
                        "action_id": str(action._id),
                        "record_id": response_data.get("record_id"),
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": response_data
                    }
                else:
                    return {
                        "status": "error",
                        "action_id": str(action._id),
                        "timestamp": datetime.utcnow().isoformat(),
                        "error": {
                            "code": "API_ERROR",
                            "message": f"API call failed with status {response.status_code}",
                            "details": response.text
                        }
                    }
        except Exception as e:
            return {
                "status": "error",
                "action_id": str(action._id),
                "timestamp": datetime.utcnow().isoformat(),
                "error": {
                    "code": "NETWORK_ERROR",
                    "message": str(e)
                }
            }

    async def _validate_form_data(self, form_data, schema):
        """Validate form data against schema."""
        # Basic validation - could be enhanced
        if not schema or not schema.get("fields"):
            return

        for field in schema["fields"]:
            field_key = field["key"]
            if field.get("required", False) and field_key not in form_data:
                raise ValueError(f"Required field '{field_key}' is missing")

    def _normalize_embedded_callback(self, callback_payload, callback_config):
        """Normalize embedded action callback to standard envelope."""

        def _normalize_event_value(value):
            if value is None:
                return []
            if isinstance(value, str):
                return [value]
            return list(value)

        mode = callback_config.get("mode", "POSTMESSAGE")
        mechanism = callback_config.get("mechanism", {})

        status = "error"

        if mode == "POSTMESSAGE":
            event = callback_payload.get("event", "")
            success_values = _normalize_event_value(mechanism.get("successEvent"))
            cancel_values = _normalize_event_value(mechanism.get("cancelEvent"))
            error_values = _normalize_event_value(mechanism.get("errorEvent"))

            if event in success_values:
                status = "success"
            elif event in cancel_values or event in error_values:
                status = "error"

        elif mode == "DEEPLINK":
            callback_url = callback_payload.get("url") or callback_payload.get("callback_url")
            if callback_url:
                success_urls = _normalize_event_value(mechanism.get("successUrl"))
                cancel_urls = _normalize_event_value(mechanism.get("cancelUrl"))
                error_urls = _normalize_event_value(mechanism.get("errorUrl"))

                if callback_url in success_urls:
                    status = "success"
                elif callback_url in cancel_urls or callback_url in error_urls:
                    status = "error"
                else:
                    status = "error"
            else:
                link_type = callback_payload.get("type", "")
                if link_type == "success":
                    status = "success"

        elif mode == "WEBHOOK":
            webhook_status = callback_payload.get("status")
            if isinstance(webhook_status, str) and webhook_status.lower() == "success":
                status = "success"
            elif webhook_status in (True, 1, "1", "true", "True"):
                status = "success"
            else:
                status = "error"

        return {
            "status": status,
            "action_id": callback_payload.get("action_id"),
            "record_id": callback_payload.get("record_id"),
            "timestamp": callback_payload.get("timestamp", datetime.utcnow().isoformat()),
            "data": callback_payload.get("data"),
            "error": callback_payload.get("error")
        }

    # def _check_action_executed(self, message_id, mailbox_id):
    #     """Check if action is executed by any profile for the message in the context of the mailbox."""
    @action("link-message", resources="message")
    async def link_message(self, right_message_id, left_message_id, mailbox_id, link_type):
        message_link_exist = await self.statemgr.exist(
            "message_link",
            where={"right_message_id": right_message_id, 
                   "left_message_id": left_message_id,
                   "mailbox_id": mailbox_id,
                   "_deleted": None}
        )
        if message_link_exist:
            raise ValueError("Link message has existed")

        message_link = self.init_resource(
            "message_link",
            _id=UUID_GENR(),
            right_message_id=right_message_id,
            left_message_id=left_message_id,
            mailbox_id=mailbox_id,
            link_type=link_type
        )

        await self.statemgr.insert(message_link)

        return message_link