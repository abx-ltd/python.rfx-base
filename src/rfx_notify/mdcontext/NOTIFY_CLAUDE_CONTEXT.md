# RFX Notify Service - Context for Claude

**Context for Claude AI Assistant**: Use this information when helping users integrate or work with the rfx_notify service.

## Service Overview

`rfx_notify` is a production-ready multi-channel notification service built on the Fluvius domain-driven design framework. It handles Email, SMS, Push, Webhook, and In-app notifications with provider abstraction, template management, and comprehensive delivery tracking.

**Location**: `/src/rfx_notify/`
**Schema**: `rfx_notify` (PostgreSQL)
**Framework**: Fluvius (Domain-Driven Design with CQRS)

## Core Capabilities

1. **Multi-Channel**: EMAIL, SMS, PUSH, WEBHOOK, INAPP
2. **Multi-Provider**: SMTP, SendGrid (email); Twilio (SMS); Extensible
3. **Templates**: Jinja2, Text, Static engines with versioning and localization
4. **Delivery Tracking**: Per-attempt logging with retry mechanisms
5. **User Preferences**: Channel-specific opt-in/out, quiet hours, frequency limits
6. **Provider Failover**: Automatic fallback between providers by priority

## Architecture Pattern

```
Command → Aggregate → Service → Provider → External API
                  ↓
               Database
                  ↓
            Query API
```

**Key Components**:
- **Aggregate** (`aggregate.py`): Business logic, domain actions
- **Service** (`service.py`): Provider routing and notification delivery
- **Providers** (`providers/`): Email (SMTP, SendGrid), SMS (Twilio)
- **Templates** (`template/`): Engine registry and template service
- **Processor** (`processor.py`): Content processing and template rendering
- **Commands** (`command.py`): SendNotification, RetryNotification, etc.
- **Queries** (`query.py`): notifications, providers, templates, logs

## Database Models

**Core Tables**:
- `notification` - Notification records (recipient, channel, content, status)
- `notification_provider` - Provider configs (name, type, credentials, priority)
- `notification_template` - Templates (key, version, locale, channel)
- `notification_delivery_log` - Delivery attempts (attempt_number, status, response)
- `notification_preference` - User preferences (channel, enabled, quiet_hours)

**Important**: Field `meta` (not `metadata` - SQLAlchemy reserved)

## Common Commands

### Send Notification
```python
# Command: send-notification
{
    "channel": "EMAIL|SMS|PUSH|WEBHOOK|INAPP",
    "recipient_id": "uuid",
    "recipients": ["email@example.com or +1234567890"],
    "subject": "Email subject (EMAIL only)",
    "body": "Message body",
    "content_type": "TEXT|HTML|MARKDOWN|JSON",
    "priority": "LOW|NORMAL|HIGH|URGENT",
    "template_key": "optional_template_key",
    "template_data": {"var": "value"},
    "scheduled_at": "2025-11-15T10:00:00Z",
    "meta": {
        "from_email": "custom@email.com",
        "cc": "cc@email.com",
        "bcc": "bcc@email.com"
    }
}
```

### Create Provider
```python
# Command: create-provider (Admin)
{
    "name": "Provider Name",
    "provider_type": "SMTP|SENDGRID|TWILIO|SES|SNS|FIREBASE|MQTT|CUSTOM",
    "channel": "EMAIL|SMS|PUSH|WEBHOOK|INAPP",
    "config": {"host": "smtp.gmail.com", "port": 587, "use_tls": true},
    "credentials": {"username": "user", "password": "pass"},
    "priority": 100,  # Lower = higher priority
    "status": "ACTIVE|INACTIVE|DISABLED|ERROR",
    "rate_limit_per_minute": 60,
    "retry_strategy": "NONE|LINEAR|EXPONENTIAL|FIBONACCI"
}
```

### Create Template
```python
# Command: create-notification-template (Admin)
{
    "key": "template_key",
    "channel": "EMAIL|SMS|etc",
    "body_template": "Hello {{name}}!",
    "subject_template": "Welcome {{name}}" (EMAIL only),
    "engine": "jinja2|text|static",
    "locale": "en",
    "content_type": "TEXT|HTML",
    "variables_schema": {"required": ["name"]},
    "tenant_id": "optional_uuid",
    "app_id": "optional_string"
}
```

### Update User Preference
```python
# Command: update-notification-preference
{
    "channel": "EMAIL|SMS|etc",
    "enabled": true,
    "email_address": "user@example.com",
    "phone_number": "+1234567890",
    "opt_in": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00",
    "quiet_hours_timezone": "America/New_York",
    "frequency_limit": {"max_per_hour": 5}
}
```

## Provider Configuration Examples

**SMTP Email**:
```python
{
    "provider_type": "SMTP",
    "channel": "EMAIL",
    "config": {
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": true,
        "from_email": "noreply@company.com"
    },
    "credentials": {
        "username": "smtp_user",
        "password": "smtp_password"
    }
}
```

**SendGrid**:
```python
{
    "provider_type": "SENDGRID",
    "channel": "EMAIL",
    "config": {"from_email": "noreply@company.com"},
    "credentials": {"api_key": "SG.xxxxx"}
}
```

**Twilio SMS**:
```python
{
    "provider_type": "TWILIO",
    "channel": "SMS",
    "config": {"from_number": "+1234567890"},
    "credentials": {
        "account_sid": "ACxxxxx",
        "auth_token": "auth_token"
    }
}
```

## Template System

**Resolution Fallback Chain**:
1. `(tenant_id, app_id, channel, locale)` - Most specific
2. `(tenant_id, app_id, channel, None)`
3. `(tenant_id, None, channel, None)`
4. `(None, None, channel, locale)`
5. `(None, None, channel, None)` - Base template

**Engines**:
- **jinja2**: Full Jinja2 syntax `{{variable}}`, filters, loops
- **text**: Simple substitution `${variable}`
- **static**: No processing

**Versioning**: Automatic version increment on updates

## Status Flow

```
PENDING → PROCESSING → SENT → DELIVERED
                    ↓
                  FAILED → RETRY (up to max_retries)
                    ↓
                REJECTED / BOUNCED
```

## Query Resources

- **notifications** - User's notifications (auth required)
- **notification-providers** - Provider list (admin only)
- **notification-delivery-logs** - Delivery attempts (admin only)
- **notification-preferences** - User preferences (auth required)
- **notification-templates** - Template list (admin only)

## Integration Patterns

**Pattern 1: Direct Command**
```python
from rfx_notify.command import SendNotification
await SendNotification().execute(payload)
```

**Pattern 2: Service Layer**
```python
from rfx_notify.service import NotificationService
service = NotificationService(stm)
result = await service.send_notification(notification)
```

**Pattern 3: With Templates**
```python
from rfx_notify.processor import NotificationContentProcessor
processor = NotificationContentProcessor(stm)
notification_data = await processor.prepare_notification_with_template(
    channel=NotificationChannelEnum.EMAIL,
    template_key="welcome",
    template_data={"name": "John"},
    recipients=["user@example.com"]
)
```

## Error Handling

All notifications track:
- `status` - Current delivery status
- `error_message` - Human-readable error
- `error_code` - Provider error code
- `retry_count` - Current retry attempt
- `failed_at` - Failure timestamp

Check delivery logs for detailed attempt history.

## Best Practices

1. **Always use templates** for repeated notifications
2. **Set up multiple providers** for redundancy (different priority)
3. **Configure rate limits** to avoid throttling
4. **Respect user preferences** (quiet hours, opt-out)
5. **Monitor delivery logs** for issues
6. **Use scheduled_at** for future notifications
7. **Track notification_id** for status checks

## Common Issues

**Problem**: Notification stuck in PENDING
- **Solution**: Check provider status is ACTIVE, verify credentials

**Problem**: Template not rendering
- **Solution**: Verify template `is_active=true`, check required variables present

**Problem**: High failure rate
- **Solution**: Check delivery logs, verify provider credentials, check rate limits

**Problem**: `metadata` field error
- **Solution**: Use `meta` field (not `metadata` - SQLAlchemy reserved)

## File Locations

```
src/rfx_notify/
├── providers/
│   ├── base.py          # NotificationProviderBase
│   ├── email.py         # SMTPEmailProvider, SendGridProvider
│   └── sms.py           # TwilioSMSProvider
├── template/
│   ├── engine.py        # Template engines and registry
│   └── service.py       # NotificationTemplateService
├── aggregate.py         # Domain actions
├── command.py           # Commands
├── query.py             # Query resources
├── service.py           # NotificationService (routing)
├── processor.py         # Content processing
├── model.py             # Database models
├── types.py             # Enums
└── domain.py            # Domain definition

src/rfx_schema/rfx_notify/
├── notification.py      # Schema models for Alembic
├── types.py             # Schema-layer enums
└── _pgentity.py         # PostgreSQL views
```

## Dependencies

- **Fluvius**: Domain framework (aggregate, commands, queries)
- **SQLAlchemy**: ORM for PostgreSQL
- **Jinja2**: Template engine
- **aiosmtplib**: Async SMTP client
- **httpx**: HTTP client for API providers (SendGrid, Twilio)

## When Helping Users

1. **Setup**: Guide through migration → provider setup → first notification
2. **Templates**: Explain template resolution, versioning, and engines
3. **Providers**: Help configure credentials, explain priority/fallback
4. **Debugging**: Check status, review logs, validate config
5. **Integration**: Show appropriate pattern for their use case
6. **Best Practices**: Multi-provider setup, templates, preferences

## Quick Reference

**Send Email**: `channel=EMAIL, recipients=[email], subject, body`
**Send SMS**: `channel=SMS, recipients=[+phone], body`
**With Template**: `template_key=key, template_data={vars}`
**Scheduled**: `scheduled_at=ISO8601`
**Custom Headers**: `meta={from_email, cc, bcc}`

---

**Documentation Files**:
- `NOTIFY_SERVICE_GUIDE.md` - Comprehensive guide
- `NOTIFY_QUICK_START.md` - Quick start guide
- `NOTIFY_CLAUDE_CONTEXT.md` - This file
