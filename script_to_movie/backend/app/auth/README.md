# Auth Module

## Status: Implemented

Authentication is fully working. You do not need to modify this module.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/me` | GET | Get current authenticated user (returns `null` if not logged in) |
| `/api/auth/register` | POST | Register a new user account |
| `/api/auth/login` | POST | Login with email and password |
| `/api/auth/logout` | POST | Logout (clears session cookie) |

## How It Works

1. **Registration**: Creates a user with a hashed password (bcrypt). Returns a JWT token in a `session` cookie.
2. **Login**: Verifies email/password. Returns a JWT token in a `session` cookie.
3. **Authentication**: The `session` cookie is sent with every request. The `get_current_user` dependency in `app/core/dependencies.py` reads the cookie, decodes the JWT, and loads the user.
4. **Logout**: Deletes the `session` cookie.

## Files

| File | What It Does |
|------|-------------|
| `service.py` | Business logic: `register_user()`, `login_user()`, `get_user_by_id()` |
| `router.py` | FastAPI endpoints that call service functions |

## Using Auth in Your Code

To protect an endpoint (require login):

```python
from fastapi import Depends
from app.core.dependencies import get_current_user
from app.models.user import User

@router.post("/my-endpoint")
async def my_endpoint(user: User = Depends(get_current_user)):
    # user is guaranteed to be logged in
    return {"user_id": user.id}
```

To optionally check if logged in:

```python
from app.core.dependencies import get_current_user_optional

@router.get("/public-endpoint")
async def public_endpoint(user: User | None = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello {user.name}"}
    return {"message": "Hello guest"}
```

## Testing

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@test.com","name":"Dev","password":"password123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@test.com","password":"password123"}'
# Save the session cookie from the response

# Check current user
curl http://localhost:8000/api/auth/me -b "session=YOUR_TOKEN"

# Logout
curl -X POST http://localhost:8000/api/auth/logout -b "session=YOUR_TOKEN"
```
