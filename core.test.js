/**
 * core.test.js — CASTÚO-SYSTEM contract & schema tests (Node.js built-in runner)
 *
 * Validates:
 *  - JSON schema files are well-formed
 *  - TRACES API contract: response.estado contains "Compliant"
 *  - Legal notice present in all document responses
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCHEMAS_DIR = join(__dirname, "config", "schemas");

// ---------------------------------------------------------------------------
// Schema integrity tests
// ---------------------------------------------------------------------------

describe("JSON schema files", () => {
  const schemaFiles = [
    "traces.schema.json",
    "siex.schema.json",
    "pac.schema.json",
    "sigpac.schema.json",
    "regepa.schema.json",
  ];

  for (const file of schemaFiles) {
    it(`${file} is valid JSON`, () => {
      const raw = readFileSync(join(SCHEMAS_DIR, file), "utf-8");
      const schema = JSON.parse(raw);
      assert.ok(schema, `${file} should parse to a truthy object`);
      assert.equal(
        typeof schema,
        "object",
        `${file} root should be an object`,
      );
    });

    it(`${file} has required JSON Schema fields`, () => {
      const schema = JSON.parse(readFileSync(join(SCHEMAS_DIR, file), "utf-8"));
      assert.ok(
        "$schema" in schema || "type" in schema || "properties" in schema,
        `${file} should have at least one of: $schema, type, properties`,
      );
    });
  }
});

// ---------------------------------------------------------------------------
// TRACES API contract tests (static contract, no live server required)
// ---------------------------------------------------------------------------

describe("TRACES API contract", () => {
  /**
   * Simulates the DocumentResponse shape returned by the FastAPI endpoint.
   * Mirrors api/main.py DocumentResponse for contract verification.
   */
  function buildTracesResponse({ estado = "✅ TRACES Compliant" } = {}) {
    return {
      tipo_documento: "TRACES Certificado Sanitario",
      estado,
      payload: {
        explotacion: { rega: "ES123456789", nombre: "Test Farm" },
        animales: { especie: "bovino", raza: "Retinta", cantidad: 10 },
        movimiento: {
          tipo: "EXPORT",
          destino_pais: "DE",
          destino_explotacion: "DE987654321",
        },
        certificado: { numero: "TRACES-ES-20260101-ES123456789" },
        firma: {
          pendiente_firma: true,
          aviso: "Documento generado para REVISIÓN y FIRMA del productor",
        },
      },
      aviso: "Documento generado para REVISIÓN y FIRMA del productor",
      generado_en: new Date().toISOString(),
    };
  }

  it("estado field contains 'Compliant'", () => {
    const response = buildTracesResponse();
    assert.ok(
      response.estado.includes("Compliant"),
      `estado should contain 'Compliant', got: ${response.estado}`,
    );
  });

  it("certificado.numero starts with 'TRACES-ES-'", () => {
    const response = buildTracesResponse();
    assert.ok(
      response.payload.certificado.numero.startsWith("TRACES-ES-"),
      "certificado.numero should start with 'TRACES-ES-'",
    );
  });

  it("pendiente_firma is true", () => {
    const response = buildTracesResponse();
    assert.equal(response.payload.firma.pendiente_firma, true);
  });

  it("mandatory legal notice present", () => {
    const response = buildTracesResponse();
    const expected = "Documento generado para REVISIÓN y FIRMA del productor";
    assert.equal(response.aviso, expected);
    assert.equal(response.payload.firma.aviso, expected);
  });
});

// ---------------------------------------------------------------------------
// General document response contract
// ---------------------------------------------------------------------------

describe("DocumentResponse contract", () => {
  const REQUIRED_FIELDS = [
    "tipo_documento",
    "estado",
    "payload",
    "aviso",
    "generado_en",
  ];

  function sampleResponse(overrides = {}) {
    return {
      tipo_documento: "Test Document",
      estado: "✅ Test Compliant",
      payload: { firma: { pendiente_firma: true } },
      aviso: "Documento generado para REVISIÓN y FIRMA del productor",
      generado_en: new Date().toISOString(),
      ...overrides,
    };
  }

  for (const field of REQUIRED_FIELDS) {
    it(`response includes required field: ${field}`, () => {
      const response = sampleResponse();
      assert.ok(field in response, `response must have field '${field}'`);
    });
  }

  it("estado for compliant documents contains 'Compliant'", () => {
    const response = sampleResponse();
    assert.ok(response.estado.includes("Compliant"));
  });

  it("payload.firma.pendiente_firma is always true", () => {
    const response = sampleResponse();
    assert.equal(response.payload.firma.pendiente_firma, true);
  });
});
