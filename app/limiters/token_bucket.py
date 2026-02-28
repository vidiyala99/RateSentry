import redis.asyncio as aioredis
import time

# Lua script: atomic read-modify-write
# Returns [allowed (0/1), remaining_tokens, reset_time]
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])   -- tokens per second
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

-- Refill tokens based on elapsed time
local elapsed = math.max(0, now - last_refill)
tokens = math.min(capacity, tokens + elapsed * refill_rate)

local allowed = 0
if tokens >= requested then
    tokens = tokens - requested
    allowed = 1
end

redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', key, 3600)

return {allowed, math.floor(tokens), math.floor(1 / refill_rate)}
"""

class TokenBucketLimiter:
    def __init__(self, redis_client: aioredis.Redis, capacity: int, refill_rate: float):
        self.redis = redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._script = self.redis.register_script(TOKEN_BUCKET_SCRIPT)

    async def is_allowed(self, key: str) -> tuple[bool, int, int]:
        now = time.time()
        result = await self._script(
            keys=[f"tb:{key}"],
            args=[self.capacity, self.refill_rate, now, 1]
        )
        allowed, remaining, retry_after = result
        return bool(allowed), int(remaining), int(retry_after)
