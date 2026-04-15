#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# generate-traffic.sh  —  Send manual bursts of HTTP traffic to both web servers
#
# Usage:
#   chmod +x generate-traffic.sh
#   ./generate-traffic.sh [requests_per_endpoint]
#
# Example:
#   ./generate-traffic.sh 20      # Send 20 requests per endpoint
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

N=${1:-10}   # Number of requests per endpoint (default 10)

WS1="http://localhost:5001"
WS2="http://localhost:5002"

echo "======================================================="
echo "  Traffic Generator — Web Server Monitoring Lab"
echo "======================================================="
echo "  Sending ${N} requests to each endpoint ..."
echo ""

send_requests() {
  local label=$1
  local url=$2
  local count=$3
  printf "  %-40s" "$label"
  for _ in $(seq 1 "$count"); do
    curl -sf "$url" -o /dev/null || true
    printf "."
  done
  echo " done"
}

echo "--- WebServer 1 (http://localhost:5001) ---"
send_requests "GET /"          "$WS1/"           "$N"
send_requests "GET /health"    "$WS1/health"     "$N"
send_requests "GET /api/data"  "$WS1/api/data"   "$N"
send_requests "GET /slow"      "$WS1/slow"       "3"
send_requests "GET /error"     "$WS1/error"      "5"
echo ""

echo "--- WebServer 2 (http://localhost:5002) ---"
send_requests "GET /"              "$WS2/"               "$N"
send_requests "GET /health"        "$WS2/health"         "$N"
send_requests "GET /api/users"     "$WS2/api/users"      "$N"
send_requests "GET /api/products"  "$WS2/api/products"   "$N"
send_requests "GET /slow"          "$WS2/slow"           "3"
send_requests "GET /error"         "$WS2/error"          "5"
echo ""

echo "======================================================="
echo "  Done! Open Grafana at http://localhost:3000"
echo "  (admin / admin123)"
echo "======================================================="
