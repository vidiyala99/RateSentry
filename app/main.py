from fastapi import FastAPI
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from prometheus_client import make_asgi_app
from app.middleware import RateLimitMiddleware
from app.policy import DEFAULT_POLICIES
from app.database import init_db, log_policy_load
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if os.getenv("MOCK_SERVICES") == "1":
        from fakeredis import aioredis as fake_aioredis

        app.state.redis = fake_aioredis.FakeRedis(decode_responses=True)
    else:
        app.state.redis = aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            encoding="utf-8",
            decode_responses=True,
        )
    await init_db()
    await log_policy_load(DEFAULT_POLICIES)
    yield
    # Shutdown
    await app.state.redis.aclose()


app = FastAPI(title="RateSentry", lifespan=lifespan)

# Wire up middleware
app.add_middleware(RateLimitMiddleware, policies=DEFAULT_POLICIES)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Demo routes to test against
@app.get("/api/hello")
async def hello():
    return {"message": "Hello — you made it past the rate limiter"}


@app.get("/api/data")
async def data():
    return {"data": list(range(100))}


@app.get("/health")
async def health():
    return {"status": "ok"}
