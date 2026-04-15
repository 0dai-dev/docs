#!/usr/bin/env node
/**
 * Post-install welcome message for 0dai CLI.
 * Always exits 0 — must never break npm install.
 */
"use strict";
try {
  // Suppress in CI environments
  if (process.env.CI || process.env.CONTINUOUS_INTEGRATION || process.env.BUILD_NUMBER) {
    process.exit(0);
  }

  const pkg = require("../package.json");
  const v = pkg.version || "?";

  console.log("");
  console.log("  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510");
  console.log("  \u2502  0dai installed successfully! v" + v.padEnd(10) + "\u2502");
  console.log("  \u2502                                         \u2502");
  console.log("  \u2502  Get started:                           \u2502");
  console.log("  \u2502    cd your-project                      \u2502");
  console.log("  \u2502    0dai init                             \u2502");
  console.log("  \u2502                                         \u2502");
  console.log("  \u2502  Docs: https://0dai.dev/docs            \u2502");
  console.log("  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518");
  console.log("");
} catch (_) {
  // Never fail
}
