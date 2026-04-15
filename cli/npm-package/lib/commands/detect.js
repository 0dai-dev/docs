"use strict";
const shared = require("../shared");
const { D, R, log, apiCall, collectMetadata } = shared;

async function cmdDetect(target) {
  const OPTIONAL_CLIS = ["gemini", "aider", "opencode"];
  const { projectFiles, manifestContents, clis: localClis } = collectMetadata(target);
  // Send file contents AND local CLI inventory so server can do content-based detection
  const result = await apiCall("/v1/detect", {
    project_files: projectFiles,
    manifest_contents: manifestContents,
    available_clis: localClis,
  });
  if (result.error) { log(`error: ${result.error}`); return; }
  console.log(`stack: ${result.stack || "?"}`);
  // Use local CLIs if server didn't return any (server can't detect locally installed binaries)
  const clis = (result.available_clis && result.available_clis.length && result.available_clis[0]) ? result.available_clis : localClis;
  if (clis.length) {
    console.log(`clis:  ${clis.join(", ")}`);
  } else {
    console.log(`clis:  none detected`);
    console.log(`       ${D}install claude, codex, or opencode to use 0dai${R}`);
  }
  // Explain optional CLIs so missing doesn't alarm users
  const missing = OPTIONAL_CLIS.filter(c => !clis.includes(c));
  if (missing.length && clis.length) {
    console.log(`       ${D}optional (not installed): ${missing.join(", ")}${R}`);
  }
}

module.exports = { cmdDetect };
