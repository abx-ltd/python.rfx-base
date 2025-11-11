"""
Bootstrap helpers for the rfx_notify provider runtime.

This module initializes self-hosted notification providers (SMTP and Kannel).
"""
from .providers.email import SMTPEmailProvider
from .providers.sms import KannelSMSProvider
from . import config, logger


def bootstrap_providers():
    """
    Instantiate available provider clients based on notify config.

    Uses self-hosted infrastructure:
    - SMTP for email (connects to local SMTP server like Postfix/Haraka)
    - Kannel for SMS (connects to local Kannel SMS gateway)
    """
    providers = {}

    # ========================================================================
    # SELF-HOSTED EMAIL PROVIDER
    # ========================================================================
    if config.SMTP_HOST:
        providers["smtp"] = SMTPEmailProvider()
        logger.info(
            f"Self-hosted SMTP provider enabled: {config.SMTP_HOST}:{config.SMTP_PORT or 25}"
        )
    else:
        logger.warning("SMTP provider disabled: SMTP_HOST not configured")

    # ========================================================================
    # SELF-HOSTED SMS PROVIDER
    # ========================================================================
    if config.KANNEL_HOST:
        providers["kannel"] = KannelSMSProvider()
        logger.info(
            f"Self-hosted Kannel SMS provider enabled: {config.KANNEL_HOST}:{config.KANNEL_PORT or 13013}"
        )
    else:
        logger.warning("Kannel provider disabled: KANNEL_HOST not configured")

    # Log summary
    if providers:
        enabled = ", ".join(providers.keys())
        logger.info(f"Notification providers bootstrapped: {enabled}")
    else:
        logger.error("No notification providers enabled! Check configuration.")

    return providers
