# FastAPI Structure

Recommended greenfield layout:

```text
repo/
  ai/
  app/
    api/
      routes/
    core/
    models/
    schemas/
    services/
    main.py
  tests/
  migrations/
  infra/
  tools/
  docs/
```

Rules:

- Keep the FastAPI application under `app/` with a clear module structure.
- Put route handlers in `app/api/routes/`.
- Separate domain models (`models/`) from API schemas (`schemas/`).
- Store business logic in `app/services/`.
- Keep configuration and shared utilities in `app/core/`.
- Use `ai/` as the operational memory for agent workflows.
