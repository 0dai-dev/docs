# Go Service Structure

Recommended greenfield layout:

```text
repo/
  ai/
  cmd/
    server/
  internal/
    handler/
    service/
    store/
  pkg/
  migrations/
  infra/
  tools/
  docs/
```

Rules:

- Put the main entrypoint in `cmd/server/`.
- Keep internal business logic under `internal/` using the standard Go project layout.
- Expose reusable packages in `pkg/`.
- Store database migrations in `migrations/`.
- Use `ai/` as the operational memory for agent workflows.
