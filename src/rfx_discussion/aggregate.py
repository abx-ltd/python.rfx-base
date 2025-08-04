from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from typing import Optional
from datetime import datetime
from rfx_discussion import logger
from .types import Availability, SyncStatus


class RFXDiscussionAggregate(Aggregate):
    """CPO Portal Aggregate Root - Handles  ticket, comment, external """

    # =========== Ticket Context ============
    @action("ticket-type-created", resources="ticket")
    async def create_ticket_type(self, stm, /, data):
        """Create a new ticket type"""
        record = self.init_resource(
            "ref--ticket-type",
            serialize_mapping(data),
        )
        await stm.insert(record)
        return record

    @action('inquiry-created', resources='ticket')
    async def create_inquiry(self, stm, /, data):
        record = self.init_resource(
            "ticket",
            serialize_mapping(data),
            status="DRAFT",
            availability=Availability.OPEN,
        )
        await stm.insert(record)
        return record

    @action('ticket-created', resources='ticket')
    async def create_ticket(self, stm, /, data):
        """Create a new ticket tied to project"""
        ticket_data = serialize_mapping(data)
        ticket_data.update({
            "_id": self.aggroot.identifier,
            "status": "DRAFT",
            "availability": Availability.OPEN,
            "sync_status": SyncStatus.PENDING
        })
        ticket = self.init_resource("ticket", ticket_data)

        logger.info(f"Ticket data: {ticket}")

        await stm.insert(ticket)
    # TH command goi 2 domain khac nhau
        await stm.insert(self.init_resource("project-ticket", {
            "project_id": data.project_id,
            "ticket_id": ticket._id
        }))

        return ticket

    @action('ticket-updated', resources='ticket')
    async def update_ticket_info(self, stm, /, data):
        """Update ticket information"""
        ticket = self.rootobj
        await stm.update(ticket, **serialize_mapping(data))
        return ticket

    @action('ticket-closed', resources='ticket')
    async def close_ticket(self, stm, /):
        """Close ticket"""
        ticket = self.rootobj
        await stm.update(ticket, availability=Availability.CLOSED)
        return ticket

    @action('ticket-reopened', resources='ticket')
    async def reopen_ticket(self, stm, /):
        """Reopen ticket"""
        ticket = self.rootobj
        await stm.update(ticket, availability=Availability.AVAILABLE)
        return ticket

    @action('ticket-status-changed', resources='ticket')
    async def change_ticket_status(self, stm, /, next_status: str, note: Optional[str] = None):
        """Change ticket status using workflow"""
        ticket = self.rootobj

        # Create status transition record
        status_record = self.init_resource(
            "ticket-status",
            {
                "ticket_id": ticket._id,
                "src_state": ticket.status,
                "dst_state": next_status,
                "note": note
            },
            _id=UUID_GENR()
        )
        await stm.insert(status_record)

        # Update ticket status
        await stm.update(ticket, status=next_status)
        return ticket

    @action('member-assigned-to-ticket', resources='ticket')
    async def assign_member_to_ticket(self, stm, /, member_id: str):
        """Assign member to ticket"""
        record = self.init_resource(
            "ticket-assignee",
            {
                "ticket_id": self.aggroot.identifier,
                "member_id": member_id,
                "role": "ASSIGNEE"
            },
            _id=UUID_GENR(),
            assigned_at=datetime.utcnow()
        )
        await stm.insert(record)
        return record

    @action('member-removed-from-ticket', resources='ticket')
    async def remove_member_from_ticket(self, stm, /, member_id: str):
        """Remove member from ticket"""
        assignees = await stm.find_all('ticket-assignee',
                                       where=dict(
                                           ticket_id=self.aggroot.identifier,
                                           member_id=member_id
                                       ))
        for assignee in assignees:
            await stm.invalidate_one('ticket-assignee', assignee._id)
        return {"removed": True}

    @action('comment-added-to-ticket', resources='ticket')
    async def add_ticket_comment(self, stm, /, comment_id: str):
        """Add comment to ticket"""
        record = self.init_resource(
            "ticket-comment",
            {
                "ticket_id": self.aggroot.identifier,
                "comment_id": comment_id
            },
            _id=UUID_GENR(),
            added_at=datetime.utcnow()
        )
        await stm.insert(record)
        return record

    @action('participant-added-to-ticket', resources='ticket')
    async def add_ticket_participant(self, stm, /, participant_id: str):
        """Add participant to ticket"""
        record = self.init_resource(
            "ticket-participants",
            {
                "ticket_id": self.aggroot.identifier,
                "participant_id": participant_id
            },
            _id=UUID_GENR()
        )
        await stm.insert(record)
        return record

    @action('tag-added-to-ticket', resources='ticket')
    async def add_ticket_tag(self, stm, /, tag_id: str):
        """Add tag to ticket"""
        record = self.init_resource(
            "ticket-tag",
            {
                "ticket_id": self.aggroot.identifier,
                "tag_id": tag_id
            },
            _id=UUID_GENR()
        )
        await stm.insert(record)
        return record

    @action('tag-removed-from-ticket', resources='ticket')
    async def remove_ticket_tag(self, stm, /, tag_id: str):
        """Remove tag from ticket"""
        tags = await stm.find_all('ticket-tag',
                                  where=dict(
                                      ticket_id=self.aggroot.identifier,
                                      tag_id=tag_id
                                  ))
        for tag in tags:
            await stm.invalidate_one('ticket-tag', tag._id)
        return {"removed": True}

    # =========== Tag Context ============
    @action("tag-created", resources="tag")
    async def create_tag(self, stm, /, data):
        """Create a new tag"""
        record = self.init_resource(
            "tag",
            serialize_mapping(data),
        )
        await stm.insert(record)
        return record

    @action("tag-updated", resources="tag")
    async def update_tag(self, stm, /, data):
        """Update tag"""
        tag = self.rootobj
        await stm.update(tag, **serialize_mapping(data))
        return tag
