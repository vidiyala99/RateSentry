from prometheus_client import Counter, Histogram, Gauge

REQUESTS_ALLOWED = Counter(
    "ratelimit_requests_allowed_total",
    "Total allowed requests",
    ["policy"]
)

REQUESTS_DENIED = Counter(
    "ratelimit_requests_denied_total",
    "Total denied requests (429s)",
    ["policy"]
)

REQUEST_LATENCY = Histogram(
    "ratelimit_middleware_latency_seconds",
    "Time spent in rate limit middleware",
    ["method", "path"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
)

BUCKET_FILL_LEVEL = Gauge(
    "ratelimit_token_bucket_fill_level",
    "Current token count per key",
    ["key"]
)
