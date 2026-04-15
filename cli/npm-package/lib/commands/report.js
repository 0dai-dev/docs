"use strict";
const shared = require("../shared");
const { log, D, R, spawnSync, findRepoScript, VERSION } = shared;

function cmdReport(target, sub, args) {
  const reportScript = findRepoScript(target, "report_manager.py");
  if (!reportScript) {
    log("report manager unavailable in this environment");
    console.log(`  ${D}Expected scripts/report_manager.py in repo checkout${R}`);
    process.exit(1);
  }

  const command = sub || "preview";
  const forwarded = [reportScript, command, "--target", target, "--channel", "npm", "--cli-version", VERSION];

  if (args.includes("--json")) forwarded.push("--json");
  if (command === "auto") {
    if (args.includes("--enable")) forwarded.push("--enable");
    if (args.includes("--disable")) forwarded.push("--disable");
    const idx = args.indexOf("--interval");
    if (idx >= 0 && args[idx + 1]) forwarded.push("--interval", args[idx + 1]);
  }

  const result = spawnSync("python3", forwarded, { stdio: "inherit" });
  if (typeof result.status === "number") process.exit(result.status);
  process.exit(1);
}

module.exports = { cmdReport };
