"""
RFX Discuss Type Definitions
=============================
Enums and type definitions for the discussion system.
"""
from enum import Enum


class FlagStatusEnum(str, Enum):
    """Comment flag status"""
    PENDING = "pending"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


class FlagReasonEnum(str, Enum):
    """Common flag reasons"""
    SPAM = "spam"
    INAPPROPRIATE = "inappropriate"
    HARASSMENT = "harassment"
    OFFENSIVE = "offensive"
    OFF_TOPIC = "off_topic"
    MISINFORMATION = "misinformation"
    OTHER = "other"


class ResolutionActionEnum(str, Enum):
    """Actions taken when resolving flags"""
    NO_ACTION = "no_action"
    WARNING_ISSUED = "warning_issued"
    COMMENT_HIDDEN = "comment_hidden"
    COMMENT_DELETED = "comment_deleted"
    USER_SUSPENDED = "user_suspended"
    USER_BANNED = "user_banned"


class AttachmentTypeEnum(str, Enum):
    """Comment attachment types"""
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    LINK = "link"
    OTHER = "other"


class ReactionTypeEnum(str, Enum):
    """Comment reaction types"""
    LIKE = "LIKE"
    LOVE = "LOVE"
    LAUGH = "LAUGH"
    WOW = "WOW"
    SAD = "SAD"
    ANGRY = "ANGRY"
    THINKING = "THINKING"
    CELEBRATE = "CELEBRATE"


__all__ = [
    "FlagStatusEnum",
    "FlagReasonEnum",
    "ResolutionActionEnum",
    "AttachmentTypeEnum",
    "ReactionTypeEnum",
]