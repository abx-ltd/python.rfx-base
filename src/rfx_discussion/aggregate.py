from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from typing import Optional
from datetime import datetime
from rfx_discussion import logger
from .types import Availability, SyncStatus
from . import config
from .service import LinearService

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
            status="NEW",
            organization_id=self.context.organization_id,
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    # =========== Ticket (Ticket Context) ============
    @action('ticket-created', resources='ticket')
    async def create_ticket(self, /, data):
        """Create a new ticket tied to project"""
        data_result=serialize_mapping(data)
        data_result.pop("project_id", None)
        data_result.pop("sync_linear", None)

        record = self.init_resource(
            "ticket",
            data_result,
            _id=self.aggroot.identifier,
            status="NEW",
            sync_status=SyncStatus.PENDING,
            is_inquiry=False,
            organization_id=self.context.organization_id
        )
        await self.statemgr.insert(record)
        return record

    @action('ticket-updated', resources='ticket')
    async def update_ticket_info(self, /, data):
        """Update ticket information"""
        ticket = self.rootobj

        if data.status:
            status = await self.statemgr.find_one("status", where=dict(
                entity_type="ticket",
            ))

            from_status_key = await self.statemgr.find_one("status-key", where=dict(
                status_id=status._id,
                key=ticket.status
            ))
            to_status_key = await self.statemgr.find_one("status-key", where=dict(
                status_id=status._id,
                key=data.status
            ))

            if not to_status_key:
                raise ValueError("Invalid status")

            transition = await self.statemgr.has_status_transition(status._id, from_status_key._id, to_status_key._id)
            if not transition:
                raise ValueError(
                    "Invalid status, Can not transition to this status")
                
        data_result=serialize_mapping(data)
        data_result.pop("sync_linear", None)

        await self.statemgr.update(ticket, **data_result)

    @action('ticket-removed', resources='ticket')
    async def remove_ticket(self, /):
        """Remove ticket"""
        ticket = self.rootobj
        if not ticket.is_inquiry:
            raise ValueError(
                "You cannot remove a ticket that attached to a project")
        await self.statemgr.invalidate(ticket)

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
        tags = await self.statemgr.find_all('ticket-tag', where=dict(
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
            organization_id=self.context.organization_id,
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

    # =========== Comment Context ============
    @action("comment-created", resources="comment")
    async def create_comment(self, /, data):
        """Create a new comment"""
        record = self.init_resource(
            "comment",
            serialize_mapping(data),
            _id=UUID_GENR(),
            organization_id=self.context.organization_id
        )
        await self.statemgr.insert(record)
        return record

    @action("comment-updated", resources="comment")
    async def update_comment(self, /, data):
        """Update comment"""
        data_result=serialize_mapping(data)
        data_result.pop("sync_linear", None)
        await self.statemgr.update(self.rootobj, **data_result)

    @action("comment-deleted", resources="comment")
    async def delete_comment(self, /):
        """Delete comment"""
        comment = self.rootobj
        await self.statemgr.invalidate(comment)

    @action("reply-to-comment", resources="comment")
    async def reply_to_comment(self, /, data):
        """Reply to comment"""
        comment = self.rootobj

        ticket_comment = await self.statemgr.find_one("ticket-comment", where=dict(comment_id=comment._id))

        parent_id = comment._id
        depth = comment.depth + 1
        if comment.depth >= config.COMMENT_NESTED_LEVEL:
            depth = comment.depth
            parent_id = comment.parent_id

        master_id = comment.master_id
        if not master_id:
            master_id = comment._id

        new_comment = self.init_resource(
            "comment",
            serialize_mapping(data),
            _id=UUID_GENR(),
            parent_id=parent_id,
            depth=depth,
            master_id=master_id
        )

        new_ticket_comment = self.init_resource(
            "ticket-comment",
            {
                "ticket_id": ticket_comment.ticket_id,
                "comment_id": new_comment._id
            },
            _id=UUID_GENR()
        )

        await self.statemgr.insert(new_comment)
        await self.statemgr.insert(new_ticket_comment)
        return new_comment

    # =========== Ticket Comment (Ticket Context) ============
    @action("ticket-comment-created", resources="ticket")
    async def create_ticket_comment(self, /, data):
        """Create a new comment for a ticket"""
        ticket = await self.statemgr.find_one("ticket", where=dict(_id=self.aggroot.identifier))
        if not ticket:
            raise ValueError("Ticket not found")
        data_result = serialize_mapping(data)
        data_result.pop("sync_linear", None)

        record = self.init_resource(
            "comment",
            data_result,
            organization_id=self.context.organization_id,
            _id=UUID_GENR()
        )

        ticket_comment = self.init_resource(
            "ticket-comment",
            {
                "ticket_id": self.aggroot.identifier,
                "comment_id": record._id
            },
        )

        await self.statemgr.insert(record)
        await self.statemgr.insert(ticket_comment)
        return record

    # =========== Status Context ============
    @action("status-created", resources="status")
    async def create_status(self, /, data):
        """Create a new workflow"""
        record = self.init_resource(
            "status",
            serialize_mapping(data),
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action("status-key-created", resources="status")
    async def create_status_key(self, /, data):
        """Create a new status key"""
        status = self.rootobj
        record = self.init_resource(
            "status-key",
            serialize_mapping(data),
            status_id=status._id,
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record

    @action("status-transition-created", resources="status")
    async def create_status_transition(self, /, data):
        """Create a new status transition"""
        status = self.rootobj
        record = self.init_resource(
            "status-transition",
            serialize_mapping(data),
            status_id=status._id,
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record


#----------- Agg Ticket Integration (Ticket Context) -----------
    @action("create-ticket-integration", resources="ticket")
    async def create_ticket_integration(self, /, data):
        """Create a new ticket integration"""
        ticket = await self.statemgr.find_one("ticket", where=dict(_id=self.aggroot.identifier))
        if not ticket:
            raise ValueError("Ticket not found")

        record = self.init_resource(
            "ticket-integration",
            serialize_mapping(data),
            ticket_id=self.aggroot.identifier,
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        
    @action("update-ticket-integration", resources="ticket")
    async def update_ticket_integration(self, /, data):
        """Update ticket integration"""
        ticket = await self.statemgr.find_one("ticket", where=dict(_id=self.aggroot.identifier))
        if not ticket:
            raise ValueError("Ticket not found")
        ticket_integration = await self.statemgr.find_one("ticket-integration", where=dict(
            provider=data.provider,
            ticket_id=self.aggroot.identifier,
            external_id=data.external_id
            ))
        if not ticket_integration:
            raise ValueError("Ticket integration not found")
        await self.statemgr.update(ticket_integration, **serialize_mapping(data))
    
    @action("remove-ticket-integration", resources="ticket")
    async def remove_ticket_integration(self, /, data):
        """Remove ticket integration"""
        ticket = await self.statemgr.find_one("ticket", where=dict(_id=self.aggroot.identifier))
        if not ticket:
            raise ValueError("Ticket not found")
        ticket_integration = await self.statemgr.find_one("ticket-integration", where=dict(
            provider=data.provider,
            ticket_id=self.aggroot.identifier,
            external_id=data.external_id
            ))
        if not ticket_integration:
            raise ValueError("Ticket integration not found")
        
        # Call LinearService to delete the issue in Linear
        LinearService.delete_issue(ticket_integration.external_id)
        
        await self.statemgr.invalidate(ticket_integration)
        return {"removed": True}
    
    @action("sync-ticket-integration", resources="ticket")
    async def sync_ticket_integration(self, /, data):
        """Sync a ticket to Linear"""
        ticket = await self.statemgr.find_one("ticket", where=dict(_id=self.aggroot.identifier))
        if not ticket:
            raise ValueError("Ticket not found")
        ticket_integration = await self.statemgr.find_one("ticket-integration", where=dict(
            provider=data.provider,
            ticket_id=self.aggroot.identifier,
            external_id=data.external_id
            ))
        
        if not ticket_integration:
            record = self.init_resource(
                "ticket-integration",
                serialize_mapping(data),
                ticket_id=self.aggroot.identifier,
                _id=UUID_GENR()
            )
            await self.statemgr.insert(record)
        else: 
            await self.statemgr.update(ticket_integration, **serialize_mapping(data))
            
            
    #----------- Comment Integration (Comment Context) -----------
    @action("create-comment-integration", resources="comment")
    async def create_comment_integration(self, /, data):
        """Create a new comment integration"""
        comment = await self.statemgr.find_one("comment", where=dict(_id=self.aggroot.identifier))
        if not comment:
            raise ValueError("Comment not found")

        record = self.init_resource(
            "comment-integration",
            serialize_mapping(data),
            comment_id=self.aggroot.identifier,
            _id=UUID_GENR()
        )
        await self.statemgr.insert(record)
        return record
        
    @action("update-comment-integration", resources="comment")
    async def update_comment_integration(self, /, data):
        """Update comment integration"""
        comment = await self.statemgr.find_one("comment", where=dict(_id=self.aggroot.identifier))
        if not comment:
            raise ValueError("Comment not found")
        
        comment_integration = await self.statemgr.find_one("comment-integration", where=dict(
            provider=data.provider,
            comment_id=self.aggroot.identifier,
            external_id=data.external_id
        ))
        
        if not comment_integration:
            raise ValueError("Comment integration not found")
        await self.statemgr.update(comment_integration, **serialize_mapping(data))
        return comment_integration

    @action("remove-comment-integration", resources="comment")
    async def remove_comment_integration(self, /, data):
        """Remove comment integration"""
        logger.warn(f"Attempting to remove integration with payload: {data}")
        comment_integration = await self.statemgr.find_one("comment-integration", where=dict(
            provider=data.provider,
            #comment_id=self.aggroot.identifier,
            external_id=data.external_id
        ))
        
        if not comment_integration:
            raise ValueError("Comment integration not found")
        
        # Call LinearService to delete the comment in Linear
        LinearService.delete_comment(comment_integration.external_id)
        
        await self.statemgr.invalidate(comment_integration)
        return {"removed": True}
            
