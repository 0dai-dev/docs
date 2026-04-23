# Project Authorization

0dai uses a project-centric authorization model. After authenticating as a user, every API operation is scoped to a **project** — a repository bound to your account. This document describes how projects are bound, how licenses activate per-project, and how the CLI manages project context.

## Overview

The authorization hierarchy:

```
User (email + plan)
  └── License (device-bound activation)
        └── Projects (bound repositories)
              └── Operations (init, sync, detect, report, graph)
```

- **User** — identified by email, has a plan tier (free, essential, pro, team)
- **License** — device-bound activation that enables authenticated operations
- **Project** — a repository bound to the user's account via `init` or `projects/bind`
- **Operation** — each API call is authorized against the user's plan limits and license status

## Project Binding

### Automatic Binding via `init`

When you run `0dai init` in a project directory, the CLI:

1. Collects project metadata (manifest files, directory structure, available CLIs)
2. Sends it to `POST /v1/init` with your Bearer token
3. The server binds the project to your account using:
   - Git remote URL (if available)
   - Project name from manifest (`package.json`, `pyproject.toml`, etc.)
   - Directory name as fallback

The server returns generated config files and records the project binding.

### Explicit Binding via API

For CI/CD or programmatic use, bind a project directly:

```bash
curl -X POST https://api.0dai.dev/v1/projects/bind \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "git_remote": "https://github.com/user/my-project.git",
    "stack": ["typescript", "nextjs"]
  }'
```

**Response:**

```json
{
  "project_id": "proj_abc123",
  "name": "my-project",
  "bound_at": "2026-04-14T10:00:00Z",
  "status": "active"
}
```

### Project Identification

The server identifies projects by (in priority order):

1. **Git remote URL** — normalized (strips `.git`, ignores protocol)
2. **Project name + owner** — from manifest files
3. **Directory hash** — SHA-256 of the project's file tree structure

This ensures the same project is recognized regardless of clone path or local directory name.

## License Activation

A license is a device-bound activation that authorizes operations for a specific plan tier.

### Activating a License

```bash
0dai activate free
```

Or via API:

```bash
curl -X POST https://api.0dai.dev/v1/licenses/activate \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: <device_fingerprint>" \
  -d '{
    "device_id": "<device_fingerprint>",
    "cli_version": "4.0.0",
    "channel": "npm"
  }'
```

**Response:**

```json
{
  "activation_id": "act_abc123",
  "status": "active",
  "plan": "free",
  "device_id": "dev_xyz789",
  "activated_at": "2026-04-14T10:00:00Z",
  "expires_at": "2027-04-14T10:00:00Z"
}
```

### License + Project Relationship

Each licensed operation (`init`, `sync`) requires both:

1. A valid Bearer token (user authentication)
2. An active license on the current device (device authorization)

The server validates both on every request. If the license is expired, revoked, or bound to a different device, the request returns `401`.

### Checking Activation Status

```bash
0dai activate status
```

Shows the current license status and plan tier.

## CLI Project Context

### Auth Storage

The CLI stores user credentials in `~/.0dai/auth.json`:

```json
{
  "email": "user@example.com",
  "name": "User Name",
  "plan": "free",
  "access_token": "0dai_at_abc123...",
  "authenticated_at": "2026-04-13T07:04:22.000Z",
  "expires_at": "2027-04-13T23:59:59+00:00",
  "license": {
    "activation_id": "act_abc123",
    "status": "active",
    "plan": "free"
  }
}
```

Local project registry is stored separately in `~/.0dai/projects.json`:

```json
{
  "projects": [
    {
      "path": "/home/user/my-project",
      "name": "my-project",
      "stack": "nextjs",
      "last_seen": "2026-04-14T10:00:00.000Z"
    }
  ]
}
```

The `projects.json` registry tracks which local directories have been initialised with 0dai. This allows the CLI to:

- Skip re-binding on subsequent `init` calls
- Show per-project sync status via `0dai portfolio`
- Support multiple projects on the same machine (up to 50 entries)

### Project Heartbeat

For active projects, the CLI can send health heartbeats:

```bash
curl -X POST https://api.0dai.dev/v1/projects/heartbeat \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_abc123",
    "event": "sync_complete",
    "agents_used": ["agent_cli_a", "agent_cli_b"]
  }'
```

Heartbeats are used for:

- Tracking project activity for the portfolio view
- Detecting stale/inactive projects
- Powering the usage analytics dashboard

## Authorization per Endpoint

Each endpoint enforces different authorization requirements:

| Endpoint | Auth Required | License Required | Plan Minimum |
|---|---|---|---|
| `/v1/detect` | No | No | — |
| `/v1/init` | Bearer | Yes | Free |
| `/v1/sync` | Bearer | Yes | Free |
| `/v1/projects/bind` | Bearer | Yes | Free |
| `/v1/projects/heartbeat` | Bearer | Yes | Free |
| `/v1/graph/sync` | Bearer | Yes | Pro |
| `/v1/graph/pull` | Bearer | Yes | Pro |
| `/v1/sessions/save` | Bearer | Yes | Pro |
| `/v1/reports/ingest` | Bearer | Yes | Free |
| `/v1/experience/ingest` | Bearer | Yes | Pro |
| `/v1/run` | Bearer | Yes | Pro |

## Multi-Project Workflow

A single user account can manage multiple projects:

```bash
# Project A
cd ~/project-a
0dai init          # Binds project-a to account

# Project B
cd ~/project-b
0dai init          # Binds project-b to account

# View all projects
0dai portfolio     # Lists all bound projects with status
```

Plan limits apply **per account**, not per project. For example, a Free plan allows 6 `init` operations total across all projects per day.

## CI/CD Integration

For headless environments (CI, containers), use a pre-generated token:

1. Authenticate on a developer machine: `0dai auth login`
2. Copy the `access_token` from `~/.0dai/auth.json`
3. Write a minimal auth file in CI:

```bash
mkdir -p ~/.0dai
echo '{"access_token": "0dai_at_abc123..."}' > ~/.0dai/auth.json
0dai init
```

To override the API endpoint (e.g. for self-hosted instances):

```bash
export ODAI_API_URL="https://api.0dai.dev"
```

## Revoking Access

### Logout (Local)

```bash
0dai auth logout
```

Removes credentials from `~/.0dai/auth.json`. The server-side token remains valid until expiry.

### License Deactivation

Contact support or use the dashboard to revoke a license activation. This immediately blocks all API operations from that device.

### Token Revocation

Tokens can be revoked via the dashboard. Revoked tokens return `401` on all subsequent requests.

## Error Responses

| Status | Error | Description |
|---|---|---|
| 401 | `not authenticated` | No valid Bearer token |
| 401 | `license not activated` | No active license on this device |
| 401 | `license expired` | License past its expiry date |
| 403 | `project not bound` | Project not bound to your account |
| 403 | `plan limit reached` | Daily quota exceeded for this action |
| 403 | `feature requires pro` | Current plan doesn't include this feature |
| 409 | `project already bound` | This project is already bound to your account |
