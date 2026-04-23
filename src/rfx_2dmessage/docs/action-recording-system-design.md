# Action Recording System — Design Summary

## Overview

This document summarises the design of an **Action Recording System** where users select an action from a list, optionally fill in a form, and submit data to a configured endpoint. The system is driven by declarative **action payloads** — JSON objects that describe what to collect, where to send it, and what to expect back.

---

## Action Payload Structure

Each action payload is a self-contained definition with four top-level concerns:

| Block | Purpose |
|---|---|
| `id`, `name`, `type`, `description` | Identity and behaviour |
| `endpoint` | Where to send the data |
| `schema` | What data to collect (form actions only) |
| `response` | Expected response shape and UI messaging |

---

## Action Types

The `type` field is a discriminator that drives UI behaviour:

### `form`
User must fill in a data entry form before submitting. The `schema` block is **required**.

### `atomic`
No data collection needed — user simply selects and confirms the action. The `schema` block is **forbidden**. The endpoint fires immediately on confirmation.

---

## Endpoint Block

Every action has an endpoint definition:

```json
"endpoint": {
  "url": "https://api.example.com/events/login",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer {{API_KEY}}"
  }
}
```

- Supports `GET`, `POST`, `PUT`, `PATCH`
- Headers support `{{TEMPLATE_VARIABLES}}` for runtime secret injection

---

## Schema Block (form actions only)

Describes the fields to collect. Used by the UI to dynamically render a form.

```json
"schema": {
  "fields": [
    { "key": "user_id",   "type": "string",   "required": true,  "label": "User ID" },
    { "key": "timestamp", "type": "datetime", "required": true,  "label": "Login Time" },
    { "key": "device",    "type": "string",   "required": false, "label": "Device Type" }
  ]
}
```

**Supported field types:** `string`, `number`, `boolean`, `datetime`, `array`, `object`

Each field supports an optional `options` array for enum/dropdown behaviour, and a `default` value.

---

## Response Block

Declared on every action payload — acts as a **client-side contract** so the UI knows what to expect before the server responds.

```json
"response": {
  "successMessage": "Login recorded successfully",
  "errorMessage": "Failed to record login",
  "fields": [
    { "key": "record_id",   "type": "string",   "label": "Record ID" },
    { "key": "recorded_at", "type": "datetime", "label": "Recorded At" }
  ]
}
```

- `successMessage` / `errorMessage` — displayed in toast/modal after submission
- `fields` — declares which keys the UI should pull from `response.data` for display or chaining into a downstream action

---

## Standard Response Envelope

All endpoints return the same wrapper structure regardless of action type or outcome.

### Success

```json
{
  "status": "success",
  "action_id": "action_001",
  "record_id": "rec_abc123",
  "timestamp": "2026-04-03T09:15:00Z",
  "data": {
    "record_id": "rec_abc123",
    "recorded_at": "2026-04-03T09:15:00Z"
  },
  "error": null
}
```

### Error

```json
{
  "status": "error",
  "action_id": "action_001",
  "record_id": null,
  "timestamp": "2026-04-03T09:15:00Z",
  "data": null,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "user_id is required",
    "fields": ["user_id"]
  }
}
```

**Envelope rules enforced by schema:**
- `status` is always `"success"` or `"error"`
- When `success`: `data` is required, `error` must be `null`
- When `error`: `error` is required, `data` must be `null`

---

## Schema Validation Rules

Two JSON Schemas govern the system:

### 1. Action Payload Schema
- `id`, `name`, `type`, `endpoint`, `response` are always required
- `schema` is **conditionally required**: required when `type = "form"`, forbidden when `type = "atomic"` — enforced via `if/then/else`

### 2. Response Envelope Schema
- `status`, `action_id`, `timestamp` always required
- `data` / `error` are mutually exclusive based on `status` — enforced via `if/then/else`

---

## Full Architecture at a Glance

```
Action Payload (design-time)
├── type              → "form" | "atomic"  — drives UI
├── endpoint          → URL, method, headers
├── schema            → fields[] to collect (form only)
└── response
    ├── successMessage
    ├── errorMessage
    └── fields[]      → keys expected in envelope.data

Response Envelope (runtime, from server)
├── status            → "success" | "error"
├── action_id         → echoes back the triggering action
├── record_id         → created record (null on error)
├── timestamp         → server processing time
├── data{}            → response fields (null on error)
└── error{}           → code, message, fields[] (null on success)
```

---

## Example Actions

### Form Action — User Login

```json
{
  "id": "action_001",
  "name": "User Login",
  "type": "form",
  "endpoint": { "url": "https://api.example.com/events/login", "method": "POST" },
  "schema": {
    "fields": [
      { "key": "user_id",   "type": "string",   "required": true,  "label": "User ID" },
      { "key": "timestamp", "type": "datetime", "required": true,  "label": "Login Time" }
    ]
  },
  "response": {
    "successMessage": "Login recorded successfully",
    "errorMessage": "Failed to record login",
    "fields": [{ "key": "record_id", "type": "string", "label": "Record ID" }]
  }
}
```

### Atomic Action — End of Shift

```json
{
  "id": "action_003",
  "name": "End of Shift",
  "type": "atomic",
  "endpoint": { "url": "https://api.example.com/events/shift-end", "method": "POST" },
  "response": {
    "successMessage": "Shift ended successfully",
    "errorMessage": "Failed to record shift end",
    "fields": [
      { "key": "record_id",        "type": "string", "label": "Record ID" },
      { "key": "duration_minutes", "type": "number", "label": "Shift Duration (mins)" }
    ]
  }
}
```
