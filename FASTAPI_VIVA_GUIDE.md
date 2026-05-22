# FastAPI Architecture & Viva Guide — FundooNotes Project

## Table of Contents
1. [Foundational Concepts](#foundational-concepts)
2. [Project Architecture](#project-architecture)
3. [Request/Response Flow](#requestresponse-flow)
4. [Component Breakdown](#component-breakdown)
5. [Sync vs Async](#sync-vs-async)
6. [Integration Points](#integration-points)
7. [Viva Q&A](#viva-qa)
8. [Demo Checklist](#demo-checklist)
9. [Key Takeaways](#key-takeaways)

---

## Foundational Concepts

### What is FastAPI?

FastAPI is a modern Python web framework built on:
- **Starlette** (ASGI web framework for async HTTP)
- **Pydantic** (data validation & serialization)
- **OpenAPI/Swagger** (automatic API documentation)

### Key Features

| Feature | Benefit |
|---------|---------|
| Type hints | Auto docs + validation |
| Async-first | Handles many concurrent requests efficiently |
| Sync-compatible | Works with blocking code (Django ORM, Celery) |
| Dependency injection | Clean, testable code structure |
| Auto validation | Pydantic validates requests before handlers |
| Built-in docs | Swagger UI auto-generated at `/docs` |

### Why FastAPI + Django?

In your project:
- **Django** handles: core models, admin panel, database migrations, ORM
- **FastAPI** handles: lightweight collaborator endpoints, modern API design, future async support

**Trade-off:**
- DRF (Django REST Framework) is heavy and model-driven
- FastAPI is lightweight and handler-driven, better for custom logic

---

## Project Architecture

### High-Level Diagram

```
┌───────────────────────────────────────────────────────┐
│              Client (React Frontend)                  │
└───────────────────────────┬───────────────────────────┘
                            │ HTTP/JSON
                            ↓
┌───────────────────────────────────────────────────────┐
│         ASGI Entry: FundooMain/asgi.py                │
│            (Starlette Router/Multiplexer)             │
├─────────────────┬─────────────────────────────────────┤
│  Path: /fastapi │  Path: /                            │
│  ↓              │  ↓                                  │
│ FastAPI App     │  Django ASGI App                    │
├─────────────────┼─────────────────────────────────────┤
│ Routers:        │  URL Routes:                        │
│ • auth          │  • /api/notes/                      │
│ • collaborators │  • /api/auth/                       │
│                 │  • /admin/                          │
├─────────────────┼─────────────────────────────────────┤
│ Shared Resources (both access):                       │
│ • Django ORM (Note, NoteCollaborator, User)           │
│ • PostgreSQL/SQLite Database                          │
│ • Redis Cache                                         │
│ • Celery Tasks                                        │
│ • JWT Tokens                                          │
│ • Django settings                                     │
└─────────────────┴─────────────────────────────────────┘
```

### File Structure

```
backend/
├── FundooMain/
│   ├── asgi.py                ← Entry point: mounts Django + FastAPI
│   ├── fastapi.py             ← FastAPI instance importer
│   ├── settings.py            ← Django settings
│   └── ...
├── fastapi_app/
│   ├── app.py                 ← FastAPI app init; includes routers
│   ├── utils/
│   │   └── auth.py            ← JWT decode, token validation
│   ├── routers/
│   │   ├── auth.py            ← Login endpoint
│   │   └── collaborators.py   ← Collaborator CRUD endpoints
│   └── schemas/
│       ├── auth.py            ← Pydantic models for auth
│       ├── collaborators.py   ← Pydantic models for collaborators
│       └── common.py          ← ApiResponseSchema (envelope)
├── notes/
│   ├── models.py              ← Django models (Note, NoteCollaborator)
│   └── api_views.py           ← Django REST Framework views
├── users/
│   ├── models.py              ← Django User model
│   ├── token_utils.py         ← JWT generation
│   └── tasks.py               ← Celery tasks (email)
└── common/
    └── api_response.py        ← Shared envelope builder
```

### How Django and FastAPI Connect

**File: `backend/FundooMain/asgi.py`**

```python
import os
import django
from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.routing import Mount

# Initialize Django FIRST
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FundooMain.settings")
django.setup()

# Import FastAPI app AFTER Django is ready
from FundooMain.fastapi import app as fastapi_app

django_asgi_app = get_asgi_application()

# Single ASGI application that routes to both
application = Starlette(
    routes=[
        Mount("/fastapi", app=fastapi_app),    # /fastapi/* → FastAPI
        Mount("/", app=django_asgi_app),        # /* → Django
    ]
)
```

**Key point:** Django is initialized first, then FastAPI is imported. This allows FastAPI to access Django ORM, models, and settings.

---

## Request/Response Flow

### Example 1: POST /fastapi/login/

**Step-by-step:**

```
1. Client sends:
   POST http://localhost:8002/fastapi/login/
   Body: {"email": "user@example.com", "password": "secret"}

2. Starlette router (in asgi.py):
   → matches /fastapi/* pattern
   → routes to FastAPI app

3. FastAPI route handler:
   @router.post("/login/", response_model=ApiResponseSchema)
   def login(credentials: LoginSchema):

4. Pydantic validation:
   class LoginSchema(BaseModel):
       email: EmailStr      ← must be valid email
       password: str        ← must be string
   
   If invalid → 422 Unprocessable Entity
   If valid → pass Python object to handler

5. Handler executes (SYNCHRONOUS Django ORM):
   user = User.objects.filter(email=email).first()
   if not check_password(password, user.password):
       raise HTTPException(status_code=401, detail="Invalid credentials")

6. Generate tokens:
   tokens = generate_tokens(user.id)  # from users.token_utils
   → creates access_token, refresh_token using SECRET_KEY

7. Build response envelope:
   return build_api_response(
       message="Login successful",
       payload=TokenResponseSchema(...).dict(),
       status_code=200
   )

8. Response JSON:
   {
     "message": "Login successful",
     "payload": {
       "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
       "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
       "token_type": "bearer",
       "user_id": 5,
       "user_email": "user@example.com",
       "user_name": "John"
     },
     "status code": 200
   }

9. Starlette sends HTTP 200 to client
10. Frontend stores access_token in localStorage
11. Future requests use: Authorization: Bearer eyJ...
```

### Example 2: GET /fastapi/notes/{note_id}/collaborators/

**Step-by-step:**

```
1. Frontend sends:
   GET http://localhost:8002/fastapi/notes/123/collaborators/
   Header: Authorization: Bearer eyJ...

2. Starlette routes to FastAPI

3. FastAPI dependency injection:
   @router.get(..., token: str = Depends(_verify_credentials))
   
   _verify_credentials extracts Authorization header
   → calls verify_auth_header(token)
   → returns User object OR raises HTTPException(401)

4. Handler receives injected user:
   def list_collaborators(note_id: int, token: str = Depends(...)):
       user = verify_auth_header(token)  # Dependency injected
       note = _get_owned_note(note_id, user)
       collaborations = NoteCollaborator.objects.filter(note=note)

5. Serialize to Pydantic:
   payload = [
       CollaboratorSchema(
           name=collab.user.name,
           access_level=collab.access_level
       ) for collab in collaborations
   ]

6. Return envelope:
   return build_api_response(
       "Collaborators fetched",
       [item.dict() for item in payload],
       200
   )

7. Response:
   {
     "message": "Collaborators fetched",
     "payload": [
       {"name": "Alice", "access_level": "edit"},
       {"name": "Bob", "access_level": "view"}
     ],
     "status code": 200
   }
```

---

## Component Breakdown

### A. Pydantic Schemas (`backend/fastapi_app/schemas/`)

**Purpose:**
- Define request/response shapes
- Auto-validate incoming JSON
- Auto-generate OpenAPI documentation
- Serialize Python objects to JSON

**Example from `schemas/auth.py`:**

```python
from pydantic import BaseModel, EmailStr

class LoginSchema(BaseModel):
    """Request shape for login endpoint"""
    email: EmailStr              # Pydantic validates email format
    password: str                # Must be string

class TokenResponseSchema(BaseModel):
    """Response shape after successful login"""
    access_token: str
    refresh_token: str
    token_type: str              # e.g., "bearer"
    user_id: int
    user_email: str
    user_name: str
```

**Validation in action:**

```
Valid input:
{"email": "user@example.com", "password": "secret123"}
→ Passes validation, handler receives LoginSchema object

Invalid input:
{"email": "not-an-email", "password": "secret"}
→ 422 Unprocessable Entity error
   {
     "detail": [
       {
         "loc": ["body", "email"],
         "msg": "invalid email format",
         "type": "value_error.email"
       }
     ]
   }
```

### B. Routers (`backend/fastapi_app/routers/`)

#### `auth.py` — Authentication

```python
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/fastapi", tags=["auth"])

@router.post("/login/", response_model=ApiResponseSchema)
def login(credentials: LoginSchema):
    """Authenticate user and return JWT tokens"""
    email = credentials.email
    password = credentials.password
    
    user = User.objects.filter(email=email).first()
    if not user or not check_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    tokens = generate_tokens(user.id)
    payload = TokenResponseSchema(...).dict()
    return build_api_response("Login successful", payload, 200)
```

#### `collaborators.py` — Collaborator CRUD

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/fastapi/notes/{note_id}/collaborators/` | GET | List all collaborators |
| `/fastapi/notes/{note_id}/collaborators/` | POST | Add collaborator (send invite) |
| `/fastapi/notes/{note_id}/collaborators/{user_id}/` | PATCH | Update access level |
| `/fastapi/notes/{note_id}/collaborators/{user_id}/` | DELETE | Remove collaborator |
| `/fastapi/invitations/` | GET | List pending invitations |
| `/fastapi/invitations/` | POST | Accept/decline invitation |

### C. Auth Utils (`backend/fastapi_app/utils/auth.py`)

**Functions:**

```python
def get_bearer_token(auth_header: str) -> Optional[str]:
    """Extract token from 'Bearer XXX' format"""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()

def decode_token(token: str) -> dict:
    """Decode JWT using Django's SECRET_KEY"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_user_from_token(token: str) -> User:
    """Get User from token payload"""
    payload = decode_token(token)
    if payload.get("token_type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("user_id")
    user = User.objects.filter(pk=user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def verify_auth_header(authorization: str) -> User:
    """Full verification pipeline"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = get_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return get_user_from_token(token)
```

**Key detail:** Uses Django's `SECRET_KEY` so tokens are compatible between Django and FastAPI.

### D. Response Envelope (`backend/common/api_response.py`)

**Shared by both Django and FastAPI:**

```python
def build_api_response(message: str, payload: Any, status_code: int) -> dict[str, Any]:
    """Create canonical response envelope"""
    return {
        "message": message,         # e.g., "Notes fetched"
        "payload": payload,         # Actual data (list, dict, etc.)
        "status code": status_code  # e.g., 200
    }
```

**Result:** Frontend always sees the same response shape regardless of which backend handled the request.

---

## Sync vs Async

### Current: Synchronous Handlers

```python
@router.get("/notes/{note_id}/collaborators/")
def list_collaborators(note_id: int, token: str = Depends(_verify_credentials)):
    # All blocking calls (no async)
    user = verify_auth_header(token)  # JWT decode (CPU-bound, fast)
    note = _get_owned_note(note_id, user)  # DB query (I/O-bound, BLOCKS)
    collaborations = NoteCollaborator.objects.filter(...)  # DB query (BLOCKS)
    return build_api_response(...)
```

### Why Sync Works Here

1. **Django ORM is blocking** — no async driver for PostgreSQL/SQLite in standard library
2. **Celery tasks are blocking** — `task.delay(...)` is sync
3. **Uvicorn supports sync handlers** — runs them in thread pool (default 10 threads)
4. **Performance is acceptable** — thread pool handles moderate concurrency

### What Happens If You Use Async

```python
@router.get("/notes/{note_id}/collaborators/")
async def list_collaborators(note_id: int, token: str = Depends(_verify_credentials)):
    # PROBLEM: Django ORM is still blocking!
    user = verify_auth_header(token)  # Still blocks, freezes event loop
    note = await Note.objects.filter(...)  # FAILS: can't await sync ORM
    # ✗ This creates deadlocks and performance degradation
```

**Rule:** Only use `async def` when dependencies support async (async DB driver, async HTTP client, etc.).

### Trade-off Table

| Aspect | Sync (`def`) | Async (`async def`) |
|--------|--------------|-------------------|
| Code style | Simple, familiar | More complex |
| Django ORM | ✅ Works | ✗ Blocks event loop |
| Celery tasks | ✅ Works | ✅ Can work with async tasks |
| Concurrency model | Thread pool | Event loop |
| Performance (DB-heavy) | Adequate for small/medium loads | Better (if async DB) |
| Current project | ✅ Using this | Not applicable |
| Learning curve | Low | Medium-High |

### When to Migrate to Async

- Replace blocking DB with async driver (e.g., `databases`, `tortoise-orm`)
- Replace blocking HTTP calls with async client (e.g., `httpx`)
- Have high-concurrency requirements (1000+ concurrent requests)

**For now:** Stick with sync. It's cleaner, works with Django ORM, and meets your project's needs.

---

## Integration Points

### 1. Shared Database

**Both Django and FastAPI query the same PostgreSQL/SQLite:**

```python
# In Django API
note = Note.objects.filter(id=note_id).first()

# In FastAPI API
note = Note.objects.filter(id=note_id).first()  # Same ORM, same DB

# Result: Single source of truth
```

### 2. Shared Authentication

**JWT tokens created by Django, validated by FastAPI:**

```python
# Django creates tokens:
from users.token_utils import generate_tokens
tokens = generate_tokens(user.id)  # Uses SECRET_KEY

# FastAPI validates same tokens:
from fastapi_app.utils.auth import verify_auth_header
user = verify_auth_header(authorization_header)  # Uses same SECRET_KEY
```

### 3. Shared Models

**Both import from the same `models.py`:**

```python
# In Django
from notes.models import Note, NoteCollaborator

# In FastAPI
from notes.models import Note, NoteCollaborator  # Same imports
```

### 4. Shared Task Queue (Celery)

**Both can dispatch async tasks:**

```python
# In Django API
from users.tasks import send_note_collaborator_added_email
send_note_collaborator_added_email.delay(invite_id)

# In FastAPI API
from users.tasks import send_note_collaborator_added_email
send_note_collaborator_added_email.delay(invite_id)  # Same task
```

### 5. Shared Cache

**Both use Django's cache backend:**

```python
from django.core.cache import cache

# In Django
cache.get(key)
cache.set(key, value, timeout=300)

# In FastAPI
cache.get(key)  # Same backend
cache.set(key, value, timeout=300)
```

---

## Viva Q&A

### Q1: Why did you add FastAPI when you already have Django REST Framework?

**Answer:**

FastAPI offers several advantages:
1. **Type hints + auto docs** — Pydantic models auto-generate Swagger/OpenAPI docs; DRF requires `drf-spectacular`
2. **Lightweight** — FastAPI routes are simpler; DRF is heavy and model-driven
3. **Validation** — Pydantic is cleaner and more Pythonic than DRF serializers
4. **Future-ready** — FastAPI is async-native; easy to migrate to async when needed
5. **Performance** — FastAPI is faster for high-concurrency scenarios

We used it for collaborator endpoints because they're cross-cutting features needing custom logic. Django stays for core models, admin, and migrations.

---

### Q2: How do FastAPI and Django share the database?

**Answer:**

Both use the **Django ORM**. When Starlette initializes in `asgi.py`:

1. Django is set up first: `django.setup()`
2. FastAPI is imported after Django is ready
3. FastAPI handlers call Django ORM directly: `Note.objects.filter(...)`
4. Both connect to the same PostgreSQL/SQLite instance

Result: Single database, consistent data.

---

### Q3: Is there a risk of one overwriting the other's data?

**Answer:**

No, because:
- **Single database** ensures atomicity via ACID transactions
- **Same ORM** means both respect constraints and migrations
- **Cache invalidation** is triggered by both endpoints
- **Transactions** work the same way in Django and FastAPI

Example:
```python
# If Django creates Note X, FastAPI can immediately query it
note = Note.objects.filter(id=X).first()  # Works in both
```

---

### Q4: How does authentication work across both?

**Answer:**

JWT tokens are created by Django and validated by FastAPI:

```
1. Django creates token:
   tokens = generate_tokens(user.id)  # Uses settings.SECRET_KEY

2. Token payload:
   {
     "user_id": 5,
     "token_type": "access",
     "exp": 1234567890,
     "iat": 1234567000
   }

3. FastAPI validates same token:
   payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
   if payload.get("token_type") != "access":
       raise HTTPException(401, "Invalid token type")
   user = User.objects.filter(pk=payload["user_id"]).first()

Result: Both use the same SECRET_KEY, so tokens are compatible
```

---

### Q5: What if I need to make an endpoint async?

**Answer:**

Only if you use async libraries:

```python
# WRONG: Using async with blocking Django ORM
@router.get("/notes/")
async def list_notes():
    notes = await Note.objects.all()  # ✗ FAILS: ORM is blocking

# RIGHT: Stick with sync for Django ORM
@router.get("/notes/")
def list_notes():
    notes = Note.objects.all()  # ✓ Works
    return build_api_response("Notes fetched", [...], 200)
```

**Migration path:**
- Current: Use `def` with Django ORM (sync)
- Future: Migrate to async DB driver → use `async def`

For now, sync is fine because Uvicorn thread pool handles blocking calls.

---

### Q6: How is the response envelope applied?

**Answer:**

Both Django and FastAPI use `build_api_response()`:

```python
# Django (in EnvelopeAPIView.finalize_response)
response.data = build_api_response(
    message="Notes fetched",
    payload=serialized_data,
    status_code=200
)

# FastAPI (in route handler)
return build_api_response(
    "Collaborators fetched",
    payload_data,
    200
)

# Result (both):
{
  "message": "...",
  "payload": {...},
  "status code": 200
}
```

Clients always see the same structure.

---

### Q7: How do Pydantic schemas and Django serializers differ?

**Answer:**

| Aspect | Pydantic | DRF Serializer |
|--------|----------|----------------|
| **Definition** | Type hints (BaseModel) | Class-based (Serializer) |
| **Validation** | Automatic from types | Explicit validators |
| **Auto docs** | ✅ OpenAPI (built-in) | ⚠️ Via drf-spectacular |
| **Serialization** | `.dict()` → JSON | `.data` → JSON |
| **Speed** | Fast (minimal overhead) | Slower (feature-rich) |
| **Learning curve** | Easy (Python types) | Medium (DRF concepts) |

**Example:**
```python
# Pydantic
class CollaboratorSchema(BaseModel):
    name: str
    access_level: str

# DRF
class CollaboratorSerializer(serializers.Serializer):
    name = serializers.CharField()
    access_level = serializers.CharField()
```

Pydantic is more concise.

---

### Q8: What happens if the frontend sends invalid JSON?

**Answer:**

**Django:** Standard 400 Bad Request
```json
{"detail": "JSON parse error"}
```

**FastAPI:** 422 Unprocessable Entity with detailed validation errors (Pydantic)
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

FastAPI's detailed errors help frontend developers debug faster.

---

### Q9: Can you run Django and FastAPI on the same port?

**Answer:**

Yes, via Starlette ASGI router in `asgi.py`:

```python
from starlette.applications import Starlette
from starlette.routing import Mount

application = Starlette(
    routes=[
        Mount("/fastapi", app=fastapi_app),    # FastAPI at /fastapi/*
        Mount("/", app=django_asgi_app),        # Django at /*
    ]
)
```

**How it works:**
- One HTTP server (Uvicorn) listens on port 8000
- Starlette routes based on path:
  - `/fastapi/login/` → FastAPI
  - `/api/notes/` → Django
  - `/admin/` → Django

**Example commands:**
```bash
# Serve both on same port
uvicorn FundooMain.asgi:application --host 0.0.0.0 --port 8000

# OR use Django development server (which serves via ASGI)
python manage.py runserver
```

---

### Q10: What's the overhead of running two frameworks?

**Answer:**

Minimal because:
- **One Python process** — no inter-process communication
- **One ASGI server** (Uvicorn) — single event loop
- **Shared memory** — ORM connections, cache, settings are in-process
- **Routing overhead** — Starlette path matching is negligible (~1ms)

**Performance comparison:**
- Pure Django (DRF): baseline
- Django + FastAPI: +5-10% memory, <1ms routing overhead
- Separate Django + FastAPI processes: +100ms communication latency

Running together is efficient.

---

### Q11: How does dependency injection work in FastAPI?

**Answer:**

FastAPI uses function parameters with `Depends()`:

```python
def _verify_credentials(credentials = Depends(security)) -> str:
    return f"Bearer {credentials.credentials}"

@router.get("/notes/{note_id}/collaborators/")
def list_collaborators(
    note_id: int,
    token: str = Depends(_verify_credentials)
):
    user = verify_auth_header(token)  # token is auto-injected
    # ... rest of handler
```

**Flow:**
1. Route is called
2. FastAPI sees `Depends(_verify_credentials)`
3. Calls `_verify_credentials()` to get the token
4. Passes token to handler

**Benefits:**
- Clean, testable code
- Separation of concerns
- Reusable dependency logic

---

### Q12: How do you test FastAPI endpoints?

**Answer:**

**Unit test (mock dependencies):**
```python
from fastapi.testclient import TestClient
from fastapi_app.app import app

client = TestClient(app)

def test_login_success(monkeypatch):
    def mock_check_password(plain, hashed):
        return True
    monkeypatch.setattr("django.contrib.auth.hashers.check_password", mock_check_password)
    
    response = client.post("/fastapi/login/", json={
        "email": "user@example.com",
        "password": "secret"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"
```

**Integration test (real DB):**
```bash
curl -X POST http://localhost:8000/fastapi/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'
```

---

### Q13: What's the difference between `response_model` and `responses` in FastAPI?

**Answer:**

| Feature | `response_model` | `responses` |
|---------|-----------------|-----------|
| **Purpose** | Validate/coerce actual response | Define response schema for docs |
| **Effect on runtime** | Modifies output | None |
| **Effect on OpenAPI** | Modifies docs | Modifies docs |
| **Use case** | Ensure data shape at runtime | Show docs-only fields |

**Example:**
```python
# response_model: validates and transforms runtime response
@router.get("/notes/", response_model=NoteSerializer)
def list_notes():
    notes = Note.objects.all()
    return notes  # Pydantic will validate and transform

# responses: only affects OpenAPI docs
@router.get("/notes/", responses={200: {"model": NotesDocsEnvelope}})
def list_notes():
    notes = Note.objects.all()
    return build_api_response("Notes fetched", notes, 200)
    # Runtime payload stays full; docs show trimmed schema
```

**In your project:** Use `responses` for docs-only shapes while keeping full runtime payload.

---

### Q14: How does Pydantic validate email addresses?

**Answer:**

Pydantic uses the `email-validator` package:

```python
from pydantic import BaseModel, EmailStr

class LoginSchema(BaseModel):
    email: EmailStr  # Auto-validates email format

# Valid:
LoginSchema(email="user@example.com")  # ✓

# Invalid:
LoginSchema(email="not-an-email")  # ✗ Raises ValidationError
```

**Validation checks:**
- Must have `@` symbol
- Must have domain name
- Must have valid TLD (e.g., `.com`, `.org`)

---

### Q15: Can Django and FastAPI share Celery tasks?

**Answer:**

Yes, both dispatch the same Celery tasks:

```python
# In both Django and FastAPI
from users.tasks import send_note_collaborator_added_email

send_note_collaborator_added_email.delay(invite_id)
```

**How it works:**
- Celery task defined in `users/tasks.py`
- Both Django and FastAPI use same Celery broker (Redis/RabbitMQ)
- Celery worker processes tasks regardless of origin

Result: Consistent background job handling.

---

## Demo Checklist

### Prerequisites

```bash
cd /Users/apple/FundooMain
source /Users/apple/myenv/bin/activate
cd backend
```

### Start Servers

```bash
# Terminal 1: Django (serves both Django + FastAPI via ASGI)
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Celery (optional, for task processing)
celery -A FundooMain worker -l info

# Terminal 3: Redis (optional, if using Redis as broker/cache)
redis-server
```

### Demo Steps for Viva

#### Step 1: Show the Architecture Files

```
Open and explain:
1. backend/FundooMain/asgi.py
   - Show: django.setup() before FastAPI import
   - Show: Starlette mounts (Mount("/fastapi", ...), Mount("/", ...))

2. backend/FundooMain/fastapi.py
   - Show: simple importer from fastapi_app.app

3. backend/fastapi_app/app.py
   - Show: FastAPI(title="...", version="...")
   - Show: app.include_router(collaborators.router)
   - Show: app.include_router(auth.router)
```

#### Step 2: Show Pydantic Validation

```
Open backend/fastapi_app/schemas/auth.py
Point to:
  class LoginSchema(BaseModel):
      email: EmailStr
      password: str

Explain:
- EmailStr auto-validates email format
- Type hints are checked at runtime
- Invalid email → 422 Unprocessable Entity
```

#### Step 3: Show Auth Flow

```
Open backend/fastapi_app/utils/auth.py
Point to:
  - get_bearer_token(): extracts "Bearer XXX"
  - decode_token(): uses SECRET_KEY
  - verify_auth_header(): full pipeline
  - get_user_from_token(): queries User model

Explain:
- Uses Django's SECRET_KEY (compatible)
- Calls Django ORM
- Works in sync context
```

#### Step 4: Show Route Handler

```
Open backend/fastapi_app/routers/auth.py
Point to:
  @router.post("/login/", response_model=ApiResponseSchema)
  def login(credentials: LoginSchema):
      ...
      return build_api_response("Login successful", payload.dict(), 200)

Explain:
- Pydantic validates input (LoginSchema)
- Handler uses Django ORM
- Returns envelope via build_api_response()
```

#### Step 5: Show ASGI Routing

```
Open backend/FundooMain/asgi.py
Point to:
  application = Starlette(
      routes=[
          Mount("/fastapi", app=fastapi_app),
          Mount("/", app=django_asgi_app),
      ]
  )

Explain:
- Single entry point
- Routes by path prefix
- Both use same Django instance
```

#### Step 6: Test Login Endpoint

```bash
# Request
curl -X POST http://localhost:8000/fastapi/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "pratyushgolwala@gmail.com", "password": "your_password"}'

# Expected response
{
  "message": "Login successful",
  "payload": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "...",
    "token_type": "bearer",
    "user_id": 1,
    "user_email": "pratyushgolwala@gmail.com",
    "user_name": "Pratyush"
  },
  "status code": 200
}

# Save the token for next request
TOKEN="<access_token_from_response>"
```

#### Step 7: Test Collaborator Endpoint

```bash
# Request with token
curl -X GET http://localhost:8000/fastapi/notes/123/collaborators/ \
  -H "Authorization: Bearer $TOKEN"

# Expected response
{
  "message": "Collaborators fetched",
  "payload": [
    {"name": "Alice", "access_level": "edit"},
    {"name": "Bob", "access_level": "view"}
  ],
  "status code": 200
}
```

#### Step 8: Show OpenAPI Docs

```
Open in browser:
http://localhost:8000/fastapi/docs

Show:
- List of all FastAPI endpoints
- Try-it-out functionality
- Request/response examples
- Automatic generation from Pydantic schemas
```

#### Step 9: Show Shared Database

```python
# Open Python shell
python manage.py shell

# Query from Django shell (same as FastAPI would)
from notes.models import Note
note = Note.objects.first()
print(note.title)  # Proves same DB

# Exit and show FastAPI also can access
```

#### Step 10: Test Invalid Input

```bash
# Invalid email
curl -X POST http://localhost:8000/fastapi/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "not-an-email", "password": "secret"}'

# Expected: 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

---

## Key Takeaways

### Viva One-Liner

**"FastAPI is integrated with Django via a shared ASGI entry point (Starlette), allowing lightweight, type-safe API routes (collaborators, auth) to leverage Django ORM, models, cache, and tokens while maintaining a consistent response envelope across both frameworks."**

### Architecture Summary

```
Frontend (React)
    ↓ HTTP
Starlette Router (asgi.py)
    ├─ /fastapi/* → FastAPI + Pydantic + Django ORM
    └─ /* → Django + DRF + Django ORM
    ↓ Both share
PostgreSQL + Redis + Celery + Django Settings
```

### Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI | Modern, type-safe API |
| **Validation** | Pydantic | Request/response shapes |
| **ORM** | Django ORM | Database access |
| **Auth** | JWT + Django settings | Token generation & validation |
| **Tasks** | Celery | Background jobs |
| **Cache** | Redis | Request/query caching |
| **Docs** | OpenAPI/Swagger | Auto-generated API docs |

### Benefits of This Setup

1. ✅ **Clean separation** — Django for models/admin, FastAPI for lightweight APIs
2. ✅ **Shared resources** — Single DB, cache, auth system
3. ✅ **Auto docs** — OpenAPI docs auto-generated from Pydantic
4. ✅ **Type safety** — Pydantic catches errors at request time
5. ✅ **Testability** — Dependency injection makes unit tests easy
6. ✅ **Future-proof** — Easy to migrate to async when needed

### Common Pitfalls to Avoid

1. ❌ Setting `response_model` when you want docs-only shapes
2. ❌ Using `async def` with Django ORM (will block event loop)
3. ❌ Forgetting to call `django.setup()` before importing FastAPI
4. ❌ Using different secrets for Django and FastAPI tokens
5. ❌ Assuming Django and FastAPI have separate databases

---

## Quick Reference Commands

### Start development servers

```bash
# Terminal 1: Both Django + FastAPI (via ASGI)
cd backend && python manage.py runserver 0.0.0.0:8000

# Terminal 2: Celery worker
cd backend && celery -A FundooMain worker -l info

# Terminal 3: Generate OpenAPI schema
cd backend && python manage.py spectacular --file openapi.yaml
```

### Test endpoints

```bash
# Login
curl -X POST http://localhost:8000/fastapi/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass"}'

# Get collaborators (requires token)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/fastapi/notes/1/collaborators/

# Add collaborator
curl -X POST http://localhost:8000/fastapi/notes/1/collaborators/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "colleague@example.com", "access_level": "edit"}'

# Respond to invitation
curl -X POST http://localhost:8000/fastapi/invitations/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"invite_id": 5, "action": "accept"}'
```

### View documentation

- FastAPI Swagger UI: `http://localhost:8000/fastapi/docs`
- FastAPI ReDoc: `http://localhost:8000/fastapi/redoc`
- OpenAPI schema JSON: `http://localhost:8000/fastapi/openapi.json`

---

## Study Tips for Viva

1. **Understand the flow** — Trace a request from client → FastAPI → Django ORM → response
2. **Know the files** — Be able to point to key files and explain their role
3. **Practice the demo** — Run the commands and show the responses
4. **Explain trade-offs** — Why sync over async, FastAPI over pure DRF
5. **Be ready for follow-ups** — Questions about async, scaling, testing
6. **Have examples ready** — Show code snippets for each concept

---

**Good luck with your viva! 🚀**
