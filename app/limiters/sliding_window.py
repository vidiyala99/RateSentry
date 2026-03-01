import redis.asyncio as aioredis
import time
import uuid

SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])   -- seconds
local limit = tonumber(ARGV[3])
local member = ARGV[4]

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Count current requests in window
local count = redis.call('ZCARD', key)

local allowed = 0
if count < limit then
    redis.call('ZADD', key, now, member)
    allowed = 1
    count = count + 1
end

redis.call('EXPIRE', key, window)
return {allowed, limit - count}
"""


class SlidingWindowLimiter:
    def __init__(self, redis_client: aioredis.Redis, limit: int, window_seconds: int):
        self.redis = redis_client
        self.limit = limit
        self.window = window_seconds
        self._script = self.redis.register_script(SLIDING_WINDOW_SCRIPT)

    async def is_allowed(self, key: str):
        now = time.time()
        member = f"{now}-{uuid.uuid4()}"
        result = await self._script(
            keys=[f"sw:{key}"], args=[now, self.window, self.limit, member]
        )
        allowed, remaining = result
        return bool(allowed), int(remaining), {"member": member}

    async def revert(self, key: str, revert_meta: dict):
        member = revert_meta.get("member")
        if member:
            await self.redis.zrem(f"sw:{key}", member)
