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
        data_result = serialize_mapping(data)
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
        await self.statemgr.update(self.rootobj, **data_result)

    @action("comment-deleted", resources="comment")
    async def delete_comment(self, /):
        """Delete comment"""
        comment = self.rootobj
        await self.statemgr.invalidate(comment)

    @action("reply-to-comment", resources="comment")
    async def reply_to_comment(self, /, data):
        """Reply to comment"""
        parent_comment = self.rootobj
        profile_id = self.get_context().profile_id
        organization_id = self.get_context().organization_id
        
        logger.info(f"Creating reply to comment: {parent_comment._id}")
        
       
        parent_id = parent_comment._id
        depth = parent_comment.depth + 1
        
        
        if parent_comment.depth >= config.COMMENT_NESTED_LEVEL:
            depth = parent_comment.depth
            parent_id = parent_comment.parent_id
            logger.info(f"Max nest level reached, attaching to parent: {parent_id}")
        
        
        reply_data = serialize_mapping(data)
        reply_data.update({
            "parent_id": parent_id,
            "depth": depth,
            "resource": parent_comment.resource,
            "resource_id": parent_comment.resource_id
        })
        
        
        new_comment = self.init_resource(
            "comment",
            reply_data,
            _id=UUID_GENR(),
            organization_id=organization_id
        )
        
        await self.statemgr.insert(new_comment)
        return new_comment