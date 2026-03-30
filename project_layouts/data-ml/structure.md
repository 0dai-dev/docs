# Data / ML Workspace Structure

Recommended greenfield layout:

```text
repo/
  ai/
  notebooks/
  src/
    data/
    features/
    models/
    pipelines/
  tests/
  data/
    raw/
    processed/
  models/
  configs/
  infra/
  tools/
  docs/
```

Rules:

- Keep exploratory work in `notebooks/`.
- Put production-quality code under `src/` with clear module separation.
- Data assets live in `data/`; trained model artifacts in `models/`.
- Pipeline definitions go in `src/pipelines/`.
- Configuration files (hyperparameters, experiment settings) go in `configs/`.
- Use `ai/` as the operational memory for agent workflows.
