---
id: SPEC-EXAMPLE-001
title: Add /api/v1/health endpoint
status: done
priority: high
author: 0dai-team
created: 2026-03-29
updated: 2026-03-29
tags: [api, health-check, monitoring]
agent: planner
---

## Context

Production monitoring requires a standardized health endpoint that returns service status, version, and dependency health. Currently, there is no way for load balancers to verify the service is ready.

## Goal

A `/api/v1/health` endpoint that returns structured JSON with service readiness status.

## Requirements

1. GET `/api/v1/health` returns 200 when service is healthy
2. Response includes: `status`, `version`, `uptime`, `dependencies`
3. Each dependency (database, cache, queue) reports its own status
4. Returns 503 if any critical dependency is unhealthy
5. Response time under 100ms (no heavy computation in health check)

## Acceptance Criteria

- [ ] Endpoint responds with 200 and correct JSON schema
- [ ] Endpoint returns 503 when database is unreachable
- [ ] Response includes accurate version from package manifest
- [ ] Integration test covers healthy and degraded states
- [ ] Endpoint is excluded from authentication middleware

## Out of Scope

- Detailed metrics (use /metrics for Prometheus)
- Historical health data storage
- Custom health check plugins

## Technical Notes

- Use the existing middleware chain — insert before auth
- Version should come from `ai/manifest/project.yaml` or package.json
- Follow the existing error response format from `app/api/errors.py`
