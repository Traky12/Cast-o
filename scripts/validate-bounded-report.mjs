#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
const root = resolve(new URL("..", import.meta.url).pathname);
const report = JSON.parse(await readFile(resolve(root, "artifacts/bounded-assurance/offline-demo/bounded-assurance-report.json"), "utf8"));
const required = ["report_id", "scope", "claims_tested", "results", "evidence_artifact", "replay", "limitations", "promotion_effect", "claim_boundary"];
const missing = required.filter((key) => !(key in report));
const valid = missing.length === 0 && report.replay === "PASS" && report.promotion_effect === "BLOCKED" && report.claim_boundary === "SIMULATION_ONLY" && report.results.critical_findings === 0 && report.limitations.length > 0;
const result = { audit_id: "CASTO-BOUND-ASSURANCE-REPORT-2026-08-20", status: valid ? "PASS_LOCAL" : "FAIL_LOCAL", missing, report_id: report.report_id, replay: report.replay, promotion_effect: report.promotion_effect, claim_boundary: report.claim_boundary, limitations: report.limitations };
console.log(JSON.stringify(result, null, 2));
process.exitCode = valid ? 0 : 1;
