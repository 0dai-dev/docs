# Fullstack Monorepo Structure

Recommended greenfield layout:

```text
repo/
  ai/
  apps/
    web/
      app/
  services/
    api/
      src/
  packages/
    ui/
    sdk/
  infra/
  tools/
  docs/
```

Rules:

- Keep product surfaces split between `apps/` and `services/`.
- Put cross-cutting code in `packages/`.
- Keep `ai/` at repo root so all agents see the whole system map.
