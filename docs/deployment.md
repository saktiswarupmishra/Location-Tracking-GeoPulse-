# GeoPulse Production Deployment Guide

## 1. Prerequisites
- Docker & Docker Compose
- MongoDB 7.0+ Replica Set (Required for transactions)
- Redis 7.0+ (Standalone or Cluster)
- Twilio Account (for production SMS OTP)

---

## 2. Environment Configuration

Copy `.env.example` to `.env` and fill in production secrets:

```bash
APP_ENV=production
JWT_SECRET=<generate_random_64_char_secret>
MONGODB_URI=mongodb://mongo1:27017,mongo2:27017/?replicaSet=rs0
REDIS_URL=redis://:strong_redis_password@redis:6379/0
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
TWILIO_VERIFY_SERVICE_SID=VAzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
OTP_DEV_MODE=false
```

---

## 3. Running with Docker Compose

```bash
# Build and run the entire hardened stack
docker-compose up -d --build
```

---

## 4. Health & Monitoring

Check API health with component-level latency and connection counts:

```bash
curl http://localhost:8000/health
```

Sample Response:
```json
{
  "status": "healthy",
  "version": "1.1.0",
  "components": {
    "mongodb": { "status": "connected", "latency_ms": 1.4 },
    "redis": { "status": "connected", "latency_ms": 0.8 },
    "websocket": { "active_connections": 142, "active_users": 110 }
  }
}
```
