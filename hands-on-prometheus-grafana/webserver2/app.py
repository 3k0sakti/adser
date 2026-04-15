"""
WebServer 2 — Flask application with Prometheus metrics.
Endpoints:
  GET /               -> Home page
  GET /health         -> Health check
  GET /api/users      -> Simulated users list API
  GET /api/products   -> Simulated products list API (heavier response)
  GET /slow           -> Simulates a slow response (0.5–3.0s, slower than ws1)
  GET /error          -> Always returns HTTP 500 (for testing error metrics)
  GET /metrics        -> Prometheus metrics endpoint
"""

import time
import random
from flask import Flask, Response, request, jsonify
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST, REGISTRY
)

# ── Server identity ────────────────────────────────────────────────────────────
SERVER_NAME = "webserver2"

app = Flask(__name__)

# ── Prometheus metrics ─────────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["server", "method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["server", "method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently in progress",
    ["server"]
)

# ── Request hooks ─────────────────────────────────────────────────────────────
@app.before_request
def before_request():
    request._start_time = time.time()
    REQUESTS_IN_PROGRESS.labels(server=SERVER_NAME).inc()


@app.after_request
def after_request(response):
    duration = time.time() - request._start_time
    REQUEST_COUNT.labels(
        server=SERVER_NAME,
        method=request.method,
        endpoint=request.path,
        http_status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        server=SERVER_NAME,
        method=request.method,
        endpoint=request.path
    ).observe(duration)
    REQUESTS_IN_PROGRESS.labels(server=SERVER_NAME).dec()
    return response


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return f"""
    <html>
      <body style="font-family:sans-serif; padding:2rem;">
        <h1> {SERVER_NAME}</h1>
        <p>Flask Web Server 2 is running!</p>
        <ul>
          <li><a href="/health">/health</a></li>
          <li><a href="/api/users">/api/users</a></li>
          <li><a href="/api/products">/api/products</a></li>
          <li><a href="/slow">/slow</a></li>
          <li><a href="/error">/error</a> (always 500)</li>
          <li><a href="/metrics">/metrics</a></li>
        </ul>
      </body>
    </html>
    """


@app.route("/health")
def health():
    return jsonify({"status": "ok", "server": SERVER_NAME})


@app.route("/api/users")
def api_users():
    names = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
    users = [{"id": i + 1, "name": names[i], "active": random.choice([True, False])}
             for i in range(5)]
    return jsonify({"server": SERVER_NAME, "users": users})


@app.route("/api/products")
def api_products():
    # Slightly heavier endpoint — simulates more processing
    time.sleep(random.uniform(0.05, 0.2))
    products = [
        {"id": i + 1, "name": f"Product-{i+1}", "price": round(random.uniform(5, 500), 2)}
        for i in range(20)
    ]
    return jsonify({"server": SERVER_NAME, "count": len(products), "products": products})


@app.route("/slow")
def slow():
    # webserver2 is intentionally slower than webserver1
    delay = random.uniform(0.5, 3.0)
    time.sleep(delay)
    return jsonify({"server": SERVER_NAME, "delay_seconds": round(delay, 3)})


@app.route("/error")
def error():
    return jsonify({"server": SERVER_NAME, "error": "Simulated internal error"}), 500


@app.route("/metrics")
def metrics():
    return Response(generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Starting {SERVER_NAME} on port 5000 ...")
    app.run(host="0.0.0.0", port=5000)
