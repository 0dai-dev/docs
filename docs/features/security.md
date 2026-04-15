# Security Features

## Secret scanning

### `0dai audit`

Scan the `ai/` directory for accidentally committed secrets.

```bash
0dai audit
# Scanning ai/ for secrets...
# FOUND 2 potential secrets:
#   ai/config/env.yaml:12    AWS access key (AKIA...)
#   ai/prompts/deploy.md:34  GitHub PAT (ghp_...)
# Run with --fix to redact and add to allowlist
```

### Detection patterns

0dai checks for 14 secret types:

| Pattern | Example prefix |
|---------|---------------|
| AWS Access Key | `AKIA` |
| AWS Secret Key | 40-char base64 after `aws_secret` |
| GCP Service Account | `"type": "service_account"` |
| GCP API Key | `AIza` |
| Stripe Secret Key | `sk_live_`, `sk_test_` |
| Stripe Publishable Key | `pk_live_`, `pk_test_` |
| OpenAI API Key | `sk-` (56+ chars) |
| Anthropic API Key | `sk-ant-` |
| GitHub PAT | `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_` |
| Private Key (PEM) | `-----BEGIN.*PRIVATE KEY-----` |
| JWT Token | `eyJ` (base64 JSON header) |
| Generic high-entropy | 32+ char alphanumeric in config context |
| Database URL | `postgres://`, `mysql://`, `mongodb+srv://` with password |
| Slack Token | `xoxb-`, `xoxp-`, `xapp-` |

### Allowlist

False positives can be suppressed in `ai/secret_scanner_allowlist.yaml`:

```yaml
# ai/secret_scanner_allowlist.yaml
allowlist:
  - file: ai/docs/examples/aws-setup.md
    line: 15
    reason: "Example key from AWS docs, not real"

  - pattern: "AKIA_EXAMPLE_.*"
    reason: "Placeholder keys used in templates"
```

## Config drift detection

### `0dai doctor --drift`

Detect when agent config files have diverged from the project manifest.

```bash
0dai doctor --drift
# Checking config consistency...
# DRIFT DETECTED:
#   CLAUDE.md specifies Node 20, but opencode.json says Node 18
#   AGENTS.md lists 5 agents, manifest lists 6
#   .gemini/settings missing model override present in other configs
# Run 0dai doctor --fix to reconcile
```

This checks alignment between:

- `ai/manifest/project.yaml` (source of truth)
- `CLAUDE.md`
- `AGENTS.md`
- `opencode.json`
- `.gemini/settings.json`

## Best practices

1. Run `0dai audit` in CI to catch secrets before they reach remote
2. Add `ai/secret_scanner_allowlist.yaml` to version control
3. Run `0dai doctor --drift` after changing any agent config
4. Keep secrets in environment variables, never in `ai/` files
