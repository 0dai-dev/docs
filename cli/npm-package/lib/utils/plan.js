/**
 * Plan detection and quota management.
 * Extracted from shared.js to reduce module size.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");

const PLAN_LEVELS = { trial: 0, free: 0, essential: 1, pro: 2, team: 3, enterprise: 4 };

function _detectPlanLocal(target) {
  const projYaml = path.join(target, "ai", "manifest", "project.yaml");
  if (fs.existsSync(projYaml)) {
    try {
      const text = fs.readFileSync(projYaml, "utf8");
      for (const line of text.split("\n")) {
        if (line.startsWith("plan:")) {
          const plan = line.split(":")[1].trim().toLowerCase();
          if (PLAN_LEVELS[plan] !== undefined) return plan;
        }
      }
    } catch {}
  }
  const projectsFile = path.join(os.homedir(), ".0dai", "projects.json");
  if (fs.existsSync(projectsFile)) {
    try {
      const projects = JSON.parse(fs.readFileSync(projectsFile, "utf8"));
      const targetResolved = path.resolve(target);
      for (const p of (projects.projects || [])) {
        if (path.resolve(p.path || "") === targetResolved) {
          const plan = (p.plan || "").toLowerCase();
          if (PLAN_LEVELS[plan] !== undefined) return plan;
        }
      }
    } catch {}
  }
  return "free";
}

function requirePlan(requiredPlan, featureName, target) {
  const plan = _detectPlanLocal(target || process.cwd());
  if ((PLAN_LEVELS[plan] || 0) >= (PLAN_LEVELS[requiredPlan] || 0)) return null;
  return {
    error: `${featureName} requires ${requiredPlan.charAt(0).toUpperCase() + requiredPlan.slice(1)} plan ($15/mo).`,
    hint: "Run: 0dai upgrade",
    current_plan: plan,
  };
}

function getSwarmQuotaLocal(target) {
  const plan = _detectPlanLocal(target);
  const limits = { free: 0, pro: 50, team: 200, enterprise: 999999 };
  const dailyLimit = limits[plan] || 0;
  const budgetPath = path.join(target, "ai", "swarm", "budget.json");
  let usedToday = 0;
  if (fs.existsSync(budgetPath)) {
    try {
      const budget = JSON.parse(fs.readFileSync(budgetPath, "utf8"));
      const today = new Date().toISOString().slice(0, 10);
      usedToday = (budget.daily_tasks || {})[today] || 0;
    } catch {}
  }
  return { plan, daily_limit: dailyLimit, used_today: usedToday, remaining: Math.max(0, dailyLimit - usedToday) };
}

module.exports = {
  PLAN_LEVELS,
  _detectPlanLocal,
  requirePlan,
  getSwarmQuotaLocal,
};
