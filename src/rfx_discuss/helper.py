from . import utils, logger, config


async def _handle_mentions(agg, stm, content: str):
    mentions = utils.extract_mentions(content)
    logger.info(f"Extracted mentions: {mentions}")

    if not mentions:
        return
    unique_user_ids = {mention["user_id"] for mention in mentions}
    if not unique_user_ids:
        return
    context = agg.get_context()
    profile_id = context.profile_id
    profile = await stm.get_profile(profile_id)
    users_info = await utils.get_mentioned_users(stm, list(unique_user_ids))

    if config.MESSAGE_ENABLED and users_info:
        message_content = f"{profile.name__given} mentioned you in a comment."
        message_subject = "Mention In Comment"

        service_proxy = context.service_proxy
        await service_proxy.msg_client.send(
            f"{config.MESSAGE_NAMESPACE}:send-message",
            command="send-message",
            resource="message",
            payload={
                "recipients": [str(user_id["id"]) for user_id in users_info],
                "subject": message_subject,
                "message_type": "NOTIFICATION",
                "priority": "MEDIUM",
                "content": message_content,
                "content_type": "TEXT",
            },
            _headers={},
            _context={
                "audit": {
                    "user_id": str(context.profile_id),
                    "profile_id": str(context.profile_id),
                    "organization_id": str(context.organization_id),
                    "realm": context.realm,
                }
            },
        )
