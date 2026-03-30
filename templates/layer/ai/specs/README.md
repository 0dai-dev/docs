# managed: true

# Spec-Driven Development

This directory holds structured specifications that agents read before starting work.

## Why Specs?

- Replace verbal descriptions with structured, reviewable documents
- Ensure agents understand context, constraints, and acceptance criteria
- Enable traceability between intent and implementation
- Support async workflows — write the spec, then hand it to any agent

## Spec Format

Each spec is a Markdown file with YAML frontmatter:

```yaml
---
id: SPEC-001
title: Add user authentication
status: draft|ready|in-progress|done|cancelled
priority: critical|high|medium|low
author: team-member
created: 2026-03-29
updated: 2026-03-29
tags: [auth, security, api]
agent: planner
---
```

## Sections

A spec should include these sections:

1. **Context** — Why this work is needed
2. **Goal** — One sentence: what success looks like
3. **Requirements** — Numbered list of what must be true
4. **Acceptance Criteria** — How to verify the work is done
5. **Out of Scope** — What is explicitly NOT included
6. **Technical Notes** — Implementation hints, constraints, references

## Workflow

1. Create a spec: `0dai spec --new <name> --target <path>`
2. Fill in the sections
3. Mark as `ready`
4. Agent reads the spec before starting work
5. Mark as `in-progress`, then `done`

## Status Flow

```
draft → ready → in-progress → done
                             → cancelled
```
