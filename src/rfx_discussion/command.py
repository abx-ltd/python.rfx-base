from fluvius.data import serialize_mapping, logger

from .domain import RFXDiscussionDomain
from . import datadef, config

processor = RFXDiscussionDomain.command_processor
Command = RFXDiscussionDomain.Command

# ---------- Ticket Context ----------


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
        await agg.assign_member_to_ticket(payload.member_id)


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


# class AddTicketComment(Command):
#     """Add Comment to Ticket - Adds a comment to ticket"""

#     class Meta:
#         key = "add-ticket-comment"
#         resources = ("ticket",)
#         tags = ["ticket", "comment"]
#         auth_required = True
#         description = "Add comment to ticket"

#     Data = datadef.AddTicketCommentPayload

#     async def _process(self, agg, stm, payload):
#         """Add comment to ticket"""
#         await agg.add_ticket_comment(payload.comment_id)
#         # Get the updated ticket data
#         ticket = await stm.fetch("ticket", self.aggroot.identifier)
#         yield agg.create_response(serialize_mapping(ticket), _type="ticket-response")


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
