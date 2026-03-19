# RFX Notify Service - Integration Guide

## Overview

The **rfx_notify** service is a multi-channel notification system that supports Email, SMS, Push, Webhook, and In-app notifications. It provides:

- **Multi-Provider Support**: SMTP, SendGrid, Twilio, and extensible to other providers
- **Template Management**: Jinja2-based templates with multi-tenant and locale support
- **Delivery Tracking**: Comprehensive logging and retry mechanisms
- **User Preferences**: Channel-specific preferences with quiet hours
- **Domain-Driven Design**: Built on the Fluvius framework with CQRS pattern

## Architecture

```
rfx_notify/
├── providers/          # Notification providers (Email, SMS, etc.)
├── template/           # Template engines and service
├── aggregate.py        # Business logic and domain actions
├── command.py          # Domain commands (SendNotification, etc.)
├── query.py            # Query resources for data retrieval
├── service.py          # Notification routing and provider management
├── model.py            # Database models
└── types.py            # Enums and type definitions
```

## Database Schema

The service uses PostgreSQL with the `rfx_notify` schema containing:

- **notification** - Core notification records
- **notification_provider** - Provider configurations
- **notification_delivery_log** - Delivery attempt logs
- **notification_template** - Multi-channel templates
- **notification_preference** - User channel preferences

## Setup

### 1. Database Migration

```bash
# Generate migration
alembic revision --autogenerate -m "Add rfx_notify schema"

# Apply migration
alembic upgrade head
```

### 2. Configure Schema

Ensure `rfx_base/_meta/defaults.py` includes:
```python
RFX_NOTIFY_SCHEMA = "rfx_notify"
```

### 3. Import Domain

```python
from rfx_notify import RFXNotifyServiceDomain, command
from rfx_notify.query import RFXNotifyServiceQueryManager
```

## Provider Setup

### Email Provider (SMTP)

```python
# Command: create-provider
{
    "name": "Company SMTP",
    "provider_type": "SMTP",
    "channel": "EMAIL",
    "config": {
        "host": "smtp.company.com",
        "port": 587,
        "use_tls": true,
        "from_email": "noreply@company.com"
    },
    "credentials": {
        "username": "smtp_user",
        "password": "smtp_password"
    },
    "priority": 100,
    "is_default": true,
    "status": "ACTIVE",
    "retry_strategy": "EXPONENTIAL",
    "max_retries": 3
}
```

### Email Provider (SendGrid)

```python
{
    "name": "SendGrid",
    "provider_type": "SENDGRID",
    "channel": "EMAIL",
    "config": {
        "from_email": "noreply@company.com"
    },
    "credentials": {
        "api_key": "SG.xxxxxxxxxxxxx"
    },
    "priority": 90,  # Higher priority than SMTP
    "is_default": false,
    "status": "ACTIVE"
}
```

### SMS Provider (Twilio)

```python
{
    "name": "Twilio SMS",
    "provider_type": "TWILIO",
    "channel": "SMS",
    "config": {
        "from_number": "+1234567890"
    },
    "credentials": {
        "account_sid": "ACxxxxxxxxxxxxxxx",
        "auth_token": "your_auth_token"
    },
    "priority": 100,
    "is_default": true,
    "status": "ACTIVE",
    "rate_limit_per_minute": 60
}
```

## Usage Examples

### 1. Send Simple Email

```python
# Command: send-notification
{
    "channel": "EMAIL",
    "recipient_id": "user-uuid",
    "recipients": ["user@example.com"],
    "subject": "Welcome to MyApp",
    "body": "<h1>Hello!</h1><p>Welcome to our platform.</p>",
    "content_type": "HTML",
    "priority": "NORMAL"
}
```

### 2. Send Email with Custom Headers

```python
{
    "channel": "EMAIL",
    "recipients": ["user@example.com"],
    "subject": "Important Notice",
    "body": "This is a test message",
    "content_type": "TEXT",
    "priority": "HIGH",
    "meta": {
        "from_email": "support@company.com",
        "cc": "admin@company.com",
        "bcc": "archive@company.com"
    }
}
```

### 3. Send SMS

```python
{
    "channel": "SMS",
    "recipient_id": "user-uuid",
    "recipients": ["+1234567890"],
    "body": "Your verification code is: 123456",
    "content_type": "TEXT",
    "priority": "URGENT",
    "meta": {
        "from_number": "+1987654321"
    }
}
```

### 4. Send with Template

```python
# First, create a template
{
    "key": "welcome_email",
    "channel": "EMAIL",
    "name": "Welcome Email Template",
    "body_template": "<h1>Welcome {{user_name}}!</h1><p>Thanks for joining {{app_name}}.</p>",
    "subject_template": "Welcome to {{app_name}}",
    "engine": "jinja2",
    "locale": "en",
    "content_type": "HTML",
    "variables_schema": {
        "required": ["user_name", "app_name"]
    }
}

# Then send notification with template
{
    "channel": "EMAIL",
    "recipients": ["user@example.com"],
    "template_key": "welcome_email",
    "template_data": {
        "user_name": "John Doe",
        "app_name": "MyApp"
    },
    "priority": "NORMAL"
}
```

### 5. Scheduled Notifications

```python
{
    "channel": "EMAIL",
    "recipients": ["user@example.com"],
    "subject": "Reminder",
    "body": "This is your scheduled reminder",
    "scheduled_at": "2025-11-15T10:00:00Z",
    "priority": "NORMAL"
}
```

## Template Management

### Template Resolution (Fallback Chain)

Templates are resolved with the following priority:
1. `(tenant_id, app_id, channel, locale)` - Most specific
2. `(tenant_id, app_id, channel, None)`
3. `(tenant_id, None, channel, None)`
4. `(None, None, channel, locale)`
5. `(None, None, channel, None)` - Base template

### Template Engines

**Jinja2** (Default):
```jinja2
<h1>Hello {{user_name}}!</h1>
<p>Your balance is {{ balance|default(0) }}</p>
```

**Text** (Simple variable substitution):
```text
Hello ${user_name}!
Your balance is ${balance}
```

**Static** (No variables):
```text
This is a static message without any variables.
```

### Multi-Locale Templates

```python
# Create English version
{
    "key": "welcome_email",
    "channel": "EMAIL",
    "locale": "en",
    "body_template": "Welcome {{user_name}}!",
    "subject_template": "Welcome!"
}

# Create Spanish version
{
    "key": "welcome_email",
    "channel": "EMAIL",
    "locale": "es",
    "body_template": "¡Bienvenido {{user_name}}!",
    "subject_template": "¡Bienvenido!"
}
```

### Template Versioning

Templates are automatically versioned when updated:
```python
# Version 1 (initial)
{"key": "welcome_email", "body_template": "Welcome!"}

# Version 2 (update creates new version)
{"key": "welcome_email", "body_template": "Welcome to our platform!"}
```

## User Preferences

### Set Channel Preferences

```python
# Command: update-notification-preference
{
    "channel": "EMAIL",
    "enabled": true,
    "email_address": "user@example.com",
    "opt_in": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00",
    "quiet_hours_timezone": "America/New_York",
    "frequency_limit": {
        "max_per_hour": 5,
        "max_per_day": 20
    }
}
```

### Disable Channel

```python
{
    "channel": "SMS",
    "enabled": false
}
```

## Query API

### Get User Notifications

```python
# Query: notifications
# GET /api/rfx-notify/notifications

# Filters
{
    "status": "DELIVERED",
    "channel": "EMAIL",
    "priority": "HIGH",
    "_created__gte": "2025-11-01"
}
```

### Get Notification Details

```python
# GET /api/rfx-notify/notifications/{notification_id}
```

### List Providers

```python
# Query: notification-providers (Admin only)
# GET /api/rfx-notify/notification-providers

# Response includes all configured providers
```

### Get Delivery Logs

```python
# Query: notification-delivery-logs (Admin only)
# GET /api/rfx-notify/notification-delivery-logs?notification_id={id}
```

## Retry Failed Notifications

```python
# Command: retry-notification
# Target: notification/{notification_id}

# Automatically retries with exponential backoff
# Respects max_retries setting
```

## Provider Selection Logic

The service automatically selects the best provider based on:
1. **Channel match** - Provider must support the notification channel
2. **Status** - Provider must be ACTIVE
3. **Priority** - Lower priority number = higher priority (100 > 200)
4. **Rate limits** - Respects configured rate limits
5. **Fallback** - If primary fails, tries next available provider

## Error Handling

Notifications track errors with:
- **error_message** - Human-readable error description
- **error_code** - Provider-specific error code
- **retry_count** - Number of retry attempts
- **failed_at** - Timestamp of final failure

## Status Flow

```
PENDING → PROCESSING → SENT → DELIVERED
                    ↓
                  FAILED
                    ↓
                REJECTED / BOUNCED
```

## Integration Patterns

### 1. Direct Command Execution

```python
from rfx_notify.command import SendNotification

async def send_welcome_email(user):
    command = SendNotification()
    result = await command.execute({
        "channel": "EMAIL",
        "recipient_id": user.id,
        "recipients": [user.email],
        "template_key": "welcome_email",
        "template_data": {"user_name": user.name}
    })
    return result
```

### 2. Using Domain Service

```python
from rfx_notify.service import NotificationService
from rfx_notify.state import NotifyStateManager

async def send_with_service(notification_data):
    stm = NotifyStateManager()
    service = NotificationService(stm)

    # Create notification
    notification = await stm.insert("notification", notification_data)

    # Send through service
    result = await service.send_notification(notification)
    return result
```

### 3. Using Content Processor (with templates)

```python
from rfx_notify.processor import NotificationContentProcessor

async def send_templated_notification(template_key, recipient, data):
    processor = NotificationContentProcessor(stm)

    # Prepare notification with template
    notification_data = await processor.prepare_notification_with_template(
        channel=NotificationChannelEnum.EMAIL,
        template_key=template_key,
        template_data=data,
        recipients=[recipient.email],
        recipient_id=recipient.id
    )

    # Save and send
    notification = await stm.insert("notification", notification_data)
    result = await service.send_notification(notification)
    return result
```

## Extending the Service

### Add New Provider

1. **Create Provider Class**:
```python
# rfx_notify/providers/my_provider.py
from .base import NotificationProviderBase

class MyCustomProvider(NotificationProviderBase):
    async def send(self, recipient, subject, body, **kwargs):
        # Implementation
        pass

    async def check_status(self, provider_message_id):
        # Implementation
        pass

    async def validate_config(self):
        # Implementation
        pass
```

2. **Register in Service**:
```python
# rfx_notify/service.py
from .providers import MyCustomProvider

PROVIDER_CLASSES = {
    ProviderTypeEnum.SMTP: SMTPEmailProvider,
    ProviderTypeEnum.SENDGRID: SendGridProvider,
    ProviderTypeEnum.TWILIO: TwilioSMSProvider,
    ProviderTypeEnum.CUSTOM: MyCustomProvider,  # Add here
}
```

3. **Add Provider Type Enum**:
```python
# rfx_notify/types.py
class ProviderTypeEnum(Enum):
    CUSTOM = "CUSTOM"
    # ... existing types
```

### Add Custom Template Engine

```python
# rfx_notify/template/engine.py
class MyTemplateEngine(TemplateEngine):
    @property
    def name(self) -> str:
        return "my_engine"

    def render(self, template_body: str, data: Dict[str, Any]) -> str:
        # Custom rendering logic
        return rendered_content

# Register it
template_registry.register(MyTemplateEngine())
```

## Webhooks (Provider Callbacks)

For providers that support webhooks (SendGrid, Twilio):

```python
# Endpoint: POST /webhooks/notify/{provider_type}

# Command: update-notification-status
{
    "provider_message_id": "msg_xxxxx",
    "status": "DELIVERED",
    "delivered_at": "2025-11-11T10:00:00Z"
}
```

## Monitoring & Metrics

### Key Metrics to Track

1. **Delivery Rate**: `DELIVERED / SENT`
2. **Failure Rate**: `FAILED / TOTAL`
3. **Average Delivery Time**: `delivered_at - sent_at`
4. **Provider Performance**: Group by `provider_id`
5. **Retry Rate**: `retry_count > 0 / TOTAL`

### Query Delivery Stats

```sql
SELECT
    channel,
    status,
    COUNT(*) as count,
    AVG(retry_count) as avg_retries
FROM rfx_notify.notification
WHERE _created >= NOW() - INTERVAL '24 hours'
GROUP BY channel, status;
```

## Best Practices

1. **Template Management**
   - Use templates for all repeated notifications
   - Version templates properly
   - Test templates before activating

2. **Provider Configuration**
   - Set up multiple providers for redundancy
   - Configure rate limits to avoid throttling
   - Use priority for fallback ordering

3. **Error Handling**
   - Always check notification status
   - Implement retry logic for critical notifications
   - Monitor delivery logs for patterns

4. **User Preferences**
   - Respect quiet hours
   - Honor opt-out preferences
   - Provide unsubscribe mechanisms

5. **Security**
   - Encrypt provider credentials
   - Use environment variables for sensitive data
   - Implement rate limiting per user

## Troubleshooting

### Notification Not Sent

1. Check provider status: `SELECT * FROM rfx_notify.notification_provider WHERE status = 'ACTIVE'`
2. Check notification status: `SELECT status, error_message FROM rfx_notify.notification WHERE _id = 'xxx'`
3. Review delivery logs: `SELECT * FROM rfx_notify.notification_delivery_log WHERE notification_id = 'xxx'`

### Provider Errors

1. Validate provider config: Use `validate_provider` command
2. Check credentials are correct
3. Verify rate limits not exceeded
4. Check provider service status

### Template Not Rendering

1. Verify template is active: `is_active = true`
2. Check template resolution scope
3. Validate template data against schema
4. Test template syntax

## API Reference

### Commands

| Command | Description | Auth Required |
|---------|-------------|---------------|
| `send-notification` | Send a notification | Yes |
| `retry-notification` | Retry failed notification | Yes |
| `update-notification-status` | Update status (webhooks) | No |
| `create-provider` | Create provider | Admin |
| `update-provider` | Update provider | Admin |
| `change-provider-status` | Activate/deactivate provider | Admin |
| `update-notification-preference` | Update user preferences | Yes |
| `create-notification-template` | Create template | Admin |
| `activate-notification-template` | Activate template | Admin |
| `deactivate-notification-template` | Deactivate template | Admin |

### Query Resources

| Resource | Description | Auth Required |
|----------|-------------|---------------|
| `notifications` | User notifications | Yes |
| `notification-providers` | Provider list | Admin |
| `notification-delivery-logs` | Delivery logs | Admin |
| `notification-preferences` | User preferences | Yes |
| `notification-templates` | Template list | Admin |

## Support

For issues or questions:
1. Check delivery logs for error details
2. Verify provider configuration
3. Review template syntax and data
4. Check database schema is up to date

---

**Version**: 1.0
**Last Updated**: 2025-11-11
**Framework**: Fluvius Domain-Driven Design
**Database**: PostgreSQL
