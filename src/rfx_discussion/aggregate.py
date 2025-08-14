from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from typing import Optional
from datetime import datetime
from rfx_discussion import logger
from .types import Availability, SyncStatus


class RFXDiscussionAggregate(Aggregate):
    """CPO Portal Aggregate Root - Handles  ticket, comment, external """

    # =========== Ticket Type (Ticket Context) ============
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

    @action("ticket-type-updated", resources="ticket")
    async def update_ticket_type(self, /, data):
        """Update a ticket type"""
        ticket_type = await self.statemgr.find_one("ref--ticket-type", where=dict(_id=data.ticket_type_id))
        if not ticket_type:
            raise ValueError("Ticket type not found")
        updated_data = serialize_mapping(data)
        updated_data.pop("ticket_type_id")
        await self.statemgr.update(ticket_type, **updated_data)
        return ticket_type

    @action("ticket-type-deleted", resources="ticket")
    async def delete_ticket_type(self, /, data):
        """Delete a ticket type"""
        ticket_type = await self.statemgr.find_one("ref--ticket-type", where=dict(_id=data.ticket_type_id))
        if not ticket_type:
            raise ValueError("Ticket type not found")
        await self.statemgr.invalidate_one("ref--ticket-type", data.ticket_type_id)
        return {"deleted": True}

    # =========== Inquiry (Ticket Context) ============

    @action('inquiry-created', resources='ticket')
    async def create_inquiry(self, /, data):
        """Create a new inquiry"""

        record = self.init_resource(
            "ticket",
            serialize_mapping(data),
            status="DRAFT",
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    # =========== Ticket (Ticket Context) ============
    @action('ticket-created', resources='ticket')
    async def create_ticket(self, /, data):
        """Create a new ticket tied to project"""
        logger.info(f"Create a new ticket tied to project: {data}")

        record = self.init_resource(
            "ticket",
            serialize_mapping(data),
            _id=self.aggroot.identifier,
            status="DRAFT",
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

    # =========== Ticket Assignee (Ticket Context) ============

    @action('member-assigned-to-ticket', resources='ticket')
    async def assign_member_to_ticket(self, /, data):
        """Assign member to ticket"""
        ticket_assignee = await self.statemgr.find_one('ticket-assignee',
                                                       where=dict(ticket_id=self.aggroot.identifier))
        if ticket_assignee and ticket_assignee.member_id == data.member_id:
            raise ValueError("Member already assigned to ticket")

        if ticket_assignee:
            await self.statemgr.invalidate_one('ticket-assignee', ticket_assignee._id)

        record = self.init_resource(
            "ticket-assignee",
            {
                "ticket_id": self.aggroot.identifier,
                "member_id": data.member_id
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action('member-removed-from-ticket', resources='ticket')
    async def remove_member_from_ticket(self, /, member_id: str):
        """Remove member from ticket"""
        assignee = await self.statemgr.find_one('ticket-assignee',                                                 where=dict(
            ticket_id=self.aggroot.identifier,
            member_id=member_id
        ))
        if not assignee:
            raise ValueError("Assignee not found")
        await self.statemgr.invalidate_one('ticket-assignee', assignee._id)
        return {"removed": True}

    # =========== Ticket Participant (Ticket Context) ============

    @action('participant-added-to-ticket', resources='ticket')
    async def add_ticket_participant(self, /, participant_id: str):
        """Add participant to ticket"""
        ticket_participant = await self.statemgr.find_one('ticket-participant', where=dict(ticket_id=self.aggroot.identifier,
                                                                                           participant_id=participant_id))
        if ticket_participant:
            raise ValueError("Participant already added to ticket")

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

    @action('participant-removed-from-ticket', resources='ticket')
    async def remove_ticket_participant(self, /, participant_id: str):
        """Remove participant from ticket"""
        participant = await self.statemgr.find_one('ticket-participant',                                                   where=dict(
            ticket_id=self.aggroot.identifier,
            participant_id=participant_id
        ))
        if not participant:
            raise ValueError("Participant not found")
        await self.statemgr.invalidate_one('ticket-participant', participant._id)
        return {"removed": True}

    # =========== Ticket Tag (Ticket Context) ============
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
