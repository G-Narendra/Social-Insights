#!/usr/bin/env bash
# ==============================================================================
# End-to-End System Smoke Test
# Validates API endpoints, live collection, background worker, ML, and frontend.
# ==============================================================================
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3000}"
KEYWORD="${1:-Toyota}"

echo "======================================================================"
echo " Starting Social Insights End-to-End Smoke Test"
echo " Backend:  $BACKEND_URL"
echo " Frontend: $FRONTEND_URL"
echo " Target:   $KEYWORD"
echo "======================================================================"

# 1. Backend Health Check
echo -n "[1/7] Testing Backend /health ... "
curl -sf "$BACKEND_URL/health" > /dev/null
echo "OK"

# 2. Database Readiness Check
echo -n "[2/7] Testing Backend /ready (DB connectivity) ... "
curl -sf "$BACKEND_URL/ready" > /dev/null
echo "OK"

# 3. Trigger Mention Collection
echo "[3/7] Triggering Collection for '$KEYWORD' ... "
TRIGGER_RESP=$(curl -sf -X POST "$BACKEND_URL/api/collect" \
  -H "Content-Type: application/json" \
  -d "{\"keyword\": \"$KEYWORD\", \"limit\": 20}")
RUN_ID=$(echo "$TRIGGER_RESP" | grep -o '"run_id":[0-9]*' | cut -d: -f2)
echo "  Run ID $RUN_ID queued."

# 4. Poll Run until Completion
echo -n "[4/7] Polling collection run status "
MAX_POLLS=30
STATUS="queued"
for i in $(seq 1 $MAX_POLLS); do
  sleep 2
  echo -n "."
  RUN_RESP=$(curl -sf "$BACKEND_URL/api/runs/$RUN_ID")
  STATUS=$(echo "$RUN_RESP" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
  if [[ "$STATUS" == "succeeded" || "$STATUS" == "failed" ]]; then
    break
  fi
done
echo ""
if [[ "$STATUS" != "succeeded" ]]; then
  echo "ERROR: Collection run ended with status '$STATUS'"
  echo "$RUN_RESP"
  exit 1
fi
echo "  Collection and AI processing completed successfully."

# 5. Query Mentions and Stats
echo -n "[5/7] Verifying /api/mentions and /api/stats/overview ... "
curl -sf "$BACKEND_URL/api/mentions?keyword=$KEYWORD&limit=5" > /dev/null
STATS_RESP=$(curl -sf "$BACKEND_URL/api/stats/overview?keyword=$KEYWORD")
echo "$STATS_RESP" | grep -q "total_mentions"
echo "OK"

# 6. Query AI Intelligence Summary
echo -n "[6/7] Verifying /api/insights/summary ... "
SUMMARY_RESP=$(curl -sf "$BACKEND_URL/api/insights/summary?keyword=$KEYWORD")
echo "$SUMMARY_RESP" | grep -q "content"
echo "OK"

# 7. Frontend Check (if reachable)
echo -n "[7/7] Checking Frontend Web Dashboard ... "
if curl -sf --max-time 3 "$FRONTEND_URL" > /dev/null 2>&1; then
  echo "OK"
else
  echo "SKIPPED (frontend server not running on $FRONTEND_URL)"
fi

echo "======================================================================"
echo " ALL SMOKE TESTS COMPLETED SUCCESSFULLY!"
echo "======================================================================"
