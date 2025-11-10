from datetime import datetime
from typing import Optional

MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# === Attribute & Value Helpers ===
def safe_getattr(obj, attr, default=None):
    """Trả về giá trị của attr, hỗ trợ cả object và dict."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)


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


def map_linear_priority_to_enum(priority_int: Optional[int]) -> Optional[str]:
    """Ánh xạ Linear numeric priority sang PriorityEnum (dạng string)."""
    if priority_int is None:
        return "MEDIUM"

    priority_map = {
        1: "CRITICAL",
        2: "HIGH",
        3: "MEDIUM",
        4: "LOW",
    }

    return priority_map.get(priority_int, "MEDIUM")


def parse_start_date(start_str: Optional[str]) -> datetime:
    """Chuyển đổi YYYY-MM-DD string sang datetime, nếu lỗi thì dùng now()."""
    if not start_str:
        return datetime.now()
    try:
        return datetime.strptime(start_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return datetime.now()


def calculate_duration(start_str: Optional[str], target_str: Optional[str]) -> str:
    """Tính toán thời lượng (duration) dạng ISO 8601 (ví dụ: P9D)."""
    default_duration = "P9D"
    if not start_str or not target_str:
        return default_duration
    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        target_date = datetime.strptime(target_str, "%Y-%m-%d").date()
        if target_date <= start_date:
            return default_duration
        delta = target_date - start_date
        return f"P{delta.days}D"
    except (ValueError, TypeError):
        return default_duration


def extract_mentions(content: str) -> list[dict]:
    """Extract mentions from the content string."""
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
