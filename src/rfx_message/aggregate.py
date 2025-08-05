"""
RFX Messaging Domain Aggregate - Business Logic and State Management
"""
from fluvius.domain.aggregate import Aggregate, action
from fluvius.data import serialize_mapping, UUID_GENR

class MessageAggregate(Aggregate):
    """
    Aggregate for managing message-related operations.
    This includes actions on messages, recipients, attachments, embedded content, and references.
    """

    # ========================================================================
    # MESSAGE OPERATIONS
    # ========================================================================

    @action("message-created", resources="message")
    async def create_message(self, stm, /, *, data):
        """Action to create a new message."""
        message = self.init_resource(
            "message",
            serialize_mapping(data),
            _id=self.aggroot.identifier)
        await stm.insert(message)
        return {
            "message_id": message._id,
        }
        
    @action
    def update_message(self, data):
        """Action to update an existing message."""
        pass

    @action
    def delete_message(self, data):
        """Action to delete a message."""
        pass

    @action("message-retrieved", resources=("message","message-recipient"))
    async def add_recipients(self, stm, /, *, data, message_id):
        """Action to add a recipient to a message."""
        recipient_objects = [
            self.init_resource(
                "message-recipient",
                data={
                    "message_id": message_id,
                    "recipient_id": recipient_data,
                    "_id": UUID_GENR()
                }
            ) for recipient_data in data
        ]

        recipients = [serialize_mapping(recipient) for recipient in recipient_objects]
        await stm.insert_many("message-recipient", *recipients)
        return {
            "recipients": [recipient for recipient in recipients]
        }

    @action
    def remove_recipient(self, data):
        """Action to remove a recipient from a message."""
        pass

    # ========================================================================
    # RECIPIENT OPERATIONS
    # ========================================================================
