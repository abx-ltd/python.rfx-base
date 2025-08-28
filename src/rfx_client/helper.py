from datetime import timedelta
from dateutil.relativedelta import relativedelta
import isodate


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


def parse_duration_for_db(duration_str: str):
    """
    Trả về:
    - parsed_delta: để tính target_date chính xác
    - duration_text: lưu human-readable (vd: "1 year 2 months 3 days")
    - duration_interval: timedelta gần đúng để lưu Postgres INTERVAL
    """
    dur = isodate.parse_duration(duration_str)

    if isinstance(dur, isodate.Duration):
        parsed_delta = relativedelta(years=dur.years or 0,
                                     months=dur.months or 0,
                                     days=dur.tdelta.days if dur.tdelta else 0,
                                     seconds=dur.tdelta.seconds if dur.tdelta else 0)
        # duration_text human-readable
        parts = []
        if dur.years:
            parts.append(f"{dur.years} year{'s' if dur.years > 1 else ''}")
        if dur.months:
            parts.append(f"{dur.months} month{'s' if dur.months > 1 else ''}")
        if dur.tdelta:
            if dur.tdelta.days:
                parts.append(
                    f"{dur.tdelta.days} day{'s' if dur.tdelta.days > 1 else ''}")
            if dur.tdelta.seconds:
                hours, rem = divmod(dur.tdelta.seconds, 3600)
                minutes, seconds = divmod(rem, 60)
                if hours:
                    parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
                if minutes:
                    parts.append(
                        f"{minutes} minute{'s' if minutes > 1 else ''}")
                if seconds:
                    parts.append(
                        f"{seconds} second{'s' if seconds > 1 else ''}")
        duration_text = ' '.join(parts)

        # duration_interval gần đúng cho Postgres
        approx_days = (dur.years or 0) * 365 + (dur.months or 0) * \
            30 + (dur.tdelta.days if dur.tdelta else 0)
        approx_seconds = (dur.tdelta.seconds if dur.tdelta else 0)
        duration_interval = timedelta(
            days=int(approx_days), seconds=int(approx_seconds))
    else:
        # Chỉ timedelta thuần
        parsed_delta = relativedelta(days=dur.days, seconds=dur.seconds)
        duration_text = f"{dur.days} day{'s' if dur.days != 1 else ''}"
        duration_interval = dur

    return parsed_delta, duration_text, duration_interval
