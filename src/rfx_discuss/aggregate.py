from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from rfx_discuss import logger
from rfx_schema.rfx_discuss.types import ReactionTypeEnum
from . import config


class RFXDiscussAggregate(Aggregate):
    """CPO Portal Aggregate Root - Handles  ticket, comment, external"""

    # =========== Comment Context ============
    @action("comment-created", resources="comment")
    async def create_comment(self, /, data):
        """Create a new comment"""
        organization_id = self.context.organization_id
        data = serialize_mapping(data)
        parent_id = data.get("parent_id")
        
        if parent_id:
            parent_comment = await self.statemgr.find_one(
                "comment", where={"_id": parent_id}
            )
            depth = parent_comment.depth + 1

            if parent_comment.depth >= config.COMMENT_NESTED_LEVEL:
                depth = parent_comment.depth
            
            data.update(
                {
                    "parent_id": parent_id,
                    "depth": depth,
                    "resource": parent_comment.resource,
                    "resource_id": parent_comment.resource_id,
                    "master_id": parent_comment.master_id,
                }
            )
        else:
            if not data.get("resource") or not data.get("resource_id"):
                raise ValueError("resource and resource_id must be provided for top-level comments")
            data.setdefault("depth", 0)
            data.setdefault("master_id", UUID_GENR())
        record = self.init_resource(
            "comment",
            data,
            master_id=data["master_id"],
            _id=UUID_GENR(),
            organization_id=organization_id,
        )
        await self.statemgr.insert(record)
        return record

    @action("comment-updated", resources="comment")
    async def update_comment(self, /, data):
        """Update comment"""
        data_result = serialize_mapping(data)
        await self.statemgr.update(self.rootobj, **data_result)

    @action("comment-deleted", resources="comment")
    async def delete_comment(self, /):
        """Delete comment"""
        comment = self.rootobj
        await self.statemgr.invalidate(comment)


    @action("attach-file", resources="comment")
    async def attach_file_to_comment(self, /, data):
        """Attach file to comment"""
        comment = self.rootobj
        attachment_data = serialize_mapping(data)
        attachment_data["comment_id"] = comment._id
        attachment = self.init_resource(
            "comment_attachment",
            attachment_data,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(attachment)
        return attachment

    @action("update-attachment", resources="comment")
    async def update_attachment(self, /, data):
        """Update attachment metadata"""
        comment = self.rootobj
        if not comment:
            raise ValueError("Comment not found")

        attachment = await self.statemgr.find_one(
            "comment_attachment",
            where={"_id": data.attachment_id, "comment_id": comment._id},
        )
        if not attachment:
            raise ValueError(f"Attachment not found: {data.attachment_id}")
        data_result = serialize_mapping(data)
        data_result.pop("attachment_id", None)
        await self.statemgr.update(attachment, **data_result)

    @action("delete-attachment", resources="comment")
    async def delete_attachment(self, /, data):
        """Delete attachment from comment"""
        comment = self.rootobj
        if not comment:
            raise ValueError("Comment not found")
        attachment = await self.statemgr.find_one(
            "comment_attachment",
            where={"_id": data.attachment_id, "comment_id": comment._id},
        )
        if not attachment:
            raise ValueError(f"Attachment not found: {data.attachment_id}")
        await self.statemgr.invalidate(attachment)

    @action("add-reaction", resources="comment")
    async def add_reaction(self, /, data):
        """Add reaction to comment"""
        comment = self.rootobj
        user_id = self.context.profile_id
        reaction_data = serialize_mapping(data)
        reaction_data["comment_id"] = comment._id
        reaction_data["user_id"] = user_id
        check_existing = await self.statemgr.exist(
            "comment_reaction",
            where={
                "comment_id": comment._id,
                "user_id": user_id,
            },
        )
        if check_existing:
            raise ValueError(
                f"Reaction already exists for user {user_id} on comment {comment._id}"
            )
        reaction = self.init_resource(
            "comment_reaction",
            reaction_data,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(reaction)
        return reaction

    @action("remove-reaction", resources="comment")
    async def remove_reaction(self, /):
        """Remove reaction from comment"""
        user_id = self.context.profile_id
        reaction = await self.statemgr.find_one(
            "comment_reaction",
            where={
                "comment_id": self.rootobj._id,
                "user_id": user_id,
            },
        )
        if not reaction:
            raise ValueError(
                f"Reaction not found for user {user_id} on comment {self.rootobj._id}"
            )
        await self.statemgr.invalidate(reaction)

    @action("flag-comment", resources="comment")
    async def flag_comment(self, /, data):
        """Flag comment"""
        comment = self.rootobj
        flag_data = serialize_mapping(data)
        flag_data["comment_id"] = comment._id
        flag_data["reported_by_user_id"] = self.context.profile_id
        flag = self.init_resource(
            "comment_flag",
            flag_data,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(flag)
        return flag

    @action("resolve-flag", resources="comment")
    async def resolve_flag(self, /, data):
        """Resolve flag"""
        comment = self.rootobj
        if not comment:
            raise ValueError(f"Comment not found: {self.rootobj._id}")
        flag = await self.statemgr.find_one("comment_flag", where={"_id": data.flag_id})
        if not flag:
            raise ValueError(f"Flag not found: {data.flag_id}")

        resolution = self.init_resource(
            "comment_flag_resolution",
            {
                "flag_id": flag._id,
                "resolved_by_user_id": self.context.profile_id,
                "resolution_action": data.resolution_action,
                "resolution_note": data.resolution_note,
            },
            _id=UUID_GENR(),
        )
        update_status = {}
        update_status["status"] = "resolved"
        await self.statemgr.update(flag, **update_status)

        await self.statemgr.insert(resolution)
        return resolution

    @action("subscribe-comment", resources="comment")
    async def subscribe_to_comment(self, /):
        """Subscribe to comment"""
        comment = self.rootobj
        subscription_data = {
            "comment_id": comment._id,
            "user_id": self.context.profile_id,
        }
        existing_subscription = await self.statemgr.find_one(
            "comment_subscription",
            where={
                "comment_id": comment._id,
                "user_id": self.context.profile_id,
            },
        )
        if not existing_subscription:
            subscription = self.init_resource(
                "comment_subscription",
                subscription_data,
                _id=UUID_GENR(),
            )
            await self.statemgr.insert(subscription)
        elif not existing_subscription.is_active:
            await self.statemgr.update(existing_subscription, is_active=True)
        elif existing_subscription.is_active:
            raise ValueError(
                f"Already subscribed to comment {comment._id} by user {self.context.profile_id}"
            )

    @action("unsubscribe-comment", resources="comment")
    async def unsubscribe_from_comment(self, /):
        """Unsubscribe from comment"""
        comment = self.rootobj
        subscription = await self.statemgr.find_one(
            "comment_subscription",
            where={
                "comment_id": comment._id,
                "user_id": self.context.profile_id,
                "is_active": True,
            },
        )
        if not subscription:
            raise ValueError(
                f"No active subscription found for comment {comment._id} by user {self.context.profile_id}"
            )
        await self.statemgr.update(subscription, is_active=False)
