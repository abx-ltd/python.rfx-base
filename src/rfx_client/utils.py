from datetime import datetime
from typing import Optional


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
