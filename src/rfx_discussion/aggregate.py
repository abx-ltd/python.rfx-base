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
    async def create_ticket_type(self, /, data):
        """Create a new ticket type"""
        record = self.init_resource(
            "ref--ticket-type",
            serialize_mapping(data),
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action('inquiry-created', resources='ticket')
    async def create_inquiry(self, /, data):
        record = self.init_resource(
            "ticket",
            serialize_mapping(data),
            status="DRAFT",
            availability=Availability.OPEN,
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action('ticket-created', resources='ticket')
    async def create_ticket(self, /, data):
        """Create a new ticket tied to project"""
        record = self.init_resource(
            "ticket",
            serialize_mapping(data),
            _id=self.aggroot.identifier,
            status="DRAFT",
            availability=Availability.OPEN,
            sync_status=SyncStatus.PENDING,
            is_inquiry=False
        )
        await self.statemgr.insert(record)
        return record

    @action('ticket-updated', resources='ticket')
    async def update_ticket_info(self, /, data):
        """Update ticket information"""
        ticket = self.rootobj
        await self.statemgr.update(ticket, **serialize_mapping(data))

    @action('ticket-removed', resources='ticket')
    async def remove_ticket(self, /):
        """Remove ticket"""
        ticket = self.rootobj
        await self.statemgr.invalidate(ticket)
        return {"removed": True}

    @action('ticket-status-changed', resources='ticket')
    async def change_ticket_status(self, /, next_status: str, note: Optional[str] = None):
        """Change ticket status using workflow"""
        ticket = self.rootobj

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
        await self.statemgr.insert(status_record)

        result = await self.statemgr.update(ticket, status=next_status)
        return result

    @action('member-assigned-to-ticket', resources='ticket')
    async def assign_member_to_ticket(self, /, member_id: str):
        """Assign member to ticket"""
        record = self.init_resource(
            "ticket-assignee",
            {
                "ticket_id": self.aggroot.identifier,
                "member_id": member_id,
                "role": "ASSIGNEE"
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action('member-removed-from-ticket', resources='ticket')
    async def remove_member_from_ticket(self, /, member_id: str):
        """Remove member from ticket"""
        assignees = await self.statemgr.find_all('ticket-assignee',
                                                 where=dict(
                                                     ticket_id=self.aggroot.identifier,
                                                     member_id=member_id
                                                 ))
        for assignee in assignees:
            await self.statemgr.invalidate_one('ticket-assignee', assignee._id)
        return {"removed": True}

    @action('comment-added-to-ticket', resources='ticket')
    async def add_ticket_comment(self, /, comment_id: str):
        """Add comment to ticket"""
        record = self.init_resource(
            "ticket-comment",
            {
                "ticket_id": self.aggroot.identifier,
                "comment_id": comment_id
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action('participant-added-to-ticket', resources='ticket')
    async def add_ticket_participant(self, /, participant_id: str):
        """Add participant to ticket"""
        record = self.init_resource(
            "ticket-participant",
            {
                "ticket_id": self.aggroot.identifier,
                "participant_id": participant_id
            },
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action('tag-added-to-ticket', resources='ticket')
    async def add_ticket_tag(self, /, tag_id: str):
        """Add tag to ticket"""
        record = self.init_resource(
            "ticket-tag",
            {
                "ticket_id": self.aggroot.identifier,
                "tag_id": tag_id
            },
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action('tag-removed-from-ticket', resources='ticket')
    async def remove_ticket_tag(self, /, tag_id: str):
        """Remove tag from ticket"""
        tags = await self.statemgr.find_all('ticket-tag',
                                            where=dict(
                                                ticket_id=self.aggroot.identifier,
                                                tag_id=tag_id
                                            ))
        for tag in tags:
            await self.statemgr.invalidate_one('ticket-tag', tag._id)
        return {"removed": True}

    # =========== Tag Context ============
    @action("tag-created", resources="tag")
    async def create_tag(self, /, data):
        """Create a new tag"""
        record = self.init_resource(
            "tag",
            serialize_mapping(data),
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action("tag-updated", resources="tag")
    async def update_tag(self, /, data):
        """Update tag"""
        tag = self.rootobj
        await self.statemgr.update(tag, **serialize_mapping(data))
        return tag

    @action("tag-deleted", resources="tag")
    async def delete_tag(self, /):
        """Delete tag"""
        tag = self.rootobj
        if not tag:
            raise ValueError("Tag not found")
        await self.statemgr.invalidate(tag)
        return {"deleted": True}
