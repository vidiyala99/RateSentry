import redis.asyncio as aioredis
import time

FIXED_WINDOW_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local count = redis.call('INCR', key)
if count == 1 then
    redis.call('EXPIRE', key, window)
end

local allowed = 0
if count <= limit then
    allowed = 1
end

return {allowed, math.max(0, limit - count), redis.call('TTL', key)}
"""


class FixedWindowLimiter:
    def __init__(self, redis_client: aioredis.Redis, limit: int, window_seconds: int):
        self.redis = redis_client
        self.limit = limit
        self.window = window_seconds
        self._script = self.redis.register_script(FIXED_WINDOW_SCRIPT)

    async def is_allowed(self, key: str):
        now = int(time.time())
        window_key = f"fw:{now // self.window}:{key}"
        result = await self._script(keys=[window_key], args=[self.limit, self.window])
        allowed, remaining, ttl = result
        return bool(allowed), int(remaining), int(ttl), {"window_key": window_key}

    async def revert(self, key: str, revert_meta: dict):
        window_key = revert_meta.get("window_key")
        if window_key:
            await self.redis.decr(window_key)
