"use strict";
const shared = require("../shared");
const { log, T, R, D, fs, path, apiCall, AUTH_FILE, buildProjectIdentity, collectMetadata, recordExperienceEvent } = shared;

async function cmdGraph(target, sub, args) {
  const graphFile = path.join(target, "ai", "manifest", "project_graph.json");

  if (sub === "push") {
    // Check auth
    let auth;
    try { auth = JSON.parse(fs.readFileSync(AUTH_FILE, "utf8")); } catch {}
    if (!auth || !auth.access_token) {
      log("Graph push requires an account. Run: 0dai auth login");
      return;
    }

    if (!fs.existsSync(graphFile)) {
      log("No local graph found. Run: 0dai graph init or create ai/manifest/project_graph.json");
      return;
    }

    let localGraph;
    try { localGraph = JSON.parse(fs.readFileSync(graphFile, "utf8")); } catch (e) {
      log(`Error reading graph file: ${e.message}`);
      return;
    }

    const nodes = localGraph.nodes || {};
    const edges = localGraph.edges || [];
    const identity = buildProjectIdentity(target, collectMetadata(target));

    log(`Pushing graph (${Object.keys(nodes).length} nodes, ${edges.length} edges)...`);
    const result = await apiCall("/v1/graph/sync", {
      project_id: identity.project_id,
      nodes,
      edges,
    });

    if (result.error) {
      log(`Error: ${result.error}`);
      return;
    }

    const parts = [];
    if (result.added_nodes) parts.push(`${result.added_nodes} nodes added`);
    if (result.updated_nodes) parts.push(`${result.updated_nodes} nodes updated`);
    if (result.deleted_nodes) parts.push(`${result.deleted_nodes} nodes deleted`);
    if (result.added_edges) parts.push(`${result.added_edges} edges added`);
    if (result.deleted_edges) parts.push(`${result.deleted_edges} edges deleted`);

    log(`Sync: ${parts.join(", ") || "up to date"}`);
    if (result.edges_rejected) {
      log(`${D}Edges rejected: upgrade to Pro for edge sync (0dai upgrade)${R}`);
    }
    recordExperienceEvent(target, {
      event_type: "graph_synced",
      agent: "cli",
      model: "0dai-cli",
      effort: "medium",
      task: { goal: "push graph to server", task_type: "feat", result: "success", elapsed_seconds: 0, cost_usd: 0 },
      context: { stack: "unknown", files_touched: 1, tests_passed: true, graph_nodes_used: Object.keys(nodes).length, graph_edges_used: edges.length },
    });
    return;
  }

  if (sub === "pull") {
    let auth;
    try { auth = JSON.parse(fs.readFileSync(AUTH_FILE, "utf8")); } catch {}
    if (!auth || !auth.access_token) {
      log("Graph pull requires an account. Run: 0dai auth login");
      return;
    }

    const identity = buildProjectIdentity(target, collectMetadata(target));
    log("Pulling graph from server...");
    const result = await apiCall(`/v1/graph/pull?project_id=${identity.project_id}`);

    if (result.error) {
      log(`Error: ${result.error}`);
      if (result.hint) log(`Hint: ${result.hint}`);
      return;
    }

    // Merge into local graph
    let localGraph = { nodes: {}, edges: [], meta: {} };
    if (fs.existsSync(graphFile)) {
      try { localGraph = JSON.parse(fs.readFileSync(graphFile, "utf8")); } catch {}
    }

    // Merge nodes (server wins on conflicts)
    const serverNodes = result.nodes || {};
    const localNodes = localGraph.nodes || {};
    const mergedNodes = { ...localNodes, ...serverNodes };

    // Merge edges (server wins for Pro users)
    const serverEdges = result.edges || [];
    const localEdges = localGraph.edges || [];
    const mergedEdges = [...localEdges, ...serverEdges];

    // Deduplicate edges by (from, to, type)
    const seen = new Set();
    const uniqueEdges = [];
    for (const e of mergedEdges) {
      const key = `${e.from}|${e.to}|${e.type}`;
      if (!seen.has(key)) {
        seen.add(key);
        uniqueEdges.push(e);
      }
    }

    const merged = {
      nodes: mergedNodes,
      edges: uniqueEdges,
      meta: {
        ...localGraph.meta,
        ...result.meta,
        node_count: Object.keys(mergedNodes).length,
        edge_count: uniqueEdges.length,
      },
    };

    fs.mkdirSync(path.dirname(graphFile), { recursive: true });
    fs.writeFileSync(graphFile, JSON.stringify(merged, null, 2) + "\n", "utf8");

    log(`Pulled: ${Object.keys(mergedNodes).length} nodes, ${uniqueEdges.length} edges`);
    if (result.meta && result.meta.edges_stripped) {
      log(`${D}Edges not included: upgrade to Pro for full graph sync (0dai upgrade)${R}`);
    }
    recordExperienceEvent(target, {
      event_type: "graph_synced",
      agent: "cli",
      model: "0dai-cli",
      effort: "medium",
      task: { goal: "pull graph from server", task_type: "feat", result: "success", elapsed_seconds: 0, cost_usd: 0 },
      context: { stack: "unknown", files_touched: 1, tests_passed: true, graph_nodes_used: Object.keys(mergedNodes).length, graph_edges_used: uniqueEdges.length },
    });
    return;
  }

  if (sub === "status") {
    let localNodes = 0, localEdges = 0;
    if (fs.existsSync(graphFile)) {
      try {
        const g = JSON.parse(fs.readFileSync(graphFile, "utf8"));
        localNodes = Object.keys(g.nodes || {}).length;
        localEdges = (g.edges || []).length;
      } catch {}
    }

    log(`Local graph: ${localNodes} nodes, ${localEdges} edges`);

    // Check plan for edge sync status
    let auth;
    try { auth = JSON.parse(fs.readFileSync(AUTH_FILE, "utf8")); } catch {}
    if (auth && auth.access_token) {
      const plan = (auth.plan || "free").toLowerCase();
      const edgeStatus = plan === "free" ? `${D}nodes only (Pro for edges)${R}` : `${T}full sync${R}`;
      log(`Server sync: ${edgeStatus}`);
    } else {
      log(`${D}Not authenticated — graph sync unavailable${R}`);
    }
    return;
  }

  if (sub === "history") {
    const authFile = path.join(require("os").homedir(), ".0dai", "auth.json");
    let auth = {};
    try { auth = JSON.parse(fs.readFileSync(authFile, "utf8")); } catch {}
    const plan = (auth.plan || "free").toLowerCase();
    const limitIdx = args.indexOf("--limit");
    const limit = limitIdx >= 0 && args[limitIdx + 1] ? parseInt(args[limitIdx + 1], 10) || 50 : 50;
    const sinceIdx = args.indexOf("--since");
    const since = sinceIdx >= 0 ? args[sinceIdx + 1] : null;
    const nodeIdx = args.indexOf("--node");
    const nodeId = nodeIdx >= 0 ? args[nodeIdx + 1] : null;

    if (["pro", "team", "enterprise"].includes(plan) && auth.access_token) {
      const identity = buildProjectIdentity(target, collectMetadata(target));
      const params = new URLSearchParams({
        project_id: identity.project_id,
        limit: String(Math.max(1, limit)),
      });
      if (since) params.set("since", since);
      if (nodeId) params.set("target_id", nodeId);
      const result = await apiCall(`/v1/graph/history?${params.toString()}`);
      if (result.error) {
        log(`Error: ${result.error}`);
        if (result.hint) log(result.hint);
        return;
      }
      const entries = result.mutations || [];
      if (!entries.length) { console.log("  No graph history yet."); return; }
      for (const entry of entries) {
        const actor = (entry.agent || "unknown").padEnd(7);
        const context = entry.context ? ` | "${entry.context}"` : "";
        console.log(`  ${entry.timestamp || "?"} | ${actor} | ${entry.action.padEnd(13)} | ${entry.target_id}${context}`);
      }
      return;
    }
    log(`${D}Graph history requires Pro plan. Upgrade: 0dai upgrade${R}`);
    return;
  }

  if (sub === "context") {
    if (!fs.existsSync(graphFile)) {
      log("No local graph found. Run: 0dai graph init or create ai/manifest/project_graph.json");
      return;
    }
    const slicerScript = shared.findRepoScript(target, "graph_slicer_cli.py");
    if (!slicerScript) {
      log("graph slicer unavailable in this environment");
      console.log(`  ${D}Expected scripts/graph_slicer_cli.py in repo checkout${R}`);
      return;
    }
    const forwarded = [slicerScript, "--target", target];
    let i = 0;
    while (i < args.length) {
      if (args[i] === "--scope" && args[i + 1]) { forwarded.push("--scope", args[i + 1]); i += 2; }
      else if (args[i] === "--task" && args[i + 1]) { forwarded.push("--task", args[i + 1]); i += 2; }
      else if (args[i] === "--depth" && args[i + 1]) { forwarded.push("--depth", args[i + 1]); i += 2; }
      else if (args[i] === "--budget" && args[i + 1]) { forwarded.push("--budget", args[i + 1]); i += 2; }
      else if (args[i] === "--json") { forwarded.push("--json"); i += 1; }
      else { i += 1; }
    }
    const result = shared.spawnSync("python3", forwarded, { stdio: "inherit" });
    if (typeof result.status === "number" && result.status !== 0) process.exit(result.status);
    return;
  }

  if (sub === "outcomes") {
    const authFile = path.join(require("os").homedir(), ".0dai", "auth.json");
    let auth = {};
    try { auth = JSON.parse(fs.readFileSync(authFile, "utf8")); } catch {}
    const plan = (auth.plan || "free").toLowerCase();
    if (!["pro", "team", "enterprise"].includes(plan)) {
      log(`${D}Outcomes require Pro plan. Upgrade: 0dai upgrade${R}`);
      return;
    }
    if (!auth.access_token) {
      log("Graph outcomes requires an account. Run: 0dai auth login");
      return;
    }
    const identity = buildProjectIdentity(target, collectMetadata(target));
    const params = new URLSearchParams({ project_id: identity.project_id });
    const limitIdx = args.indexOf("--limit");
    if (limitIdx >= 0 && args[limitIdx + 1]) params.set("limit", args[limitIdx + 1]);
    const sinceIdx = args.indexOf("--since");
    if (sinceIdx >= 0 && args[sinceIdx + 1]) params.set("since", args[sinceIdx + 1]);
    const result = await apiCall(`/v1/outcomes?${params.toString()}`);
    if (result.error) { log(`Error: ${result.error}`); return; }
    const stats = result.stats || {};
    log(`Outcomes: ${stats.total || 0} total, ${stats.success_rate || 0}% success rate`);
    if (result.outcomes && result.outcomes.length) {
      for (const o of result.outcomes.slice(0, 10)) {
        console.log(`  ${o.result || "?"} | ${o.agent || "?"} | ${o.title || o.task_id || "?"}`);
      }
    }
    return;
  }

  console.log("Usage: 0dai graph [push|pull|status|history|context|outcomes]");
  console.log("  push     Upload local graph to server (Pro: edges, Free: nodes only)");
  console.log("  pull     Download server graph and merge locally");
  console.log("  status   Show local graph stats and sync state");
  console.log("  history  Show graph mutation timeline [--since 7d] [--node ID] [--limit 50]");
  console.log("  context  Get relevant graph context for a task [--scope FILE] [--task TYPE]");
  console.log("  outcomes Show outcome analytics (Pro only)");
}

module.exports = { cmdGraph };
