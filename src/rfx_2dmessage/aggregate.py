from pyexpat.errors import messages

from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR, UUID_TYPE
from fluvius.error import BadRequestError
from typing import Optional, Dict, Any
from .types import RenderStatusEnum, PriorityLevelEnum, ActionExecutionStatus

class RFX2DMessageAggregate(Aggregate):
    # def _normalize_member_ids(self, sender_id, recipients=None):
    #     """Build a unique ordered member list from sender and recipients."""
    #     member_ids = [sender_id, *(recipients or [])]
    #     return [member_id for member_id in dict.fromkeys(member_ids) if member_id]

    # async def find_members_by_box_id(self, box_id, member_ids):
    #     """Check whether the box contains exactly the requested members."""
    #     memberships = await self.statemgr.find_all(
    #         "message_box_user",
    #         where={"box_id": box_id},
    #     )
    #     box_member_ids = {membership.user_id for membership in memberships}
    #     return box_member_ids == set(member_ids)

    # async def get_or_create_member_box(self, sender_id, recipients=None):
    #     """Get an existing exact-match member box or create a new one."""
    #     unique_member_ids = self._normalize_member_ids(sender_id, recipients)

    #     sender_box_users = await self.statemgr.find_all(
    #         "message_box_user",
    #         where={"user_id": sender_id},
    #     )

    #     for box_user in sender_box_users:
    #         if await self.find_members_by_box_id(box_user.box_id, unique_member_ids):
    #             return await self.statemgr.find_one(
    #                 "message_box",
    #                 where={"_id": box_user.box_id},
    #             )

    #     box_type = "GROUP" if len(unique_member_ids) >= 2 else "SINGLE"
    #     box = self.init_resource(
    #         "message_box",
    #         {"name": None, "key": None, "type": box_type},
    #         _id=UUID_GENR(),
    #     )
    #     await self.statemgr.insert(box)

    #     box_users = []
    #     for member_id in unique_member_ids:
    #         box_user = self.init_resource(
    #             "message_box_user",
    #             {"user_id": member_id, "box_id": box._id},
    #             _id=UUID_GENR(),
    #         )
    #         box_users.append(serialize_mapping(box_user))

    #     await self.statemgr.insert_data("message_box_user", *box_users)
    #     return box
    
    # @action("get-message-sender-by-message-id", resources="message")
    # async def get_message_sender_by_message_id(self, message_id):
    #     """Get message sender by message id."""
    #     return await self.statemgr.find_one(
    #         "message_sender",
    #         where={"message_id": message_id},
    #     )
    
    # @action("get-message-recipient", resources="message")
    # async def get_message_recipient(self, message_id, profile_id):
    #     """Get message recipient."""
    #     return await self.statemgr.find_one(
    #         "message_recipient",
    #         where={"message_id": message_id, "recipient_id": profile_id},
    #     )

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
    async def remove_tag(self, tag_id, profile_id):
        """Remove a tag."""
        tag = await self.statemgr.find_one(
            "tag",
            where={"_id": tag_id, "profile_id": profile_id},
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
            profile_id=profile_id    
        )

        await self.statemgr.insert(category)

        return category

    @action("remove-category", resources="category")
    async def remove_category(self, category_id, profile_id):
        # Delete all message-category associations for this category
        message_category = await self.statemgr.find_all(
            "message_category",
            where={"category_id": category_id}
        )
        for mc in message_category:
            await self.statemgr.invalidate(mc)

        # Remove category by category_id and profile_id
        category = await self.statemgr.find_one(
            "category",
            where={"_id": category_id, "profile_id": profile_id},
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
    async def add_message_to_category(self, mailbox_id, category_id, profile_id, message_ids):

        categories = await self.statemgr.find_all(
            "category",
            where={"profile_id": profile_id, "mailbox_id": mailbox_id, "_deleted": None},
        )

        message_category_exists = []
        
        for message_id in message_ids:
            # Check if message is already in any category for this profile of mailbox (non-deleted)
            # First, find all message categorie for this profile in mailbox
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
        
    @action("remove-message-from-category", resources="category")
    async def remove_message_from_category(self, mailbox_id, category_id, profile_id, message_ids):
        for message_id in message_ids:
            message_category = await self.statemgr.find_one(
                "message_category",
                where={"message_id": message_id, "category_id": category_id, "_deleted": None},
            )
            if message_category:
                await self.statemgr.invalidate(message_category)
        
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

    async def register_action(self, mailbox_id, action_data, profile_id):
        """Register or update an action definition for a mailbox."""
        from .types import ActionTypeEnum, ExecutionModeEnum

        # Validate action payload structure
        action_key = action_data["action_key"]
        action_type = action_data["action_type"]
        execution = action_data["execution"]

        # Validate action type and execution mode constraints
        if action_type == "atomic":
            if execution.get("mode") != "api":
                raise BadRequestError("Atomic actions must use API execution mode")
        elif action_type == "form":
            if execution.get("mode") != "api":
                raise BadRequestError("Form actions must use API execution mode")
            if "schema" not in action_data:
                raise BadRequestError("Form actions require a schema")
        elif action_type == "embedded":
            if execution.get("mode") != "embed":
                raise BadRequestError("Embedded actions must use embed execution mode")
        else:
            raise BadRequestError(f"Invalid action type: {action_type}")

        # Check if action already exists
        existing_action = await self.statemgr.find_one(
            "message_action",
            where={
                "mailbox_id": mailbox_id,
                "action_key": action_key,
                "_deleted": None
            }
        )

        if existing_action:
            # Update existing action
            action_data["execution_mode"] = ExecutionModeEnum(execution["mode"])
            action_data["action_type"] = ActionTypeEnum(action_type)

            # Handle nested JSON fields
            if "endpoint" in execution:
                action_data["endpoint_json"] = execution["endpoint"]
                action_data["embedded_json"] = None
            elif "embedded" in execution:
                action_data["embedded_json"] = execution["embedded"]
                action_data["endpoint_json"] = None

            if "authorization" in execution:
                action_data["authorization"] = execution["authorization"]

            await self.statemgr.update(existing_action, action_data)
            action = existing_action
        else:
            # Create new action
            action = self.init_resource(
                "message_action",
                _id=UUID_GENR(),
                mailbox_id=mailbox_id,
                action_key=action_key,
                name=action_data["name"],
                action_type=ActionTypeEnum(action_type),
                description=action_data.get("description"),
                execution_mode=ExecutionModeEnum(execution["mode"]),
                endpoint_json=execution.get("endpoint"),
                embedded_json=execution.get("embedded"),
                authorization=execution.get("authorization"),
                schema_json=action_data.get("schema"),
                response_json=action_data["response"]
            )
            await self.statemgr.insert(action)

        return {
            "action_id": action._id,
            "action_key": action_key,
            "status": "registered"
        }

    async def execute_atomic_action(self, message_id, action_id, profile_id):
        """Execute an atomic action for a message."""
        import httpx
        from datetime import datetime

        # Get the action definition
        action = await self.statemgr.find_one(
            "message_action",
            where={"_id": action_id, "_deleted": None}
        )
        if not action:
            raise BadRequestError("Action not found")

        if action.action_type.name != "ATOMIC":
            raise BadRequestError("Action is not an atomic action")

        # Create action execution record
        execution = self.init_resource(
            "message_action_execute",
            _id=UUID_GENR(),
            message_id=message_id,
            action_id=action_id,
            profile_id=profile_id,
            execution_mode=action.execution_mode,
            status=ActionExecutionStatus.PENDING
        )
        await self.statemgr.insert(execution)

        # Execute the action (server-side API call)
        result = await self._execute_action_api(action, {})

        # Update execution record
        execution.status = ActionExecutionStatus.COMPLETED if result["status"] == "success" else ActionExecutionStatus.FAILED
        execution.response_payload_json = result
        execution.completed_at = datetime.utcnow()
        await self.statemgr.update(execution, {
            "status": execution.status,
            "response_payload_json": result,
            "completed_at": execution.completed_at
        })

        return result

    async def submit_form_action(self, message_id, action_id, form_data, client_context, profile_id):
        """Submit a form action for a message."""
        import httpx
        from datetime import datetime

        # Get the action definition
        action = await self.statemgr.find_one(
            "message_action",
            where={"_id": action_id, "_deleted": None}
        )
        if not action:
            raise BadRequestError("Action not found")

        if action.action_type.name != "FORM":
            raise BadRequestError("Action is not a form action")

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
            status=ActionExecutionStatus.PENDING,
            input_payload_json=form_data
        )
        await self.statemgr.insert(execution)

        # Execute the action
        result = await self._execute_action_api(action, form_data)

        # Update execution record
        execution.status = ActionExecutionStatus.COMPLETED if result["status"] == "success" else ActionExecutionStatus.FAILED
        execution.response_payload_json = result
        execution.completed_at = datetime.utcnow()
        await self.statemgr.update(execution, {
            "status": execution.status,
            "response_payload_json": result,
            "completed_at": execution.completed_at
        })

        return result

    async def record_embedded_action_result(self, message_id, action_id, execution_id, callback_payload, profile_id):
        """Record the result of an embedded action."""
        from datetime import datetime

        # Get the execution record
        execution = await self.statemgr.find_one(
            "message_action_execute",
            where={"_id": execution_id, "_deleted": None}
        )
        if not execution:
            raise BadRequestError("Action execution not found")

        # Normalize callback payload to standard envelope
        result = self._normalize_embedded_callback(callback_payload)

        # Update execution record
        execution.status = ActionExecutionStatus.COMPLETED if result["status"] == "success" else ActionExecutionStatus.FAILED
        execution.response_payload_json = result
        execution.completed_at = datetime.utcnow()
        await self.statemgr.update(execution, {
            "status": execution.status,
            "response_payload_json": result,
            "completed_at": execution.completed_at
        })

        return result

    async def _execute_action_api(self, action, payload):
        """Execute an action via API call."""
        import httpx
        from datetime import datetime

        if not action.endpoint_json:
            raise BadRequestError("Action has no endpoint configuration")

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
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=payload)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=payload)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=payload)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, headers=headers, json=payload)
                else:
                    raise BadRequestError(f"Unsupported HTTP method: {method}")

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
                raise BadRequestError(f"Required field '{field_key}' is missing")

    def _normalize_embedded_callback(self, callback_payload):
        """Normalize embedded action callback to standard envelope."""
        from datetime import datetime

        # Map callback event to status
        event = callback_payload.get("event", "")
        if event in ["SIGNING_COMPLETE", "successEvent"]:
            status = "success"
        elif event in ["SIGNING_CANCELLED", "SIGNING_FAILED", "cancelEvent", "errorEvent"]:
            status = "error"
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
                