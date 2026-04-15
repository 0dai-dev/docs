# Common Errors and Solutions

## "No 0dai config found"

Your project has no `ai/` layer yet. Run `0dai init` to scaffold it.

## "Not authenticated"

Your CLI session has expired or was never set up. Run `0dai auth login` to authenticate.

## "Swarm requires Pro plan"

Multi-agent swarm delegation is a Pro feature. Either switch to free-tier mode with `0dai activate free` or upgrade your plan at https://0dai.dev.

## "SECRET DETECTED — commit blocked"

The secret scanner found a potential credential in your `ai/` layer. Remove the secret and retry. If it is a false positive, run `0dai security allowlist` to exclude the pattern.

## "Config drift detected"

Local config has diverged from the canonical source. To accept the remote version, run `0dai sync --force`. To keep your local changes, run `0dai drift accept FILE`.

## "Rate limit exceeded"

You have hit the API rate limit. Wait a few minutes and retry, or upgrade your plan for higher limits.

## "Cannot find module 'node-pty'"

The `node-pty` native module is only required for `0dai terminal`. Install it globally:

```bash
npm i -g node-pty
```

## "ai/ layer already exists"

The project was already initialized. Use `0dai sync` to update the existing layer instead of `0dai init`.

## "Graph sync failed"

Verify your authentication is valid with `0dai auth status`. Graph sync requires a Pro plan — confirm your subscription is active.
