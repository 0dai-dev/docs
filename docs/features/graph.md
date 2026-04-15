# Graph -- Project Knowledge Graph

The knowledge graph stores structured relationships between components, technologies, decisions, and risks in your project. Agents query the graph automatically to get relevant context before writing code.

## Commands

### `0dai graph status`

Show local graph statistics. Available on all plans.

```bash
0dai graph status
# Nodes: 47 | Edges: 83
# Components: 12 | Technologies: 8 | Decisions: 15
# Risks: 4 | Requirements: 6 | Outcomes: 2
# Last updated: 2 hours ago
```

### `0dai graph push`

> Plan required: **Pro** or **Team**

Upload your local graph to the 0dai cloud for cross-machine sync and team sharing.

```bash
0dai graph push
# Pushed 47 nodes, 83 edges to remote
```

### `0dai graph pull`

> Plan required: **Pro** or **Team**

Download the remote graph and merge it with your local copy. Conflicts are resolved by latest-write-wins.

```bash
0dai graph pull
# Pulled 12 new nodes, 5 updated edges
# Local graph: 59 nodes, 101 edges
```

## Node types

| Type | Description | Example |
|------|-------------|---------|
| **Component** | Code module or service | `auth-service`, `payment-api` |
| **Technology** | Framework, library, tool | `Next.js 14`, `PostgreSQL` |
| **Decision** | Architectural choice | "Use JWT for auth tokens" |
| **Risk** | Identified concern | "Rate limiting not implemented" |
| **Requirement** | Feature or constraint | "GDPR data export endpoint" |
| **Outcome** | Measured result | "Latency reduced from 200ms to 45ms" |

## Context slicing

When an agent starts work, 0dai automatically slices the graph to extract only the nodes relevant to the task. This means agents get:

- Components they will modify and their direct dependencies
- Technologies in use for those components
- Recent decisions affecting the area
- Known risks in the neighborhood

No manual prompt engineering needed -- the graph handles context delivery.

## How the graph is built

The graph populates from three sources:

1. **Automatic discovery** -- `0dai` scans your codebase for imports, configs, and structure
2. **Agent contributions** -- agents record decisions and outcomes as they work
3. **Manual entries** -- edit `ai/manifest/project.yaml` to add nodes directly

## Local storage

Graph data lives in `ai/graph/` as JSON files. These are safe to commit to version control.

```
ai/graph/
  nodes.json      # all graph nodes
  edges.json      # relationships between nodes
  meta.json       # sync metadata
```
