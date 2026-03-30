# Backend API Structure

Recommended greenfield layout:

```text
repo/
  ai/
  services/
    api/
      src/
      tests/
  packages/
  infra/
  tools/
  docs/
```

Rules:

- Keep deployable services under `services/`.
- Put shared code or clients into `packages/`.
- Treat `ai/` as the operational memory for agent workflows.
