# System Module

## Status: Implemented

The health check endpoint is working.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/system/health` | GET | Returns `{"status": "ok"}` |

## Usage

Use this to verify the backend is running:

```bash
curl http://localhost:8000/api/system/health
# Returns: {"status": "ok"}
```
