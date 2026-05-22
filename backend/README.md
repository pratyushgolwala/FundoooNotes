# FundooNotes Backend

Django REST API backend for FundooNotes application with complete authentication, email verification, OTP system, and note management.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Redis server running
- Virtual environment

### Installation

1. **Activate virtual environment:**
   ```bash
   source myenv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install django djangorestframework celery redis PyJWT drf-spectacular drf-excel pytest pytest-django
   ```

3. **Configure `.env` file:**
   ```bash
   # Create from .env if not exists
   DJANGO_SECRET_KEY=your-secret-key
   DJANGO_DEBUG=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start services:**

   **Terminal 1: Django server**
   ```bash
   python manage.py runserver
   ```

   **Terminal 2: Redis**
   ```bash
   redis-server
   ```

   **Terminal 3: Celery worker**
   ```bash
   celery -A FundooMain worker -l info
   ```

   **Terminal 4: Celery beat**
   ```bash
   celery -A FundooMain beat -l info
   ```

## 📁 Project Structure

```
backend/
├── manage.py                    # Django management tool
├── FundooMain/                  # Main Django config
│   ├── settings.py             # Settings (CACHES, THROTTLE, CELERY)
│   ├── urls.py                 # URL routing
│   ├── wsgi.py                 # WSGI application
│   ├── asgi.py                 # ASGI application
│   ├── celery.py               # Celery configuration
│   └── middleware.py           # Custom middleware
├── users/                       # User management
│   ├── models.py               # User model
│   ├── views.py                # Template views
│   ├── api_views.py            # API endpoints
│   ├── serializers.py          # Request/response serializers
│   ├── token_utils.py          # JWT token generation
│   ├── tasks.py                # Celery async tasks
│   └── tests.py                # Unit tests
├── notes/                       # Note management
│   ├── models.py               # Note model
│   ├── forms.py                # Django forms
│   ├── views.py                # Template views
│   ├── api_views.py            # API endpoints
│   ├── serializers.py          # Note serializers
│   └── tests.py                # Tests
├── labels/                      # Label management
│   ├── models.py               # Label model
│   ├── views.py                # Views
│   └── models.py               # Tests
├── db.sqlite3                   # SQLite database
├── .env                         # Environment variables
└── pytest.ini                   # Pytest configuration
```

## 🔐 Authentication System

### Flow
1. **Signup** → Email verification link sent
2. **Email Verification** → User verifies email
3. **Login** → 6-digit OTP sent to email
4. **OTP Verification** → JWT tokens returned
5. **API Access** → Bearer token in headers

### Key Files
- **User Model:** `users/models.py`
- **Auth Views:** `users/api_views.py`
- **Token Utils:** `users/token_utils.py`
- **Email Tasks:** `users/tasks.py`

## 📊 Database Models

### User
```python
class User(models.Model):
    name, email, phone_number, password
    is_email_verified, email_verification_token
    otp_code, otp_expires_at
```

### Note
```python
class Note(models.Model):
    user (FK), title, content
    labels (M2M), color
    is_pinned, is_archived
    created_at, updated_at
```

### Label
```python
class Label(models.Model):
    user (FK), name
```

## 🔌 API Endpoints

### Authentication
- `POST /api/signup/` - Register new user
- `POST /api/login/` - Login (returns OTP)
- `POST /api/verify-otp/` - Verify OTP (returns tokens)
- `POST /api/refresh-token/` - Refresh access token

### Notes
- `GET /api/notes/` - List (filters: search, pin, archive, label, color)
- `POST /api/notes/` - Create
- `GET /api/notes/{id}/` - Retrieve
- `PUT /api/notes/{id}/` - Update
- `DELETE /api/notes/{id}/` - Delete

### Notes (Web UI)
- `GET /users/{id}/notes/` - Notes list page
- `GET /users/{id}/notes/create/` - Create note form
- `GET /users/{id}/notes/{id}/edit/` - Edit note form
- `POST /users/{id}/notes/delete/` - Delete note

### Labels
- `GET /users/{id}/labels/` - Labels list
- `GET /users/{id}/labels/create/` - Create label form
- `GET /users/{id}/labels/{id}/edit/` - Edit label form
- `POST /users/{id}/labels/delete/` - Delete label

## ⚙️ Key Features

### Rate Limiting (Throttling)
```python
"DEFAULT_THROTTLE_RATES": {
    "anon": "100/hour",      # Guests
    "user": "1000/hour",     # Authenticated
    "signup": "5/hour",      # Prevent spam
    "login": "5/hour",       # Anti-brute force
    "notes": "500/hour",     # API operations
}
```

### Caching (Redis)
- All note queries cached for 5 minutes
- Cache cleared on create/update/delete
- Key format: `user_notes:{user_id}:label:{label_id}`

### Background Tasks (Celery)
- `send_verification_email()` - Async email sending
- `send_otp_email()` - OTP generation & sending
- `cleanup_expired_tokens()` - Runs every 6 hours

### Security
- Passwords hashed with `django.contrib.auth.hashers`
- Email verification required before login
- OTP-based MFA (10 minute validity)
- JWT token expiry (1 hour access, 7 days refresh)
- CSRF protection enabled

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with verbosity
pytest -v

# Test specific app
pytest users/tests.py
pytest notes/tests.py

# Test coverage
pytest --cov=users --cov=notes
```

## 📈 Performance Monitoring

### Middleware Logger
Tracks request execution time:
```
[Middleware Log] GET /api/notes/ took 0.0234 seconds
[Middleware Log] POST /api/notes/ took 0.1567 seconds
```

### Database Queries
Use Django Debug Toolbar (optional) or check SQL logs

## 🔧 Configuration

### settings.py Key Sections
1. **REST_FRAMEWORK** - DRF configuration
2. **CACHES** - Redis cache settings
3. **CELERY_** - Celery/Redis broker setup
4. **EMAIL_** - SMTP email configuration

### Environment Variables
All sensitive data in `.env`:
```env
DJANGO_SECRET_KEY
DJANGO_DEBUG
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
CELERY_BROKER_URL
REDIS_CACHE_LOCATION
```

## 🐛 Troubleshooting

### "Cannot connect to Redis"
```bash
redis-cli ping
# If no response, start Redis:
redis-server
```

### "Invalid token type"
- Ensure using `access_token`, not `refresh_token`
- Token type verified in `_get_user_from_request()`

### "Email not sending"
- Check `.env` has correct Gmail credentials
- Gmail requires App Password (not regular password)
- Ensure "Less secure apps" enabled or 2FA app password set

### Database locked
```bash
rm db.sqlite3
python manage.py migrate
```

## 📝 Important Code Locations

| Functionality | File | Key Lines |
|---|---|---|
| Password hashing | `users/api_views.py` | Line 45 `make_password()` |
| Email verification | `users/tasks.py` | Line 9-37 `send_verification_email` |
| OTP validation | `users/api_views.py` | Line 122-125 |
| Token generation | `users/token_utils.py` | All functions |
| Auth check | `notes/api_views.py` | Line 34-60 `_get_user_from_request` |
| Caching | `notes/api_views.py` | Line 156-173 |
| Rate limiting | `settings.py` | Line 72-80 |

## 🚀 Deployment

### Using Docker (Optional)
```bash
docker-compose up
```

### Using Heroku
```bash
git push heroku main
heroku run python manage.py migrate
```

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [DRF Guide](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.io/)
- [JWT Tokens](https://pyjwt.readthedocs.io/)

---

**Backend Status**: ✅ Complete and Production-Ready
