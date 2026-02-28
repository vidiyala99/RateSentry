from pydantic import BaseModel
from enum import Enum

class Algorithm(str, Enum):
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"

class ScopeType(str, Enum):
    USER = "user"
    IP = "ip"
    API_KEY = "api_key"

class RateLimitPolicy(BaseModel):
    name: str
    algorithm: Algorithm
    limit: int
    window_seconds: int = 60
    capacity: int = 100           # token bucket only
    refill_rate: float = 1.0      # token bucket only
    scope: ScopeType = ScopeType.IP
    paths: list[str] = ["*"]      # which routes this policy applies to

# Default policies — swap these for DB-loaded configs later
DEFAULT_POLICIES = [
    RateLimitPolicy(
        name="api_key_token_bucket",
        algorithm=Algorithm.TOKEN_BUCKET,
        capacity=20,
        refill_rate=1.0,
        limit=20,
        scope=ScopeType.API_KEY,
        paths=["/api/*"]
    ),
    RateLimitPolicy(
        name="global_ip_limit",
        algorithm=Algorithm.SLIDING_WINDOW,
        limit=100,
        window_seconds=60,
        scope=ScopeType.IP,
        paths=["*"]
    ),
]
