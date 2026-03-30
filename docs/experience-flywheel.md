# Experience Flywheel

ZeroDayAI treats experience as a separate knowledge system from instructions and skills.

## Loop

`signals -> normalization -> selection -> promotion -> rollout -> measurement`

## Project-Local Sources

- wrappers such as `0dai task`
- Claude hooks
- CI workflows
- human-reported incidents and lessons

## Canonical Experience Tree

```text
ai/experience/
  outbox/
  events/
  candidates/
  accepted/
    rules/
    skills/
    playbooks/
    anti-patterns/
  rejected/
  archived/
```

## Promotion Principle

- raw events are not durable knowledge
- candidates are reviewed
- accepted knowledge is promoted into packs, skills, playbooks, rules, or anti-patterns
- promoted knowledge should flow back into generated repo files through sync

## Harvest Step

- write normalized JSON or JSONL events into `ai/experience/outbox/`
- `./bin/0dai task run ... -- <command>` is the standard local wrapper for event creation
- run `./bin/0dai harvest --target <repo>`
- the harvester archives processed events into `ai/experience/events/`
- repeated or promotable events become markdown candidates in `ai/experience/candidates/`

## Promote Step

- review candidate lessons in `ai/experience/candidates/`
- run `./bin/0dai promote --target <repo>`
- accepted items move into `ai/experience/accepted/{rules,skills,playbooks,anti-patterns}/`
- promoted knowledge is now eligible for future pack/rule/skill roll-in

## Aggregation Step

- run `python3 scripts/aggregate_experience.py`
- generate `ai/experience/reports/0dai-experience-report.json`
- upload the report as a GitHub Actions artifact for cross-run review
- run `python3 scripts/prepare_knowledge_issue.py`
- generate `ai/experience/reports/0dai-knowledge-intake.json` as the GitHub-native intake summary
- run `python3 scripts/score_knowledge_intake.py`
- generate `ai/experience/reports/0dai-knowledge-intake-scored.json` with score, confidence, and duplicate key
- optionally run `python3 scripts/create_knowledge_issue.py --repo <owner/repo>` to open an intake issue from that summary
