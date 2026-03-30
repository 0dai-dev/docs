# Next.js Structure

Recommended greenfield layout:

```text
repo/
  ai/
  apps/
    web/
      app/
      public/
  packages/
    ui/
    config/
  infra/
  tools/
  docs/
```

Rules:

- Keep the web app in `apps/web/`.
- Put reusable UI and shared config in `packages/`.
- Keep deployment assets in `infra/`.
