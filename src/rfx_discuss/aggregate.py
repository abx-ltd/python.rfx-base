from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from typing import Optional
from datetime import datetime
from rfx_discuss import logger
from .types import Availability, SyncStatus
from . import config


class RFXDiscussAggregate(Aggregate):
    """CPO Portal Aggregate Root - Handles  ticket, comment, external """

    

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
            
