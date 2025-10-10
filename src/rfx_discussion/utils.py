from datetime import datetime
from typing import Optional, Any

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
