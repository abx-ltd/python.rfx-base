"""
Notification providers module

Self-hosted infrastructure providers:
- SMTPEmailProvider: Connects to local SMTP server (Postfix/Haraka)
- KannelSMSProvider: Connects to local Kannel SMS gateway
"""
from .base import NotificationProviderBase
from .email import SMTPEmailProvider
from .sms import KannelSMSProvider

__all__ = [
    'NotificationProviderBase',
    'SMTPEmailProvider',
    'KannelSMSProvider',
]
