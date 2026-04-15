# Versioning Policy

## Semantic Versioning

0dai follows [Semantic Versioning 2.0.0](https://semver.org):

```
MAJOR.MINOR.PATCH

MAJOR — breaking changes (CLI interface, tier gates, activation requirements)
MINOR — new features (commands, integrations, agent support)
PATCH — bug fixes, refactoring, documentation
```

## Current Version

Defined in `VERSION` (project root). Synced to:
- `cli/npm-package/package.json`
- `web/package.json`
- `ai/VERSION`
- `bootstrap/common.sh` (CURRENT_AI_VERSION)

## Release Process

```bash
# Preview what would be released
scripts/release.sh minor --dry-run

# Cut a release (must be on main, clean tree)
scripts/release.sh minor

# Pre-release (beta tag on npm)
scripts/release.sh minor  # then manually tag with -rc.1 suffix
```

### What `scripts/release.sh` does:
1. Verify clean tree + main branch
2. Compute new version from bump type
3. Parse conventional commits since last tag
4. Generate CHANGELOG section
5. Update VERSION file
6. Create release-notes stub
7. Commit + tag
8. Push + create GitHub Release

### What `.github/workflows/release.yml` does (on tag push):
1. Validate: templates, smoke test, guardian, unit tests, secret scan
2. Verify VERSION matches tag
3. Create GitHub Release with notes
4. Publish to npm (`@0dai-dev/cli`)
5. Pre-releases get `beta` npm tag

## Version Sync

All version references must match `VERSION` file. Verified by:
- `scripts/consistency_check.py` — checks root/ai/cli/web version alignment
- `scripts/release_auditor.py` — checks changelog, bootstrap, SDK

## npm Publishing

- Package: `@0dai-dev/cli`
- Registry: https://registry.npmjs.org
- Auth: `NPM_TOKEN` GitHub secret
- Pre-releases: `npm install @0dai-dev/cli@beta`
- Stable: `npm install -g @0dai-dev/cli`

## Release Cadence

- After each sprint (every 2 weeks) if significant changes
- Hotfixes: immediate patch release for critical bugs
- Breaking changes: coordinate with ROADMAP.md phase transitions
