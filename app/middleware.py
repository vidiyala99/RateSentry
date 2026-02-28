from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.limiters.token_bucket import TokenBucketLimiter
from app.limiters.sliding_window import SlidingWindowLimiter
from app.metrics import REQUESTS_ALLOWED, REQUESTS_DENIED, REQUEST_LATENCY
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, policies):
        super().__init__(app)
        self.policies = policies
        self.limiters = {}
        self._initialized = False

    def _lazy_init(self, redis_client):
        if self._initialized:
            return
        for policy in self.policies:
            if policy.algorithm.value == "token_bucket":
                self.limiters[policy.name] = TokenBucketLimiter(
                    redis_client, policy.capacity, policy.refill_rate
                )
            elif policy.algorithm.value == "sliding_window":
                self.limiters[policy.name] = SlidingWindowLimiter(
                    redis_client, policy.limit, policy.window_seconds
                )
        self._initialized = True

    def _extract_scope_key(self, request: Request, scope_type: str) -> str:
        if scope_type == "ip":
            return request.client.host or "127.0.0.1"
        if scope_type == "api_key":
            # Direct access for speed, case-insensitive via Starlette Headers
            return request.headers.get("x-api-key") or "anonymous"
        if scope_type == "user":
            auth = request.headers.get("authorization", "")
            if auth.lower().startswith("bearer "):
                try:
                    from jose import jwt
                    payload = jwt.decode(auth[7:], options={"verify_signature": False})
                    return str(payload.get("sub", "anonymous"))
                except Exception:
                    pass
        return request.client.host or "127.0.0.1"

    async def dispatch(self, request: Request, call_next):
        self._lazy_init(request.app.state.redis)
        path = request.url.path
        start = time.perf_counter()

        for policy in self.policies:
            # Optimized path matching: prefix match for wildcards
            if policy.paths != ["*"]:
                match = False
                for p in policy.paths:
                    if p.endswith("*"):
                        if path.startswith(p[:-1]):
                            match = True
                            break
                    elif path == p:
                        match = True
                        break
                if not match:
                    continue
            
            limiter = self.limiters.get(policy.name)
            if not limiter:
                continue

            scope_key = self._extract_scope_key(request, policy.scope.value)
            identifier = f"{policy.name}:{scope_key}"

            result = await limiter.is_allowed(identifier)
            allowed = result[0]
            remaining = result[1]

            if not allowed:
                REQUESTS_DENIED.labels(policy=policy.name).inc()
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "policy": policy.name},
                    headers={
                        "X-RateLimit-Limit": str(policy.limit),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(result[2] if len(result) > 2 else 60),
                    }
                )

            REQUESTS_ALLOWED.labels(policy=policy.name).inc()

        response = await call_next(request)
        latency = time.perf_counter() - start
        REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(latency)
        return response
