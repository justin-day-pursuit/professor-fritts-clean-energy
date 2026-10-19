/* eslint-disable @typescript-eslint/no-require-imports -- a plain Node script, so it loads modules with require */
// Checks the helpers that run a real analysis from the design page (app/plan-mockup/live-run.ts): reading dollar amounts and goals,
// building the profile and question, listing the steps, and how a run ends (finished, needs more information, daily limit,
// planner unreachable, timeout). It compiles the file with the TypeScript compiler and stubs the backend calls, so it makes no
// network calls and costs nothing. Run it with: npm run check:live-run
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const frontend = process.argv[2] || process.cwd();
const ts = require(path.join(frontend, "node_modules", "typescript"));
const source = fs.readFileSync(path.join(frontend, "app/plan-mockup/live-run.ts"), "utf8");
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText;

class ApiError extends Error { constructor(status, message) { super(message); this.status = status; } }
let script = { createSession: async () => ({ id: "s1" }), startRun: async () => ({}), getLatestRun: async () => ({}), uploadDocument: async () => ({}) };
const stubs = {
  "@/lib/api": { ApiError, createSession: (...a) => script.createSession(...a), startRun: (...a) => script.startRun(...a), getLatestRun: (...a) => script.getLatestRun(...a), uploadDocument: (...a) => script.uploadDocument(...a) },
  "./address": { buildingTypeLabel: () => "School or educational building", numberOf: (v) => (Number(v) > 0 ? Number(v) : null) },
};
const mod = { exports: {} };
vm.runInNewContext(js, { module: mod, exports: mod.exports, require: (n) => stubs[n], setTimeout, Date, Number, Object, String, Array, Promise, Math, Error }, {});
const L = mod.exports;

let failed = 0;
const eq = (name, got, want) => {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) failed++;
  console.log(ok ? "  ok " : "  FAIL", name, ok ? "" : `got ${JSON.stringify(got)} want ${JSON.stringify(want)}`);
};

eq("money $400k", L.parseMoney("$400k"), 400000);
eq("money 800,000", L.parseMoney("$800,000"), 800000);
eq("money 1.2 million", L.parseMoney("1.2 million"), 1200000);
eq("money 750K", L.parseMoney("750K"), 750000);
eq("money plain 250000", L.parseMoney("250000"), 250000);
eq("money words only", L.parseMoney("a lot"), null);
eq("money empty", L.parseMoney(""), null);
eq("number with commas", L.parseNumber("456,834"), 456834);
eq("number zero is blank", L.parseNumber("0"), null);
eq("goal 30% by 2030", L.parseGoal("cut grid electricity 30% by 2030"), { percent: 30, year: 2030 });
eq("goal with no numbers", L.parseGoal("go green"), { percent: null, year: null });
eq("question with everything", L.buildQuestion({ goal: "cut grid electricity 30% by 2030", budget_amount: "$800,000", critical_loads: "emergency lighting" }), "How can we cut grid power 30% by 2030 and keep emergency lighting running during outages on a $800,000 capital budget?");
eq("question words only", L.buildQuestion({ goal: "Be greener.", budget_amount: "400k" }), "How can we be greener on a $400,000 capital budget?");

const found = { borough: "Bronx", label: "1871 WALTON AVENUE, Bronx", record: { bldgarea: "46700", yearbuilt: "1994" } };
eq("missing: nothing typed", L.missingForRun(found, {}), ["capital budget", "energy goal"]);
eq("missing: all there", L.missingForRun(found, { budget_amount: "$1", goal: "x" }), []);
eq("missing: no address", L.missingForRun(null, { budget_amount: "$1", goal: "x" }), ["address"]);

const profile = L.buildProfile(found, { annual_kwh: "456,834", budget_amount: "$800,000", goal: "cut 30% by 2030", roof_type: "flat" });
eq("profile address", profile.address, "1871 WALTON AVENUE");
eq("profile numbers", [profile.annual_kwh, profile.budget_amount, profile.goal_percent, profile.target_year, profile.floor_area_sqft], [456834, 800000, 30, 2030, 46700]);
eq("profile leaves blanks out", "critical_loads" in profile || "roof_area_sqft" in profile || "existing_solar_kw" in profile, false);
eq("profile 'none' defaults", [profile.existing_renewables, profile.existing_efficiency], ["none", "none"]);

// The goal as numbers (its own boxes), the floor area from the energy report, and hours of backup power.
eq("goal numbers: boxes win over a sentence", L.goalNumbers({ goal: "cut 30% by 2030", goal_percent: "40", target_year: "2032" }), { percent: 40, year: 2032 });
eq("goal numbers: boxes alone", L.goalNumbers({ goal_percent: "30", target_year: "2030" }), { percent: 30, year: 2030 });
eq("goal numbers: a percent outside 1 to 100 is not given", L.goalNumbers({ goal_percent: "150" }).percent, null);
eq("question from the number boxes", L.buildQuestion({ goal_percent: "30", target_year: "2030", budget_amount: "750k", critical_loads: "the gym" }), "How can we cut grid power 30% by 2030 and keep the gym running during outages on a $750,000 capital budget?");
eq("missing: the goal boxes count", L.missingForRun(found, { budget_amount: "$1", goal_percent: "30" }), []);
eq("missing: a percent out of range counts as no goal", L.missingForRun(found, { budget_amount: "$1", goal_percent: "150" }), ["energy goal"]);
const numeric = L.buildProfile(found, { budget_amount: "$750,000", goal_percent: "30", target_year: "2030", backup_hours_wanted: "8", floor_area_sqft: "43,760" });
eq("profile from the number boxes", [numeric.goal, numeric.goal_percent, numeric.target_year, numeric.backup_hours_wanted], ["Cut grid electricity 30% by 2030", 30, 2030, 8]);
eq("profile floor area: the energy report's figure wins over the tax lot's", numeric.floor_area_sqft, 43760);
eq("profile floor area: the tax lot's is the fallback", L.buildProfile(found, { budget_amount: "$1", goal_percent: "30" }).floor_area_sqft, 46700);
eq("profile leaves backup hours out when blank", "backup_hours_wanted" in L.buildProfile(found, { budget_amount: "$1", goal_percent: "30" }), false);

const call = (tool) => ({ kind: "tool_call", payload: { tool } });
eq("steps before any tool", L.stepsSoFar([]), ["Reading your building details"]);
eq("steps in order, each once", L.stepsSoFar([call("get_building_profile"), call("calculate"), call("calculate"), call("get_utility_rates")]), ["Reading your building details", "Running the numbers", "Looking up Con Edison electricity prices"]);
eq("steps add the closing two when writing", L.stepsSoFar([call("calculate"), call("write_roadmap")]).slice(-2), ["Checking every number has a label and a source", "Writing your plan"]);
eq("tool results are ignored", L.stepsSoFar([{ kind: "tool_result", payload: { tool: "calculate" } }]), ["Reading your building details"]);

(async () => {
  const noWait = async () => {};
  // finishes after one "running" look
  let n = 0;
  script.getLatestRun = async () => (++n < 2 ? { status: "running", events: [] } : { status: "done", output: { plan_summary: {} }, events: [] });
  const run = await L.runLive({}, "q", () => {}, { wait: noWait });
  eq("runLive returns the finished run", run.status, "done");
  // 404 means "not created yet": keep asking
  n = 0;
  script.getLatestRun = async () => { if (++n < 3) throw new ApiError(404, "none"); return { status: "partial", output: {}, events: [] }; };
  eq("runLive waits through 404", (await L.runLive({}, "q", () => {}, { wait: noWait })).status, "partial");
  // needs_input: the question is the message
  script.getLatestRun = async () => ({ status: "needs_input", output: { question: "Which borough?" }, events: [] });
  await L.runLive({}, "q", () => {}, { wait: noWait }).then(() => eq("needs_input throws", true, false), (e) => eq("needs_input throws with the question", [e.kind, e.message], ["needs_input", "Which borough?"]));
  // the daily cap
  script.startRun = async () => { throw new ApiError(429, "Professor Fritts has done as many live analyses as he can for today."); };
  await L.runLive({}, "q", () => {}, { wait: noWait }).then(() => eq("limit throws", true, false), (e) => eq("limit kind and plain message", [e.kind, e.message.startsWith("Professor Fritts has done")], ["limit", true]));
  script.startRun = async () => ({});
  // backend not reachable at all
  script.createSession = async () => { throw new TypeError("Failed to fetch"); };
  await L.runLive({}, "q", () => {}, { wait: noWait }).then(() => eq("unreachable throws", true, false), (e) => eq("unreachable kind", e.kind, "unreachable"));
  script.createSession = async () => ({ id: "s1" });
  // gives up when the connection keeps failing
  script.getLatestRun = async () => { throw new TypeError("Failed to fetch"); };
  await L.runLive({}, "q", () => {}, { wait: noWait }).then(() => eq("lost touch throws", true, false), (e) => eq("lost touch kind", e.kind, "unreachable"));
  // gives up on a run that never ends
  let clock = 0;
  script.getLatestRun = async () => ({ status: "running", events: [] });
  await L.runLive({}, "q", () => {}, { wait: async () => { clock += 10 * 60 * 1000; }, now: () => clock }).then(() => eq("timeout throws", true, false), (e) => eq("timeout kind", e.kind, "timeout"));
  // the bill is uploaded before the run starts, and a failed upload does not stop the run
  const order = [];
  script.uploadDocument = async () => { order.push("upload"); throw new Error("disk full"); };
  script.startRun = async () => { order.push("start"); return {}; };
  script.getLatestRun = async () => ({ status: "done", output: {}, events: [] });
  await L.runLive({}, "q", () => {}, { wait: noWait, bill: { name: "bill.csv" } });
  eq("bill first, run still starts if the upload fails", order, ["upload", "start"]);

  console.log(failed ? `\n${failed} FAILED` : "\nall passed");
  process.exit(failed ? 1 : 0);
})();
