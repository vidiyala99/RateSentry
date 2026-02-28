# RateSentry — Distributed Rate Limiting & API Gateway

RateSentry is a high-performance, production-grade rate limiting service built with FastAPI and Redis. It provides atomic rate limiting using Lua scripts to ensure consistency across distributed instances.

## Features

- **Distributed State**: Uses Redis for synchronized rate limiting across multiple API nodes.
- **Atomic Operations**: Core limiting logic is implemented in Redis Lua scripts to prevent race conditions.
- **Multiple Algorithms**:
  - **Token Bucket**: For smooth traffic shaping.
  - **Sliding Window Log**: For precise window-based limiting.
  - **Fixed Window**: Simple and fast limiting.
- **Full Observability**: Integrated with Prometheus and Grafana for real-time monitoring.
- **Audit Logging**: Asynchronous audit logging of policy changes to PostgreSQL.
- **Production Ready**: Full Docker Compose setup for easy deployment.

## Architecture

- **FastAPI**: Main service framework.
- **Redis**: Distributed store for rate limit counters.
- **PostgreSQL**: Audit log storage.
- **Prometheus**: Metrics collection.
- **Grafana**: Visualization dashboard.

## Quick Start

1. **Start the stack**:
   ```bash
   docker-compose up -d
   ```
2. **Test the API**:
   ```bash
   curl http://localhost:8000/api/hello -H "X-API-Key: my-secret-key"
   ```

## Load Testing

RateSentry is designed for high throughput. You can run the included Locust scripts:

```bash
locust -f scripts/locustfile.py --host=http://localhost:8000 --users 500 --spawn-rate 50 --run-time 60s --headless
```

## Monitoring

- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Grafana**: [http://localhost:3000](http://localhost:3000) (Default login: `admin/admin`)
- **Metrics Endpoint**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
