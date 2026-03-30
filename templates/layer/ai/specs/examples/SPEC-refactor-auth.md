---
id: SPEC-EXAMPLE-002
title: Refactor authentication to middleware pattern
status: done
priority: critical
author: 0dai-team
created: 2026-03-29
updated: 2026-03-29
tags: [auth, refactor, security, middleware]
agent: architect
---

## Context

Authentication logic is duplicated across 12 route handlers. Each handler validates tokens independently, leading to inconsistent error responses and making it easy to forget auth on new endpoints. A recent security audit flagged two unprotected endpoints.

## Goal

Centralize authentication into a single middleware that runs before route handlers.

## Requirements

1. Single auth middleware validates JWT tokens for all protected routes
2. Unprotected routes are explicitly listed in a whitelist configuration
3. Middleware sets `request.user` with decoded token claims
4. Invalid tokens return 401 with consistent error format
5. Expired tokens return 401 with `token_expired` error code
6. All 12 route handlers remove inline auth logic
7. Whitelist is configurable (not hardcoded)

## Acceptance Criteria

- [ ] All existing auth tests pass without modification
- [ ] New middleware test covers: valid token, expired token, missing token, malformed token
- [ ] No route handler contains direct token validation
- [ ] Whitelist includes: /health, /api/v1/health, /api/v1/docs
- [ ] Security review confirms no unprotected endpoints

## Out of Scope

- OAuth2/OIDC provider integration (separate spec)
- Role-based access control (separate spec)
- Token refresh mechanism

## Technical Notes

- Use `ai/personas/security.yaml` review checklist for validation
- Reference `ai/experience/accepted/anti-patterns/` for known auth mistakes
- The middleware pattern should follow the framework's convention (e.g., Express middleware, FastAPI dependency)
