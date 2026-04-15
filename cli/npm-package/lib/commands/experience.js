"use strict";
const shared = require("../shared");
const { log, D, R, spawnSync, findRepoScript } = shared;

function cmdExperience(target, sub, args) {
  const experienceScript = findRepoScript(target, "experience_pipeline.py");
  if (!experienceScript) {
    log("experience pipeline unavailable in this environment");
    console.log(`  ${D}Expected scripts/experience_pipeline.py in repo checkout${R}`);
    process.exit(1);
  }

  const command = sub || "list";
  const forwarded = [experienceScript, command, "--target", target];
  if (command === "list") {
    if (args.includes("--json")) forwarded.push("--json");
    const sinceIdx = args.indexOf("--since");
    if (sinceIdx >= 0 && args[sinceIdx + 1]) forwarded.push("--since", args[sinceIdx + 1]);
    const agentIdx = args.indexOf("--agent");
    if (agentIdx >= 0 && args[agentIdx + 1]) forwarded.push("--agent", args[agentIdx + 1]);
    const typeIdx = args.indexOf("--type");
    if (typeIdx >= 0 && args[typeIdx + 1]) forwarded.push("--type", args[typeIdx + 1]);
    const resultIdx = args.indexOf("--result");
    if (resultIdx >= 0 && args[resultIdx + 1]) forwarded.push("--result", args[resultIdx + 1]);
    const limitIdx = args.indexOf("--limit");
    if (limitIdx >= 0 && args[limitIdx + 1]) forwarded.push("--limit", args[limitIdx + 1]);
  } else if (command === "stats") {
    if (args.includes("--json")) forwarded.push("--json");
    const periodIdx = args.indexOf("--period");
    if (periodIdx >= 0 && args[periodIdx + 1]) forwarded.push("--period", args[periodIdx + 1]);
    const byIdx = args.indexOf("--by");
    if (byIdx >= 0 && args[byIdx + 1]) forwarded.push("--by", args[byIdx + 1]);
  } else if (command === "warnings") {
    const detectorScript = findRepoScript(target, "anti_pattern_detector.py");
    if (!detectorScript) { log("anti-pattern detector unavailable"); process.exit(1); }
    const fwd = [detectorScript, "warnings", "--target", target];
    if (args.includes("--json")) fwd.push("--json");
    if (args.includes("--refresh")) fwd.push("--refresh");
    if (args.includes("--verbose")) fwd.push("--verbose");
    const sevIdx = args.indexOf("--severity");
    if (sevIdx >= 0 && args[sevIdx + 1]) fwd.push("--severity", args[sevIdx + 1]);
    const wr = spawnSync("python3", fwd, { stdio: "inherit" });
    if (typeof wr.status === "number") process.exit(wr.status);
    process.exit(1);
  } else if (command === "dismiss") {
    const detectorScript = findRepoScript(target, "anti_pattern_detector.py");
    if (!detectorScript) { log("anti-pattern detector unavailable"); process.exit(1); }
    const patternId = args.find(a => a && !a.startsWith("-")) || "";
    if (!patternId) { console.log("Usage: 0dai experience dismiss <pattern_id>"); process.exit(1); }
    const fwd = [detectorScript, "dismiss", patternId, "--target", target];
    if (args.includes("--json")) fwd.push("--json");
    const dr = spawnSync("python3", fwd, { stdio: "inherit" });
    if (typeof dr.status === "number") process.exit(dr.status);
    process.exit(1);
  } else {
    console.log("Usage: 0dai experience [list|stats|warnings|dismiss]");
    process.exit(1);
  }

  const result = spawnSync("python3", forwarded, { stdio: "inherit" });
  if (typeof result.status === "number") process.exit(result.status);
  process.exit(1);
}

module.exports = { cmdExperience };
