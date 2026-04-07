# Action Recording System — Design Summary

## Overview

This document summarises the design of an **Action Recording System** where users select an action from a list, optionally fill in a form, and submit data to a configured endpoint. The system is driven by declarative **action payloads** — JSON objects that describe what to collect, how to execute the action, and what to expect back.

---

## Action Payload Structure

Each action payload is a self-contained definition with four top-level concerns:

| Block | Purpose |
|---|---|
| `id`, `name`, `type`, `description` | Identity and UI behaviour |
| `execution` | How the action is performed — API post or embedded remote view |
| `schema` | What data to collect (API form actions only) |
| `response` | Expected response shape and UI messaging |

---

## Action Types

The `type` field drives UI behaviour — what the user sees and does:

### `atomic`
No data collection needed. User selects and confirms the action in one tap. Execution fires immediately on confirmation.

### `form`
User fills in a data entry form before submitting. The `schema` block is required. Only valid with `execution.mode = "api"`.

### `embedded`
A remote server renders the entire UI inside a modal, fullscreen view, or sheet. The action system loads the URL, waits for a callback, then records the outcome. No `schema` block — the remote page owns its own form.

---

## Execution Block

Every action has an `execution` block that declares **who submits** the data. The `mode` field is a strict discriminator — `endpoint` and `embedded` are mutually exclusive. An optional `authorization` block specifies the auth method applied to outbound requests.

### `authorization` — Optional, applies to both modes

```json
"authorization": {
  "type": "bearer",
  "token": "eyJhbGciOiJIUzI1NiJ9..."
}
```

Supported authorization types:

| `type` | Required fields | Usage |
|---|---|---|
| `bearer` | `token` | Adds `Authorization: Bearer <token>` header |
| `apiKey` | `header`, `value` | Adds a named header with a static key value |
| `basic` | `username`, `password` | Adds `Authorization: Basic <base64>` header |
| `none` | — | Explicitly no authorization |

Authorization is declared at the `execution` level and applies uniformly — for `api` mode it is attached to the endpoint request, for `embed` mode it is passed to the embedded URL host via the callback handshake.

### `mode: "api"` — Action system posts directly

```json
"execution": {
  "mode": "api",
  "authorization": {
    "type": "bearer",
    "token": "eyJhbGciOiJIUzI1NiJ9..."
  },
  "endpoint": {
    "url": "https://api.example.com/events/login",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

- Supports `GET`, `POST`, `PUT`, `PATCH`
- Used with `type: "atomic"` or `type: "form"`

### `mode: "embed"` — Remote server owns submission

```json
"execution": {
  "mode": "embed",
  "embedded": {
    "url": "https://signing.example.com/flows/sign?doc=doc_123&signer=user_456",
    "callback": {
      "mode": "postMessage",
      "successEvent": "SIGNING_COMPLETE",
      "cancelEvent":  "SIGNING_CANCELLED",
      "errorEvent":   "SIGNING_FAILED"
    },
    "display": {
      "mode": "modal",
      "width": 800,
      "height": 600,
      "title": "Sign Document"
    }
  }
}
```

- The URL is **fully constructed by the sender** at registration time — all query params are baked in. The action system loads it as an opaque URL and does not inspect or modify it.
- Used with `type: "atomic"` or `type: "embedded"`

#### Callback Modes

The `callback.mode` determines how the remote server signals completion back to the action system:

| Mode | Mechanism |
|---|---|
| `postMessage` | Remote page fires `window.parent.postMessage` — for web/webview |
| `deepLink` | Remote page redirects to a registered app URL scheme — for native mobile |
| `webhook` | Remote server POSTs directly to a callback URL — for server-to-server |

**`postMessage`** requires: `successEvent`, `cancelEvent`, `errorEvent`

**`deepLink`** requires: `successUrl`, `cancelUrl`, `errorUrl`

**`webhook`** requires: `url`, `secret`

#### Display Modes

| `mode` | Behaviour |
|---|---|
| `modal` | Overlay on current screen, configurable width/height |
| `fullscreen` | Takes over the entire screen |
| `bottomSheet` | Slides up from bottom (mobile-native) |
| `tab` | Opens in a new browser tab |

---

## Execution Mode Constraint Matrix

| `type` | `execution.mode` | `schema` | `endpoint` | `embedded` |
|---|---|---|---|---|
| `atomic` | `api` | ❌ Forbidden | ✅ Required | ❌ Forbidden |
| `atomic` | `embed` | ❌ Forbidden | ❌ Forbidden | ✅ Required |
| `form` | `api` | ✅ Required | ✅ Required | ❌ Forbidden |
| `embedded` | `embed` | ❌ Forbidden | ❌ Forbidden | ✅ Required |

---

## Schema Block (`form` + `api` only)

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

**Supported field types:** `string`, `number`, `boolean`, `datetime`, `array`, `object`, `signature`, `pin`

Each field supports an optional `options` array for enum/dropdown behaviour and a `default` value.

---

## Response Block

Declared on every action payload — acts as a **client-side contract** so the UI knows what to expect before the server responds. Applies to both `api` and `embed` execution modes, since the action system normalises embed callbacks into the same envelope.

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

- `successMessage` / `errorMessage` — displayed in toast/modal after completion
- `fields` — declares which keys the UI should pull from `response.data` for display or chaining

---

## Standard Response Envelope

All actions produce the same response envelope regardless of execution mode. For `embed` mode, the action system normalises the callback payload into this structure before recording.

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

**Envelope rules:**
- `status` is always `"success"` or `"error"`
- When `success`: `data` is required, `error` must be `null`
- When `error`: `error` is required, `data` must be `null`

### Embed Callback Payload

The remote server delivers this structure via whichever callback mode is configured. The action system maps it to the standard envelope above:

```json
{
  "event":      "SIGNING_COMPLETE",
  "action_id":  "action_005",
  "session_id": "sess_xyz789",
  "timestamp":  "2026-04-03T09:15:00Z",
  "status":     "success",
  "data": {
    "signed_at":    "2026-04-03T09:15:00Z",
    "document_url": "https://signing.example.com/docs/signed-abc123.pdf"
  },
  "error": null
}
```

---

## Schema Validation Rules

Two JSON Schemas govern the system:

### 1. Action Payload Schema
- `id`, `name`, `type`, `execution`, `response` are always required
- `execution.mode` drives a strict `if/then/else`: `endpoint` required when `api`, `embedded` required when `embed`, never both
- `schema` is conditionally required: required when `type = "form"`, forbidden otherwise

### 2. Response Envelope Schema
- `status`, `action_id`, `timestamp` always required
- `data` / `error` are mutually exclusive based on `status` — enforced via `if/then/else`

---

## Full Architecture at a Glance

```
Action Payload (design-time)
├── type              → "atomic" | "form" | "embedded"  — drives UI
├── execution
│   ├── mode          → "api" | "embed"  — who submits
│   ├── authorization → bearer | apiKey | basic | none (optional)
│   ├── endpoint      → present only when mode = "api"
│   └── embedded      → present only when mode = "embed"
│       ├── url           → fully constructed by sender, opaque to action system
│       ├── callback      → postMessage | deepLink | webhook
│       └── display       → modal | fullscreen | bottomSheet | tab
├── schema            → fields[] — only when type = "form" and mode = "api"
└── response          → successMessage, errorMessage, fields[]
                        normalised from both api and embed paths

Response Envelope (runtime)
├── status            → "success" | "error"
├── action_id         → echoes back the triggering action
├── record_id         → created record (null on error)
├── timestamp         → processing time
├── data{}            → response fields (null on error)
└── error{}           → code, message, fields[] (null on success)
```

---

## Example Actions

### Form Action — User Login (API)

```json
{
  "id": "action_001",
  "name": "User Login",
  "type": "form",
  "execution": {
    "mode": "api",
    "authorization": {
      "type": "bearer",
      "token": "eyJhbGciOiJIUzI1NiJ9..."
    },
    "endpoint": { "url": "https://api.example.com/events/login", "method": "POST" }
  },
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

### Atomic Action — End of Shift (API, API key)

```json
{
  "id": "action_003",
  "name": "End of Shift",
  "type": "atomic",
  "execution": {
    "mode": "api",
    "authorization": {
      "type": "apiKey",
      "header": "X-API-Key",
      "value": "abc123xyz"
    },
    "endpoint": { "url": "https://api.example.com/events/shift-end", "method": "POST" }
  },
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

### Embedded Action — Sign Document (Embed, no auth)

```json
{
  "id": "action_005",
  "name": "Sign Document",
  "type": "embedded",
  "execution": {
    "mode": "embed",
    "authorization": {
      "type": "none"
    },
    "embedded": {
      "url": "https://signing.example.com/flows/sign?doc=doc_123&signer=user_456",
      "callback": {
        "mode": "postMessage",
        "successEvent": "SIGNING_COMPLETE",
        "cancelEvent":  "SIGNING_CANCELLED",
        "errorEvent":   "SIGNING_FAILED"
      },
      "display": {
        "mode": "modal",
        "width": 800,
        "height": 600,
        "title": "Sign Document"
      }
    }
  },
  "response": {
    "successMessage": "Document signed successfully",
    "errorMessage": "Document signing failed",
    "fields": [
      { "key": "record_id",    "type": "string",   "label": "Record ID" },
      { "key": "signed_at",    "type": "datetime", "label": "Signed At" },
      { "key": "document_url", "type": "string",   "label": "Signed Document URL" }
    ]
  }
}
```
