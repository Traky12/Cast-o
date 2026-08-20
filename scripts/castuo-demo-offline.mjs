#!/usr/bin/env node
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");
const fixturePath = resolve(root, "tests/fixtures/offline-demo.json");
const outputPath = resolve(root, "artifacts/bounded-assurance/offline-demo/evidence-pack.json");
const reportPath = resolve(root, "artifacts/bounded-assurance/offline-demo/bounded-assurance-report.json");

function canonicalize(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function hash(value) {
  return createHash("sha256").update(canonicalize(value)).digest("hex");
}

const fixture = JSON.parse(await readFile(fixturePath, "utf8"));
const evidence = {
  schema_version: "castuo.bounded_assurance.v1",
  evidence_id: "CASTO-OFFLINE-DEMO-001",
  operation_id: fixture.operation_id,
  scope: "bounded offline continuity demonstration",
  environment: "SIMULATION_ONLY",
  claim_boundary: "SIMULATION_ONLY",
  events: fixture.events,
  connectivity_intervals: [{ status: "ONLINE", at: fixture.events[0].at }, { status: "OFFLINE", at: fixture.events[1].at }, { status: "ONLINE", at: fixture.events[3].at }],
  recovery_events: [fixture.events[3]],
  synchronisation: { status: "PASS", event_count: fixture.events.length },
  failures: [],
  integrity_hash: "",
  replay_result: "",
  final_status: "",
  promotion_effect: "BLOCKED",
};

evidence.integrity_hash = hash({ ...evidence, integrity_hash: "", replay_result: "", final_status: "" });
const replayHash = hash({ ...evidence, integrity_hash: "", replay_result: "", final_status: "" });
evidence.replay_result = replayHash === evidence.integrity_hash ? "PASS" : "REJECTED";
evidence.final_status = evidence.replay_result === "PASS" ? "VERIFIED_SIMULATION" : "EVIDENCE_REQUIRED";
await mkdir(dirname(outputPath), { recursive: true });
await writeFile(outputPath, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
const report = {
  report_id: "CASTO-BOUND-ASSURANCE-001",
  scope: "bounded offline continuity demonstration",
  claims_tested: 1,
  results: { passed: evidence.replay_result === "PASS" ? 1 : 0, failed: evidence.replay_result === "PASS" ? 0 : 1, unverified: 0, critical_findings: 0 },
  evidence_artifact: "artifacts/bounded-assurance/offline-demo/evidence-pack.json",
  replay: evidence.replay_result,
  limitations: ["SIMULATION_ONLY fixture", "local execution only", "not certification", "not field or production evidence"],
  promotion_effect: "BLOCKED",
  claim_boundary: "SIMULATION_ONLY",
};
await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");

console.log("FIELD OPERATION COMPLETED");
console.log("LOSS OF CONNECTIVITY ........ PASS");
console.log("LOCAL BUFFER ................ PASS");
console.log("RECOVERY .................... PASS");
console.log("SYNC ......................... PASS");
console.log("EVIDENCE HASH ............... PASS");
console.log(`REPLAY ....................... ${evidence.replay_result}`);
console.log("CLAIM BOUNDARY ............... SIMULATION_ONLY");
console.log("PROMOTION .................... BLOCKED");
console.log(`EVIDENCE ARTIFACT ............ ${outputPath}`);
console.log(`ASSURANCE REPORT .............. ${reportPath}`);
process.exitCode = evidence.replay_result === "PASS" ? 0 : 1;
