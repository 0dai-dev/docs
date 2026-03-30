# managed: true

# Custom Stacks

Place custom stack detector YAML files here to extend 0dai's stack detection.

Custom stacks take priority over upstream detectors during `0dai detect` and `init-existing`.

## Example

```yaml
name: my-custom-stack
priority: 5
match_primary:
  - custom-config.json
  - src/custom/
match_any:
  - package.json
recommended_layout: custom
agents:
  - codex
  - claude
  - opencode
```

## Fields

- `name`: unique stack identifier
- `priority`: lower number wins on tie (default: 50, upstream uses 10-90)
- `match_primary`: high-weight markers unique to this stack (3x score)
- `match_any`: low-weight common markers (1x score)
- `recommended_layout`: layout directory name (or "custom" for project-defined)
- `agents`: which agent CLIs to configure

## Priority Guidelines

- 1-9: project-specific custom stacks (highest priority)
- 10-30: specific upstream stacks (nextjs, flutter, go-service)
- 50: default
- 90: generic catch-all (node, python)
