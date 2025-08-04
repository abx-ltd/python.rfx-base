from fluvius.domain.aggregate import Aggregate, action

class MessageAggregate(Aggregate):
    """
    Aggregate for managing message-related operations.
    This includes actions on messages, recipients, attachments, embedded content, and references.
    """

    @action
    def create_message(self, data):
        """Action to create a new message."""
        pass

    @action
    def update_message(self, data):
        """Action to update an existing message."""
        pass

    @action
    def delete_message(self, data):
        """Action to delete a message."""
        pass

    @action
    def add_recipient(self, data):
        """Action to add a recipient to a message."""
        pass

    @action
    def remove_recipient(self, data):
        """Action to remove a recipient from a message."""
        pass
    

