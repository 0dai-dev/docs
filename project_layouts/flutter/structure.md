# Flutter Structure

Recommended greenfield layout:

```text
repo/
  ai/
  app/
    lib/
    test/
    assets/
  packages/
  infra/
  tools/
  docs/
```

Rules:

- Keep the product app isolated in `app/`.
- Place shared Dart packages in `packages/`.
- Keep deployment and CI assets in `infra/`.
- Store AI-specific architecture and workflow data in `ai/`.
