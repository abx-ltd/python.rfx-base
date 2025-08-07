"""
RFX Messaging Domain Aggregate - Business Logic and State Management
"""
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, UUID_GENR

from . import logger

class MessageAggregate(Aggregate):
    """
    Aggregate for managing message-related operations.
    This includes actions on messages, recipients, attachments, embedded content, and references.
    """

    # ========================================================================
    # MESSAGE OPERATIONS
    # ========================================================================

    @action("message-generated", resources="message")
    async def generate_message(self, stm, /, *, data):
        """Action to create a new message."""
        message = self.init_resource(
            "message",
            serialize_mapping(data),
            _id=self.aggroot.identifier)
        await stm.insert(message)
        return {
            "message_id": message._id,
        }
        
    # @action("message-updated", resources="message")
    # async def update_message(self, stm, /, *, data):
    #     """Action to update an existing message."""
    #     message_id = data.pop("message_id")
        
    #     # Fetch the existing message
    #     message = await stm.fetch("message", message_id)
        
    #     # Only update non-None fields
    #     update_data = {k: v for k, v in data.items() if v is not None}
        
    #     await stm.update(message, **update_data)
    #     return {
    #         "message_id": message_id,
    #     }

    # @action("message-deleted", resources="message")
    # async def delete_message(self, stm, /, *, message_id):
    #     """Action to delete a message."""
    #     # Fetch the message and soft delete it
    #     message = await stm.fetch("message", message_id)
    #     await stm.invalidate(message)
        
    #     return {
    #         "message_id": message_id,
    #     }

    @action("message-retrieved", resources=("message", "message-recipient"))
    async def add_recipients(self, stm, /, *, data, message_id):
        """Action to add recipients to a message."""
        recipient_data_list = []
        
        for recipient_id in data:
            recipient_data = {
                "message_id": message_id,
                "recipient_id": recipient_id,
                "_id": UUID_GENR(),
                "read": False,
                "archived": False
            }
            recipient_data_list.append(recipient_data)

        await stm.insert_many("message-recipient", *recipient_data_list)
        
        return {
            "recipients": recipient_data_list
        }

    @action("message-read", resources=("message-recipient"))
    async def mark_message_read(self, stm, /):
        """Action to mark a message as read for a specific user."""
        # Find the recipient record for this user and message
        recipient_record = await stm.fetch("message-recipient", self.aggroot.identifier)

        await stm.update(recipient_record, 
            read=True,
            mark_as_read=self.context.timestamp
        )
        return {
            "status": "success",
            "message_id": self.get_aggroot().identifier,
            "user_id": self.context.user_id,
            "read_at": self.context.timestamp.isoformat()
        }

    @action("bulk-messages-read", resources="message-recipient")
    async def mark_all_messages_read(self, stm, /, *, user_id):
        """Action to mark all unread messages as read for a user."""
        # Find all unread message-recipient records for this user
        unread_recipients = await stm.find_all(
            "message-recipient",
            where=dict(
                recipient_id=user_id, 
                read=False
            )
        )
        
        await stm.upsert_many(
            "message-recipient",
            *[{
                "_id": recipient._id,
                "read": True,
                "mark_as_read": self.context.timestamp
            } for recipient in unread_recipients]
        )
        
        return {
            "status": "success",
            "user_id": user_id,
            "messages_read": len(unread_recipients),
        }

    @action("message-archived", resources="message-recipient")
    async def archive_message(self, stm, /):
        """Action to archive a message for a specific user."""
        recipient_record = await stm.fetch("message-recipient", self.aggroot.identifier)
        await stm.update(recipient_record, archived=True)

        return {"status": "success", "message_id": self.aggroot.identifier}


    @action("attachment-added", resources="message-attachment")
    async def add_attachment(self, stm, /, *, data):
        """Action to add an attachment to a message."""
        attachment_data = serialize_mapping(data)
        attachment_data['_id'] = UUID_GENR()
        
        attachment = stm.create("message-attachment", attachment_data)
        await stm.insert(attachment)
        
        return {
            "attachment_id": attachment._id,
            "message_id": data["message_id"],
        }