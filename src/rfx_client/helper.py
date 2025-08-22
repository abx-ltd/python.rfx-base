async def get_project_member_user_ids(stm, project_id: str) -> tuple[list[str], dict]:
    """
    Reusable helper function to get user IDs of project members.

    Args:
        stm: Stream/State manager for database operations
        project_id: The ID of the project

    Returns:
        List of user IDs for all project members
    """
    project_data = await stm.find_one("_project", where=dict(_id=project_id))
    member_ids = project_data.members if hasattr(
        project_data, 'members') else []
    members = await stm.get_profiles(member_ids) if member_ids else []
    user_ids = [member.user_id for member in members]
    return user_ids, project_data
