from datetime import datetime
from typing import Optional, Any


MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# === Attribute & Value Helpers ===
def safe_getattr(obj: Any, name: str, default=None):
    """Lấy giá trị thuộc tính an toàn, tránh AttributeError."""
    return getattr(obj, name, default)


# === Enum & Mapping ===
def map_priority(priority) -> int:
    """Chuyển Priority Enum/String sang Linear numeric priority."""
    value = priority.value if hasattr(priority, "value") else str(priority)
    return {
        "CRITICAL": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "LOW": 4,
    }.get(value.upper(), 3)


# === Date Normalization ===
def parse_date(date_str: Optional[str]) -> Optional[str]:
    """Chuẩn hóa định dạng date về YYYY-MM-DD, hoặc None nếu lỗi."""
    if not date_str:
        return None
    try:
        clean = str(date_str).replace(" GMT", "")
        return datetime.fromisoformat(clean).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def extract_mentions(content: str) -> list:
    """Extract user mentions from comment content."""
    import re

    mentions = []
    pattern_rich = r"@\[([^\]]+)\]\(([a-f0-9\-]{36})\)"
    for match in re.finditer(pattern_rich, content):
        mentions.append(
            {
                "display_name": match.group(1),
                "user_id": match.group(2),
                "position": match.start(),
                "full_match": match.group(0),
            }
        )
    pattern_simple = r"@(\w+)\(([a-f0-9\-]{36})\)"
    for match in re.finditer(pattern_simple, content):
        user_id = match.group(2)
        if not any(m["user_id"] == user_id for m in mentions):
            mentions.append(
                {
                    "display_name": match.group(1),
                    "user_id": user_id,
                    "position": match.start(),
                    "full_match": match.group(0),
                }
            )
    pattern_minimal = r"@\(([a-f0-9\-]{36})\)"
    for match in re.finditer(pattern_minimal, content):
        user_id = match.group(1)
        if not any(m["user_id"] == user_id for m in mentions):
            mentions.append(
                {
                    "display_name": None,
                    "user_id": user_id,
                    "position": match.start(),
                    "full_match": match.group(0),
                }
            )
    return mentions


async def get_mentioned_users(stm, user_ids: list[str]) -> list[dict]:
    if not user_ids:
        return []
    users = await stm.get_profiles(user_ids)

    users_info = []
    for user in users:
        users_info.append(
            {
                "id": user._id,
                "name": f"{user.name__given} {user.name__family}",
            }
        )
    return users_info
