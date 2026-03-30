# React Native Structure

Recommended greenfield layout:

```text
repo/
  ai/
  src/
    screens/
    navigation/
    components/
    services/
    hooks/
    assets/
  __tests__/
  infra/
  tools/
  docs/
```

Rules:

- Keep screen components in `src/screens/`.
- Put navigation configuration in `src/navigation/`.
- Shared UI components go in `src/components/`.
- API clients and business logic go in `src/services/`.
- Custom React hooks go in `src/hooks/`.
- Static assets go in `src/assets/`.
- Use `ai/` as the operational memory for agent workflows.
