#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
BATCH_ID="${BATCH_ID:-test-batch-$(date +%s)}"
PLANT_ID="${PLANT_ID:-test-plant-001}"

echo "Validating THC flow against: ${BASE_URL}"
echo "Batch: ${BATCH_ID} | Plant: ${PLANT_ID}"

SPECTRUM="$(python -c "import json,random; print(json.dumps([round(random.random(),6) for _ in range(157)]))")"

ESTIMATE_PAYLOAD="$(python -c "import json,sys; batch=sys.argv[1]; plant=sys.argv[2]; spectrum=json.loads(sys.argv[3]); print(json.dumps({'batch_id':batch,'plant_id':plant,'zone_id':'default','spectrum':spectrum}))" "${BATCH_ID}" "${PLANT_ID}" "${SPECTRUM}")"
ESTIMATE_RESPONSE="$(curl -sS -X POST "${BASE_URL}/thc/estimate" -H "Content-Type: application/json" -d "${ESTIMATE_PAYLOAD}")"

echo "Estimate response:"
echo "${ESTIMATE_RESPONSE}"

STATUS_EST="$(python -c "import json,sys; data=json.loads(sys.argv[1]); print(data.get('data',{}).get('status',''))" "${ESTIMATE_RESPONSE}")"
if [ "${STATUS_EST}" != "PENDING_VALIDATION" ]; then
  echo "ERROR: expected PENDING_VALIDATION, got ${STATUS_EST}"
  exit 1
fi

VALIDATE_PAYLOAD="$(python -c "import json,sys; batch=sys.argv[1]; print(json.dumps({'batch_id':batch,'lab_certificate':'LIMS-ABC123','thc_validated':18.5,'validation_method':'HPLC'}))" "${BATCH_ID}")"
VALIDATE_RESPONSE="$(curl -sS -X POST "${BASE_URL}/thc/validate_lims" -H "Content-Type: application/json" -d "${VALIDATE_PAYLOAD}")"

echo "Validate response:"
echo "${VALIDATE_RESPONSE}"

STATUS_VAL="$(python -c "import json,sys; data=json.loads(sys.argv[1]); print(data.get('data',{}).get('status',''))" "${VALIDATE_RESPONSE}")"
if [ "${STATUS_VAL}" != "VALIDATED_BY_LIMS" ]; then
  echo "ERROR: expected VALIDATED_BY_LIMS, got ${STATUS_VAL}"
  exit 1
fi

echo "THC flow validated successfully."
