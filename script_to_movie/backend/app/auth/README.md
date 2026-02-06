# Auth Module

## Role

Handles user authentication and session management for the Script-to-Movie platform.

## Endpoints to Implement

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/me` | GET | Get current authenticated user |
| `/api/auth/register` | POST | Register new user account |
| `/api/auth/login` | POST | Login with email/password |
| `/api/auth/logout` | POST | Logout (clear session cookie) |

## Available Infrastructure

- `app/core/security.py` - JWT token creation/verification, password hashing (bcrypt)
- `app/core/dependencies.py` - `get_current_user`, `get_current_user_optional` dependencies
- `app/models/user.py` - User SQLAlchemy model
- `app/schemas/user.py` - Pydantic schemas (UserCreate, UserLogin, UserResponse)

## Key Decisions

1. **Session Storage**: Currently uses JWT in cookies (1-year expiration). Adjust if needed.
2. **OAuth**: Add OAuth providers (Google, GitHub) if desired.

## Implementation Steps

1. **Implement `service.py`**:
   ```python
   async def register_user(db: AsyncSession, data: UserCreate) -> User
   async def login_user(db: AsyncSession, data: UserLogin) -> User
   async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None
   ```

2. **Implement `router.py`** endpoints:
   - Use `get_password_hash()` and `verify_password()` from `app.core.security`
   - Use `create_access_token()` to generate JWT
   - Set cookie with `response.set_cookie("session", token, httponly=True, ...)`

3. **Test the flow**:
   - Register → Login → Call protected endpoint → Logout

## Reference

See original implementation: `script_to_movie/server/_core/auth.ts`
