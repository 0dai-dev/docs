# Python Service Structure

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

- Put deployable Python service code under `services/api/src/`.
- Keep tests close to the service boundary in `services/api/tests/`.
- Use `packages/` for shared internal libraries.
