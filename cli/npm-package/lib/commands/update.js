"use strict";
const shared = require("../shared");
const { log, SUPPORTED_CLIS } = shared;

function cmdUpdate(args) {
  const { execFileSync: _ef3, execSync } = require("child_process");
  const dryRun = args.includes("--dry-run");

  // 0dai self-update entry, then all supported agent CLIs.
  const CLIS = [
    { name: "0dai", pkg: "@0dai-dev/cli", bin: "0dai", pkgType: "npm" },
    ...SUPPORTED_CLIS,
  ];

  let updated = 0;
  for (const cli of CLIS) {
    let installed = false, ver = null;
    try {
      const out = _ef3(cli.bin, ["--version"], { timeout: 8000 }).toString().trim();
      installed = true;
      const m = out.match(/(\d+\.\d+\.\d+)/);
      if (m) ver = m[1];
    } catch {}

    if (!installed) continue;

    let latest = null;
    if (cli.pkgType === "npm" && cli.pkg) {
      try { latest = _ef3("npm", ["view", cli.pkg, "version"], { timeout: 5000 }).toString().trim(); } catch {}
    } else if (cli.pkgType === "pip" && cli.pkg) {
      try {
        const out = _ef3("pip", ["index", "versions", cli.pkg], { timeout: 8000, encoding: "utf8" });
        const m = out.match(/LATEST:\s*(\d+\.\d+\.\d+)/i) || out.match(/(\d+\.\d+\.\d+)/);
        if (m) latest = m[1];
      } catch {}
    }

    if (!latest || latest === ver) {
      console.log(`  ${cli.name} ${ver || ""} — up to date`);
      continue;
    }

    console.log(`  ${cli.name} ${ver} → ${latest}`);
    if (dryRun) { updated++; continue; }

    try {
      if (cli.pkgType === "npm") {
        log(`updating ${cli.name}...`);
        execSync(`npm install -g ${cli.pkg}@latest`, { timeout: 60000, stdio: "pipe" });
        log(`${cli.name} updated to ${latest}`);
        updated++;
      } else if (cli.pkgType === "pip") {
        log(`updating ${cli.name}...`);
        execSync(`pip install --upgrade ${cli.pkg}`, { timeout: 60000, stdio: "pipe" });
        log(`${cli.name} updated to ${latest}`);
        updated++;
      }
    } catch (e) {
      log(`failed to update ${cli.name}: ${e.message.split("\n")[0]}`);
    }
  }
  if (updated) {
    log(`${dryRun ? "would update" : "updated"} ${updated} CLI(s)`);
  } else {
    log("all CLIs are up to date");
  }
}

module.exports = { cmdUpdate };
