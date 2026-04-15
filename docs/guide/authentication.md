# Authentication & Authorization

0dai uses a token-based authentication system to track projects, usage limits, and team features. This document describes the auth flow, API endpoints, and how to integrate with 0dai programmatically.

## Overview

0dai authentication is separate from individual agent CLI subscriptions (Claude Code, Codex, etc.). It tracks:

- **Projects** — which repos are bound to your account
- **Usage limits** — daily quotas for init, sync, detect, and report operations
- **Plans** — free, essential, pro, team tiers with different limits
- **Licenses** — device-bound activations with plan and expiry

All API requests to `https://api.0dai.dev` use Bearer token authentication via the `Authorization` header.

## Auth Flows

0dai supports two authentication flows:

### 1. Device Code Flow (CLI → Browser)

The primary flow for terminal-based authentication. The CLI initiates a device code, the user verifies it in a browser, and the CLI polls for the resulting token.

```
┌─────────┐                    ┌─────────┐                    ┌──────────┐
│  CLI    │                    │  API    │                    │ Browser  │
└────┬────┘                    └────┬────┘                    └────┬─────┘
     │                              │                              │
     │ POST /v1/auth/device         │                              │
     │─────────────────────────────>│                              │
     │                              │                              │
     │ {device_code, user_code}     │                              │
     │<─────────────────────────────│                              │
     │                              │                              │
     │  (prints user_code + URL)    │                              │
     │                              │                              │
     │                              │  POST /v1/auth/verify        │
     │                              │  (with Bearer token + code)  │
     │                              │<─────────────────────────────│
     │                              │                              │
     │                              │  {verified: true}            │
     │                              │─────────────────────────────>│
     │                              │                              │
     │ POST /v1/auth/token          │                              │
     │─────────────────────────────>│                              │
     │                              │                              │
     │ {access_token, email, plan}  │                              │
     │<─────────────────────────────│                              │
     │                              │                              │
```

#### Step 1: Initiate Device Flow

```bash
curl -X POST https://api.0dai.dev/v1/auth/device \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "device_code": "dc_abc123...",
  "user_code": "ABCD-1234",
  "verification_uri": "https://0dai.dev/auth/device",
  "expires_in": 600,
  "interval": 5
}
```

| Field | Type | Description |
|---|---|---|
| `device_code` | string | Opaque identifier for polling (not shown to user) |
| `user_code` | string | 8-character code the user enters in the browser |
| `verification_uri` | string | URL where the user verifies the code |
| `expires_in` | int | Seconds until the code expires (600 = 10 min) |
| `interval` | int | Recommended polling interval in seconds |

#### Step 2: User Verifies in Browser

The user opens `https://0dai.dev/auth/device`, signs in via GitHub or Google (which creates a browser session with a Bearer token stored in `localStorage`), then enters the `user_code`.

The browser sends:

```bash
curl -X POST https://api.0dai.dev/v1/auth/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <browser_token>" \
  -d '{"user_code": "ABCD-1234"}'
```

**Response:**

```json
{
  "verified": true,
  "email": "user@example.com"
}
```

The verify endpoint:
1. Validates the browser's Bearer token (checks existence and expiry)
2. Looks up the pending device by `user_code`
3. Checks device code hasn't expired
4. Generates a new access token bound to the verified user
5. Marks the device as `verified` with the new token

#### Step 3: CLI Polls for Token

```bash
curl -X POST https://api.0dai.dev/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"device_code": "dc_abc123..."}'
```

**Response (pending):**

```json
{
  "error": "authorization_pending"
}
```

**Response (success):**

```json
{
  "access_token": "0dai_at_abc123...",
  "email": "user@example.com",
  "plan": "free",
  "expires_at": "2027-04-14T07:04:22+00:00"
}
```

The token endpoint:
1. Finds the device by `device_code`
2. Enforces IP binding (only the CLI that initiated the flow can retrieve the token)
3. Checks device code expiry
4. Returns the access token if the device is verified

### 2. OAuth Flow (Browser Only)

For web dashboard access, users sign in via GitHub or Google OAuth:

- **GitHub:** `GET https://api.0dai.dev/v1/auth/github` — redirects to GitHub OAuth
- **Google:** `GET https://api.0dai.dev/v1/auth/google` — redirects to Google OAuth

After OAuth callback, the browser receives a one-time exchange code that can be exchanged for a token:

```bash
curl -X POST https://api.0dai.dev/v1/auth/exchange \
  -H "Content-Type: application/json" \
  -d '{"code": "<one_time_code>"}'
```

**Response:**

```json
{
  "access_token": "0dai_at_abc123...",
  "email": "user@example.com",
  "name": "User Name"
}
```

## Token Format

Access tokens follow the pattern `0dai_at_<48_hex_chars>`. They are stored server-side as SHA-256 hashes and include:

| Field | Type | Description |
|---|---|---|
| `email` | string | User email (primary key) |
| `plan` | string | Plan tier: `free`, `essential`, `pro`, `team` |
| `name` | string | Display name |
| `avatar` | string | Avatar URL |
| `created_at` | string | ISO timestamp of token creation |
| `expires_at` | string | ISO timestamp of token expiry (365 days) |

## API Endpoints

### Auth Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/auth/device` | None | Initiate device code flow |
| `POST` | `/v1/auth/verify` | Browser Bearer | Verify device code from browser |
| `POST` | `/v1/auth/token` | None | Poll for device flow token |
| `POST` | `/v1/auth/exchange` | None | Exchange OAuth code for token |
| `GET` | `/v1/auth/status` | Bearer | Get current user status and usage |
| `GET` | `/v1/auth/github` | None | Start GitHub OAuth flow |
| `GET` | `/v1/auth/google` | None | Start Google OAuth flow |

### Project Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/init` | Bearer + License | Initialize ai/ layer for a project |
| `POST` | `/v1/detect` | None | Detect project stack |
| `POST` | `/v1/sync` | Bearer + License | Sync ai/ layer updates |
| `POST` | `/v1/projects/bind` | Bearer + License | Bind a project to the account |
| `POST` | `/v1/projects/heartbeat` | Bearer + License | Send project health heartbeat |

### License Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/licenses/activate` | Bearer | Activate a license on this device |

### Graph Endpoints (Pro+)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/graph/sync` | Bearer | Upload local graph to server |
| `GET` | `/v1/graph/pull` | Bearer | Download server graph |

### Admin Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/v1/admin/metrics` | Admin | Get platform metrics |
| `GET` | `/v1/admin/reports` | Admin | List ingested reports |
| `POST` | `/v1/admin/plan` | Admin | Set user plan tier |
| `POST` | `/v1/admin/code` | Admin | Generate plan upgrade code |

### Other Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/feedback` | Optional | Submit user feedback |
| `POST` | `/v1/reports/ingest` | Bearer | Ingest project report |
| `POST` | `/v1/experience/ingest` | Pro+ | Ingest experience events |
| `POST` | `/v1/sessions/save` | Pro+ | Save session for roaming |
| `POST` | `/v1/run` | None | Decompose goal into tasks |
| `POST` | `/v1/redeem` | Bearer | Redeem a plan upgrade code |

## Request Headers

All authenticated requests should include:

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <access_token>` |
| `X-Device-ID` | Recommended | Unique device fingerprint |
| `X-CLI-Version` | Recommended | CLI version string (e.g. `4.0.0`) |
| `X-Client-Channel` | Optional | Distribution channel (`npm`, `binary`, etc.) |

## Rate Limits

Rate limits vary by plan. Default limits per day:

| Action | Free | Essential | Pro | Team |
|---|---|---|---|---|
| `init` | 6 | 50 | 500 | 10000 |
| `sync` | 20 | 100 | 1000 | 9999 |
| `detect` | 20 | 100 | 1000 | 9999 |
| `report` | 3 | 10 | 100 | 9999 |

### Auth Endpoint Rate Limits

| Endpoint | Limit | Window |
|---|---|---|
| `/v1/auth/device` | 20 | Per IP per day |
| `/v1/auth/verify` | 10 | Per IP per day |
| `/v1/auth/token` | 60 | Per IP per day |
| `/v1/auth/exchange` | 20 | Per IP per day |

## Plans

| Plan | Projects | Swarm | Graph | Description |
|---|---|---|---|---|
| `free` | 3 | 0/day | Nodes only | Basic usage |
| `essential` | 10 | 5/day | Full | Extended limits |
| `pro` | 50 | 20/day | Full | Power users |
| `team` | 9999 | Unlimited | Full | Teams and orgs |

## CLI Auth Storage

The CLI stores auth state in `~/.0dai/auth.json`:

```json
{
  "token_id": "tok_abc123",
  "email": "user@example.com",
  "name": "User Name",
  "plan": "free",
  "access_token": "0dai_at_abc123...",
  "authenticated_at": "2026-04-13",
  "expires_at": "2027-04-13T23:59:59+00:00",
  "license": {
    "activation_id": "act_abc123",
    "status": "active",
    "plan": "free"
  }
}
```

## Error Responses

| Status | Error | Description |
|---|---|---|
| 400 | `code required` | Missing required field |
| 401 | `not authenticated` | No valid Bearer token |
| 401 | `invalid session` | Token not found or expired |
| 401 | `session expired` | Token past its expiry |
| 403 | `free trial used` | Anonymous init already used |
| 403 | `device_code bound to different IP` | IP mismatch on token poll |
| 404 | `invalid code` | User code not found |
| 410 | `code expired` | Device code past 10-min expiry |
| 428 | `authorization_pending` | User hasn't verified yet |
| 429 | `too many ...` | Rate limit exceeded |

## Security Considerations

1. **Token hashing** — Access tokens are stored as SHA-256 hashes, never in plaintext
2. **IP binding** — Device flow tokens can only be retrieved by the CLI that initiated the flow
3. **One-time use** — Device codes are deleted after successful token retrieval
4. **Expiry** — Tokens expire after 365 days; device codes expire after 10 minutes
5. **Rate limiting** — All endpoints have per-IP and per-user rate limits
