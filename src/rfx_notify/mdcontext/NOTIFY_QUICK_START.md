# RFX Notify - Quick Start Guide

## TL;DR

Multi-channel notification service supporting Email (SMTP/SendGrid), SMS (Twilio), Push, and Webhooks with template support and delivery tracking.

## Quick Setup (5 Minutes)

### 1. Run Migration
```bash
alembic revision --autogenerate -m "Add rfx_notify"
alembic upgrade head
```

### 2. Setup Email Provider
```python
# Command: create-provider
{
    "name": "SMTP",
    "provider_type": "SMTP",
    "channel": "EMAIL",
    "config": {"host": "smtp.gmail.com", "port": 587, "use_tls": true},
    "credentials": {"username": "your@email.com", "password": "password"},
    "priority": 100,
    "status": "ACTIVE"
}
```

### 3. Send Your First Email
```python
# Command: send-notification
{
    "channel": "EMAIL",
    "recipients": ["user@example.com"],
    "subject": "Hello",
    "body": "Welcome!",
    "content_type": "TEXT"
}
```

## Common Use Cases

### Send Email with Template
```python
# 1. Create template
{
    "key": "welcome",
    "channel": "EMAIL",
    "body_template": "Hi {{name}}!",
    "subject_template": "Welcome {{name}}",
    "engine": "jinja2"
}

# 2. Send notification
{
    "channel": "EMAIL",
    "recipients": ["user@example.com"],
    "template_key": "welcome",
    "template_data": {"name": "John"}
}
```

### Send SMS
```python
# 1. Setup Twilio provider
{
    "name": "Twilio",
    "provider_type": "TWILIO",
    "channel": "SMS",
    "config": {"from_number": "+1234567890"},
    "credentials": {"account_sid": "ACxxx", "auth_token": "xxx"},
    "status": "ACTIVE"
}

# 2. Send SMS
{
    "channel": "SMS",
    "recipients": ["+1234567890"],
    "body": "Your code: 123456"
}
```

### Schedule Notification
```python
{
    "channel": "EMAIL",
    "recipients": ["user@example.com"],
    "subject": "Reminder",
    "body": "Your appointment is tomorrow",
    "scheduled_at": "2025-11-15T10:00:00Z"
}
```

### HTML Email with CC/BCC
```python
{
    "channel": "EMAIL",
    "recipients": ["user@example.com"],
    "subject": "Important",
    "body": "<h1>Hello!</h1>",
    "content_type": "HTML",
    "meta": {
        "cc": "manager@company.com",
        "bcc": "archive@company.com"
    }
}
```

## Available Providers

| Provider | Type | Channels |
|----------|------|----------|
| SMTP | Built-in | EMAIL |
| SendGrid | API | EMAIL |
| Twilio | API | SMS |
| Custom | Extensible | Any |

## Supported Channels

- **EMAIL** - Email notifications
- **SMS** - Text messages
- **PUSH** - Push notifications (extensible)
- **WEBHOOK** - HTTP callbacks
- **INAPP** - In-app via MQTT

## Template Engines

- **jinja2** (default) - Full Jinja2 support
- **text** - Simple `${variable}` substitution
- **static** - No variables

## Status Flow

```
PENDING → PROCESSING → SENT → DELIVERED
                    ↓
                  FAILED (auto-retry with backoff)
```

## Query Your Notifications

```python
# GET /api/rfx-notify/notifications
# Returns all notifications for current user

# Filter by status
GET /api/rfx-notify/notifications?status=DELIVERED

# Filter by channel
GET /api/rfx-notify/notifications?channel=EMAIL
```

## User Preferences

```python
# Command: update-notification-preference
{
    "channel": "EMAIL",
    "enabled": true,
    "email_address": "user@example.com",
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00"
}
```

## Retry Failed Notification

```python
# Command: retry-notification
# Target: notification/{id}
# Automatically retries with exponential backoff
```

## Key Features

✅ **Multi-Provider** - Automatic failover between providers
✅ **Templates** - Jinja2 templates with versioning & locales
✅ **Retry Logic** - Exponential backoff for failed deliveries
✅ **Delivery Tracking** - Comprehensive logs per attempt
✅ **User Preferences** - Per-channel opt-in/out with quiet hours
✅ **Rate Limiting** - Provider-level and user-level limits
✅ **Multi-Tenant** - Tenant and app scoping support

## Database Tables

- `notification` - Core notification records
- `notification_provider` - Provider configs
- `notification_template` - Templates
- `notification_delivery_log` - Delivery attempts
- `notification_preference` - User preferences

## Code Examples

### Python Integration
```python
from rfx_notify.command import SendNotification

async def send_welcome_email(user):
    cmd = SendNotification()
    result = await cmd.execute({
        "channel": "EMAIL",
        "recipients": [user.email],
        "template_key": "welcome",
        "template_data": {"name": user.name}
    })
```

### Check Notification Status
```python
notification = await stm.fetch("notification", notification_id)
print(f"Status: {notification.status}")
print(f"Sent at: {notification.sent_at}")
print(f"Error: {notification.error_message}")
```

## Troubleshooting

**Notification stuck in PENDING?**
- Check provider status: `SELECT * FROM rfx_notify.notification_provider WHERE status='ACTIVE'`

**Provider failing?**
- Check delivery logs: `SELECT * FROM rfx_notify.notification_delivery_log WHERE notification_id='xxx'`

**Template not rendering?**
- Verify template is active: `is_active = true`
- Check template data has required variables

## Next Steps

1. ✅ Read full guide: `NOTIFY_SERVICE_GUIDE.md`
2. ✅ Set up providers for your channels
3. ✅ Create templates for common notifications
4. ✅ Configure user preferences
5. ✅ Monitor delivery logs

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ send-notification
       ▼
┌─────────────────┐
│   Aggregate     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐     ┌──────────────┐
│    Service      │────▶│  Providers   │
│  (Routing)      │     │ SMTP/Twilio  │
└──────┬──────────┘     └──────────────┘
       │
       ▼
┌─────────────────┐
│   Database      │
│  (PostgreSQL)   │
└─────────────────┘
```

---

**For detailed documentation, see `NOTIFY_SERVICE_GUIDE.md`**
