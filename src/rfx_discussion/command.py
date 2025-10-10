from fluvius.data import serialize_mapping, logger
from fluvius.domain.activity import ActivityType
from fluvius.domain.aggregate import AggregateRoot

from .domain import RFXDiscussionDomain
from . import datadef, config
from .types import ActivityAction

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
        policy_required = True

    Data = datadef.CreateInquiryPayload

    async def _process(self, agg, stm, payload):

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        result = await agg.create_inquiry(data=payload)

        yield agg.create_activity(
            logroot=AggregateRoot(
                resource="ticket",
                identifier=result._id,
                domain_sid=agg.get_aggroot().domain_sid,
                domain_iid=agg.get_aggroot().domain_iid,
            ),
            message=f"{profile.name__given} {profile.name__family} created a inquiry {result.title}",
            msglabel="create inquiry",
            msgtype=ActivityType.USER_ACTION,
            data={
                "ticket_id": result._id,
                "ticket_title": result.title,
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
        )
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
        policy_required = False

    Data = datadef.CreateTicketPayload

    async def _process(self, agg, stm, payload):
        """Create a new ticket in project"""
        result = await agg.create_ticket(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} created a ticket {result.title}",
            msglabel="create ticket",
            msgtype=ActivityType.USER_ACTION,
            data={
                "ticket_id": agg.get_aggroot().identifier,
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        yield agg.create_response(serialize_mapping(result), _type="ticket-response")


class UpdateTicketInfo(Command):
    """Update Ticket Info - Updates ticket information"""

    class Meta:
        key = "update-ticket"
        resources = ("ticket",)
        tags = ["ticket", "update"]
        auth_required = True
        description = "Update ticket information"
        policy_required = True

    Data = datadef.UpdateTicketPayload

    async def _process(self, agg, stm, payload):
        await agg.update_ticket_info(payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        ticket = await stm.find_one("ticket", where=dict(_id=agg.get_aggroot().identifier))

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} updated a ticket {ticket.title}",
            msglabel="update ticket",
            msgtype=ActivityType.USER_ACTION,
            data={
                "ticket_id": agg.get_aggroot().identifier,
                "updated_by": f"{profile.name__given} {profile.name__family}",
            }
        )


class RemoveTicket(Command):
    """Remove Ticket - Removes a ticket"""

    class Meta:
        key = "remove-ticket"
        resources = ("ticket",)
        tags = ["ticket", "remove"]
        auth_required = True
        description = "Remove ticket"
        policy_required = True

    async def _process(self, agg, stm, payload):

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        ticket = await stm.find_one("ticket", where=dict(_id=agg.get_aggroot().identifier))

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a ticket {ticket.title}",
            msglabel="remove ticket",
            msgtype=ActivityType.USER_ACTION,
            data={
                "removed_by": f"{profile.name__given} {profile.name__family}",
            }
        )

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
        policy_required = True

    Data = datadef.AssignTicketMemberPayload

    async def _process(self, agg, stm, payload):
        """Assign member to ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        member = await stm.get_profile(payload.member_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} assigned {member.name__given} {member.name__family}",
            msglabel="assign member",
            msgtype=ActivityType.USER_ACTION,
            data={
                "member_id": member._id,
                "assigned_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        await agg.assign_member_to_ticket(data=payload)


class RemoveMemberFromTicket(Command):
    """Remove Member from Ticket - Removes a member from ticket"""

    class Meta:
        key = "remove-member"
        resources = ("ticket",)
        tags = ["ticket", "member"]
        auth_required = True
        description = "Remove member from ticket"
        policy_required = True

    Data = datadef.RemoveTicketMemberPayload

    async def _process(self, agg, stm, payload):
        """Remove member from ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        member = await stm.get_profile(payload.member_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed {member.name__given} {member.name__family}",
            msglabel="remove member",
            msgtype=ActivityType.USER_ACTION,
            data={
                "member_id": member._id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            }
        )

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
        policy_required = True

    Data = datadef.AddTicketParticipantPayload

    async def _process(self, agg, stm, payload):
        """Add participant to ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        participant = await stm.get_profile(payload.participant_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} added {participant.name__given} {participant.name__family} as a participant",
            msglabel="add participant",
            msgtype=ActivityType.USER_ACTION,
            data={
                "participant_id": participant._id,
                "added_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        await agg.add_ticket_participant(payload.participant_id)


class RemoveParticipantFromTicket(Command):
    """Remove Participant from Ticket - Removes a participant from ticket"""

    class Meta:
        key = "remove-participant"
        resources = ("ticket",)
        tags = ["ticket", "participant"]
        auth_required = True
        description = "Remove participant from ticket"
        policy_required = True

    Data = datadef.RemoveTicketParticipantPayload

    async def _process(self, agg, stm, payload):
        """Remove participant from ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        participant = await stm.get_profile(payload.participant_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a participant {participant.name__given} {participant.name__family}",
            msglabel="remove participant",
            msgtype=ActivityType.USER_ACTION,
            data={
                "participant_id": participant._id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            }
        )

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = False

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
        policy_required = True

    Data = datadef.AddTicketTagPayload

    async def _process(self, agg, stm, payload):
        """Add tag to ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} added a tag",
            msglabel="add tag",
            msgtype=ActivityType.USER_ACTION,
            data={
                "tag_id": payload.tag_id,
                "added_by": f"{profile.name__given} {profile.name__family}",
            }
        )
        await agg.add_ticket_tag(payload.tag_id)


class RemoveTicketTag(Command):
    """Remove Tag from Ticket - Removes a tag from ticket"""

    class Meta:
        key = "remove-ticket-tag"
        resources = ("ticket",)
        tags = ["ticket", "tag"]
        auth_required = True
        description = "Remove tag from ticket"
        policy_required = True

    Data = datadef.RemoveTicketTagPayload

    async def _process(self, agg, stm, payload):
        """Remove tag from ticket"""

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} removed a tag",
            msglabel="remove tag",
            msgtype=ActivityType.USER_ACTION,
            data={
                "tag_id": payload.tag_id,
                "removed_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        await agg.remove_ticket_tag(payload.tag_id)


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
        policy_required = True

    Data = datadef.CreateTicketCommentPayload

    async def _process(self, agg, stm, payload):
        """Create ticket comment"""
        result = await agg.create_ticket_comment(data=payload)

        profile_id = agg.get_context().profile_id
        profile = await stm.get_profile(profile_id)

        yield agg.create_activity(
            logroot=agg.get_aggroot(),
            message=f"{profile.name__given} {profile.name__family} created a comment",
            msglabel="create comment",
            msgtype=ActivityType.USER_ACTION,
            data={
                "comment_id": result._id,
                "created_by": f"{profile.name__given} {profile.name__family}",
            }
        )

        yield agg.create_response(serialize_mapping(result), _type="comment-response")


# ------------ Status Context ----------
class CreateStatus(Command):
    """Create Status - Creates a new status"""

    class Meta:
        key = "create-status"
        resources = ("status",)
        tags = ["status"]
        auth_required = True
        description = "Create a new status"
        new_resource = True
        policy_required = False

    Data = datadef.CreateStatusPayload

    async def _process(self, agg, stm, payload):
        """Create status"""
        status = await agg.create_status(data=payload)
        yield agg.create_response(serialize_mapping(status), _type="status-response")


class CreateStatusKey(Command):
    """Create Status Key - Creates a new status key"""

    class Meta:
        key = "create-status-key"
        resources = ("status",)
        tags = ["status", "status-key"]
        auth_required = True
        description = "Create a new status key"
        policy_required = False

    Data = datadef.CreateStatusKeyPayload

    async def _process(self, agg, stm, payload):
        """Create status key"""
        status_key = await agg.create_status_key(data=payload)
        yield agg.create_response(serialize_mapping(status_key), _type="status-key-response")


class CreateStatusTransition(Command):
    """Create Status Transition - Creates a new status transition"""

    class Meta:
        key = "create-status-transition"
        resources = ("status",)
        tags = ["status", "status-transition"]
        auth_required = True
        description = "Create a new status transition"
        policy_required = False

    Data = datadef.CreateStatusTransitionPayload

    async def _process(self, agg, stm, payload):
        """Create status transition"""
        status_transition = await agg.create_status_transition(data=payload)
        yield agg.create_response(serialize_mapping(status_transition), _type="status-transition-response")

# ------------ Linear Integration (Ticket Context) ------------
class SyncTicketToLinear(Command):
    """Sync Ticket to Linear - Sync a ticket to Linear"""

    class Meta:
        key = "sync-ticket-to-linear"
        resources = ("ticket",)
        tags = ["ticket", "linear"]
        auth_required = True
        description = "Sync a ticket to Linear"
        policy_required = False

    async def _process(self, agg, stm, payload):
        """Sync a ticket to Linear"""
        check = await agg.check_linear_project_ticket_exists()
        exists = check.get("exists", False)

        if not exists:
            result = await agg.create_linear_project_ticket()
        else:
            result = await agg.update_linear_project_ticket()

        yield agg.create_response({"data": result}, _type="sync-ticket-to-linear-response")