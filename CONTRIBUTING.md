# Contributing to ZeroDayAI

## Branch Naming

Use descriptive prefixes:

- `feature/<name>` for new functionality
- `fix/<name>` for bug fixes
- `polish/<name>` for cleanup and consistency work
- `docs/<name>` for documentation updates

## Development Flow

1. Create a branch from `main`.
2. Make changes and verify locally.
3. Run validation before committing:
   ```bash
   python3 scripts/validate_templates.py
   python3 scripts/roadmap_guardian.py
   bash tests/smoke_test.sh
   ```
4. Commit with a clear message explaining *why*, not just *what*.
5. Merge to `main` after verification passes.

## Commit Messages

- Lead with a short imperative summary (under 72 chars).
- Add a blank line and a body paragraph for non-trivial changes.
- Reference issue numbers when applicable.

## Adding a New Stack

When adding a new stack layout, update all of these:

1. `project_layouts/<stack>/scaffold.sh` — directory and file creation.
2. `project_layouts/<stack>/structure.md` — recommended layout docs.
3. `templates/layer/ai/patterns/detectors/<stack>.yaml` — detection rules.
4. `templates/layer/ai/patterns/stacks/<stack>.yaml` — stack definition.
5. `bootstrap/common.sh` `layout_for_stack()` — routing entry.
6. `scripts/validate_templates.py` — add to `expected_detectors` and `validate_layouts`.
7. `tests/smoke_test.sh` — add scaffold `chmod` and `init-new` test.
8. `README.md` — update tree and Included Stacks list.

Run `python3 scripts/roadmap_guardian.py` to verify consistency.

## Adding a New Command

1. Create the bootstrap script in `bootstrap/`.
2. Wire it into `bin/0dai-repo` case statement.
3. Wire it into `bin/0dai` if it should be a top-level command.
4. Add smoke test coverage in `tests/smoke_test.sh`.
5. Document in `docs/bootstrap-spec.md`.

## Validation

Three levels of validation are available:

- **Fast**: `python3 scripts/validate_templates.py` — structural checks.
- **Consistency**: `python3 scripts/roadmap_guardian.py` — cross-file alignment.
- **Full**: `bash tests/smoke_test.sh` — end-to-end init/sync/harvest cycle.

All three must pass before merging to `main`.

## Release Process

1. Update `VERSION` with the new version number.
2. Add a section to `CHANGELOG.md`.
3. Create `release-notes/v<version>.md`.
4. Verify with roadmap guardian and smoke tests.
5. Merge to `main` and tag: `git tag v<version> && git push origin v<version>`.
6. The release workflow creates a GitHub Release automatically.
