"""
Bootstrap helpers for the rfx_notify provider runtime.
"""
from .providers import SMTPEmailProvider, SendGridProvider, TwilioSMSProvider
from . import config, logger


def bootstrap_providers():
    """
    Instantiate available provider clients based on notify config.
    """
    providers = {}

    if config.SENDGRID_API_KEY:
        providers["sendgrid"] = SendGridProvider()
    else:
        logger.warning("SendGrid provider disabled: SENDGRID_API_KEY not set")

    if config.SMTP_HOST and config.SMTP_USERNAME and config.SMTP_PASSWORD:
        providers["smtp"] = SMTPEmailProvider()
    else:
        logger.warning("SMTP provider disabled: missing SMTP credentials/host")

    if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN and config.TWILIO_FROM_NUMBER:
        providers["twilio"] = TwilioSMSProvider()
    else:
        logger.warning("Twilio provider disabled: missing SID/auth token/from_number")

    enabled = ", ".join(providers.keys()) if providers else "none"
    logger.info("Notify providers bootstrapped: %s", enabled)
    return providers
