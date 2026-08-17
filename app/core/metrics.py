from prometheus_client import make_asgi_app, Counter, Histogram

# Create a metric to track time spent and requests made.
REQUEST_TIME = Histogram(
    "request_processing_seconds",
    "Time spent processing request",
    ["method", "endpoint"],
)
REQUEST_COUNT = Counter(
    "request_count", "Total number of requests", ["method", "endpoint", "http_status"]
)

# Create an ASGI app to serve the metrics
metrics_app = make_asgi_app()
