from fluvius.data import serialize_mapping, logger

from .domain import RFXDiscussionDomain
from . import datadef, config

processor = RFXDiscussionDomain.command_processor
Command = RFXDiscussionDomain.Command


# ---------- Inquiry (Ticket Context) ----------
class CreateInquiry(Command):
    """Create Inquiry - Creates a new inquiry (ticket not tied to project)"""

    class Meta:
        key = "create-inquiry"
        resources = ("ticket",)
        tags = ["ticket", "inquiry"]
        auth_required = True
        description = "Create a new inquiry"
        new_resource = True

    Data = datadef.CreateInquiryPayload

    async def _process(self, agg, stm, payload):
        context = agg.get_context()
        user_id = context.user_id
        payload = payload.set(creator=user_id)
        result = await agg.create_inquiry(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="ticket-response")


# ---------- Ticket (Ticket Context) ----------
class CreateTicket(Command):
    """Create Ticket - Creates a new ticket tied to a project"""

    class Meta:
        key = "create-ticket"
        resources = ("ticket",)
        tags = ["ticket"]
        auth_required = True
        description = "Create a new ticket in project"
        new_resource = True
        internal = True

    Data = datadef.CreateTicketPayload

    async def _process(self, agg, stm, payload):
        """Create a new ticket in project"""
        result = await agg.create_ticket(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="ticket-response")


class UpdateTicketInfo(Command):
    """Update Ticket Info - Updates ticket information"""

    class Meta:
        key = "update-ticket"
        resources = ("ticket",)
        tags = ["ticket", "update"]
        auth_required = True
        description = "Update ticket information"

    Data = datadef.UpdateTicketPayload

    async def _process(self, agg, stm, payload):
        await agg.update_ticket_info(payload)


class RemoveTicket(Command):
    """Remove Ticket - Removes a ticket"""

    class Meta:
        key = "remove-ticket"
        resources = ("ticket",)
        tags = ["ticket", "remove"]
        auth_required = True
        description = "Remove ticket"

    async def _process(self, agg, stm, payload):
        await agg.remove_ticket()


# ---------- Ticket Assignee (Ticket Context) ----------
class AssignMemberToTicket(Command):
    """Assign Member to Ticket - Assigns a member to ticket"""

    class Meta:
        key = "assign-member"
        resources = ("ticket",)
        tags = ["ticket", "member"]
        auth_required = True
        description = "Assign member to ticket"

    Data = datadef.AssignTicketMemberPayload

    async def _process(self, agg, stm, payload):
        """Assign member to ticket"""
        await agg.assign_member_to_ticket(data=payload)


class RemoveMemberFromTicket(Command):
    """Remove Member from Ticket - Removes a member from ticket"""

    class Meta:
        key = "remove-member"
        resources = ("ticket",)
        tags = ["ticket", "member"]
        auth_required = True
        description = "Remove member from ticket"

    Data = datadef.RemoveTicketMemberPayload

    async def _process(self, agg, stm, payload):
        """Remove member from ticket"""
        await agg.remove_member_from_ticket(payload.member_id)


# ---------- Ticket Participant (Ticket Context) ----------
class AddParticipantToTicket(Command):
    """Add Participant to Ticket - Adds a participant to ticket"""

    class Meta:
        key = "add-participant"
        resources = ("ticket",)
        tags = ["ticket", "participant"]
        auth_required = True
        description = "Add participant to ticket"

    Data = datadef.AddTicketParticipantPayload

    async def _process(self, agg, stm, payload):
        """Add participant to ticket"""
        await agg.add_ticket_participant(payload.participant_id)


class RemoveParticipantFromTicket(Command):
    """Remove Participant from Ticket - Removes a participant from ticket"""

    class Meta:
        key = "remove-participant"
        resources = ("ticket",)
        tags = ["ticket", "participant"]
        auth_required = True
        description = "Remove participant from ticket"

    Data = datadef.RemoveTicketParticipantPayload

    async def _process(self, agg, stm, payload):
        """Remove participant from ticket"""
        await agg.remove_ticket_participant(payload.participant_id)


# ---------- Tag Context ----------
class CreateTag(Command):
    """Create Tag - Creagtes a new tag"""

    class Meta:
        key = "create-tag"
        resources = ("tag",)
        tags = ["tag"]
        auth_required = True
        description = "Create a new tag in project"
        new_resource = True

    Data = datadef.CreateTagPayload

    async def _process(self, agg, stm, payload):
        """Create tag"""
        result = await agg.create_tag(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="tag-response")


class UpdateTag(Command):
    """Update Tag - Updates a tag"""

    class Meta:
        key = "update-tag"
        resources = ("tag",)
        tags = ["tag", "update"]
        auth_required = True
        description = "Update tag"

    Data = datadef.UpdateTagPayload

    async def _process(self, agg, stm, payload):
        """Update tag"""
        await agg.update_tag(data=payload)


class DeleteTag(Command):
    """Delete Tag - Deletes a tag"""

    class Meta:
        key = "delete-tag"
        resources = ("tag",)
        tags = ["tag", "delete"]
        auth_required = True
        description = "Delete tag"

    async def _process(self, agg, stm, payload):
        """Delete tag"""
        await agg.delete_tag()


# ---------- Ticket Type (Ticket Context) ----------
class CreateTicketType(Command):
    """Create Ticket Type - Creates a new ticket type"""

    class Meta:
        key = "create-ticket-type"
        resources = ("ticket",)
        tags = ["ticket", "ticket-type", "reference"]
        auth_required = True
        description = "Create a new ticket type"
        new_resource = True

    Data = datadef.CreateTicketTypePayload

    async def _process(self, agg, stm, payload):
        """Create ticket type"""
        result = await agg.create_ticket_type(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="ticket-type-response")


class UpdateTicketType(Command):
    """Update Ticket Type - Updates a ticket type"""

    class Meta:
        key = "update-ticket-type"
        resources = ("ticket",)
        tags = ["ticket", "ticket-type", "update"]
        auth_required = True
        description = "Update a ticket type"
        new_resource = True

    Data = datadef.UpdateTicketTypePayload

    async def _process(self, agg, stm, payload):
        """Update ticket type"""
        await agg.update_ticket_type(data=payload)


class DeleteTicketType(Command):
    """Delete Ticket Type - Deletes a ticket type"""

    class Meta:
        key = "delete-ticket-type"
        resources = ("ticket",)
        tags = ["ticket", "ticket-type", "delete"]
        auth_required = True
        description = "Delete a ticket type"
        new_resource = True

    Data = datadef.DeleteTicketTypePayload

    async def _process(self, agg, stm, payload):
        """Delete ticket type"""
        await agg.delete_ticket_type(data=payload)


# ---------- Ticket Tag (Ticket Context) ----------
class AddTicketTag(Command):
    """Add Tag to Ticket - Adds a tag to ticket"""

    class Meta:
        key = "add-ticket-tag"
        resources = ("ticket",)
        tags = ["ticket", "tag"]
        auth_required = True
        description = "Add tag to ticket"

    Data = datadef.AddTicketTagPayload

    async def _process(self, agg, stm, payload):
        """Add tag to ticket"""
        await agg.add_ticket_tag(payload.tag_id)


class RemoveTicketTag(Command):
    """Remove Tag from Ticket - Removes a tag from ticket"""

    class Meta:
        key = "remove-ticket-tag"
        resources = ("ticket",)
        tags = ["ticket", "tag"]
        auth_required = True
        description = "Remove tag from ticket"

    Data = datadef.RemoveTicketTagPayload

    async def _process(self, agg, stm, payload):
        """Remove tag from ticket"""
        await agg.remove_ticket_tag(payload.tag_id)
        # Get the updated ticket data
        ticket = await stm.fetch("ticket", self.aggroot.identifier)
        yield agg.create_response(serialize_mapping(ticket), _type="ticket-response")

# ---------- Comment Context ----------


class CreateComment(Command):
    """Create Comment - Creates a new comment"""

    class Meta:
        key = "create-comment"
        resources = ("comment",)
        tags = ["comment"]
        auth_required = True
        description = "Create a new comment"
        new_resource = True
        internal = True

    Data = datadef.CreateCommentPayload

    async def _process(self, agg, stm, payload):
        """Create comment"""
        result = await agg.create_comment(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="comment-response")


class UpdateComment(Command):
    """Update Comment - Updates a comment"""

    class Meta:
        key = "update-comment"
        resources = ("comment",)
        tags = ["comment", "update"]
        auth_required = True
        description = "Update a comment"

    Data = datadef.UpdateCommentPayload

    async def _process(self, agg, stm, payload):
        """Update comment"""
        await agg.update_comment(data=payload)


class DeleteComment(Command):
    """Delete Comment - Deletes a comment"""

    class Meta:
        key = "delete-comment"
        resources = ("comment",)
        tags = ["comment", "delete"]
        auth_required = True
        description = "Delete a comment"

    async def _process(self, agg, stm, payload):
        """Delete comment"""
        await agg.delete_comment()


class ReplyToComment(Command):
    """Reply to Comment - Replies to a comment"""

    class Meta:
        key = "reply-to-comment"
        resources = ("comment",)
        tags = ["comment", "reply"]
        auth_required = True
        description = "Reply to a comment"

    Data = datadef.ReplyToCommentPayload

    async def _process(self, agg, stm, payload):
        """Reply to comment"""
        result = await agg.reply_to_comment(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="comment-response")


# ------------ Ticket Comment (Ticket Context) ------------


class CreateTicketComment(Command):
    """Create Ticket Comment - Creates a new comment for a ticket"""

    class Meta:
        key = "create-ticket-comment"
        resources = ("ticket",)
        tags = ["ticket", "comment"]
        auth_required = True
        description = "Create a new comment for a ticket"

    Data = datadef.CreateTicketCommentPayload

    async def _process(self, agg, stm, payload):
        """Create ticket comment"""
        result = await agg.create_ticket_comment(data=payload)
        yield agg.create_response(serialize_mapping(result), _type="comment-response")
