# FundooNotes - Full Stack Note Taking Application

A full-stack note-taking and organization application with Django REST API backend and React frontend.

## 🏗️ Project Structure

```
FundooMain/
├── backend/              # Django REST API Backend
│   ├── manage.py
│   ├── FundooMain/       # Django project config
│   ├── users/            # User authentication & authorization
│   ├── notes/            # Note CRUD operations
│   ├── labels/           # Note labeling system
│   ├── .env              # Environment variables
│   ├── db.sqlite3        # SQLite database
│   └── [more configs]
│
├── frontend/             # React Frontend (Coming Soon)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env
│
├── docker-compose.yml    # Docker services configuration
├── .gitignore
└── README.md
```

## 🚀 Features

### Backend (Django + DRF)
- ✅ Email verification with OTP (Multi-Factor Authentication)
- ✅ JWT Token-based authentication (Access & Refresh tokens)
- ✅ Rate limiting (Throttling) to prevent abuse
- ✅ Redis caching for optimized performance
- ✅ Celery async tasks for email sending
- ✅ Full CRUD operations for notes
- ✅ Multiple labels per note (ManyToMany relationship)
- ✅ Advanced filtering (search, color, pin, archive)
- ✅ Automatic token cleanup (scheduled tasks)

### Frontend (React) - In Development
- User registration and login
- Email verification flow
- Dashboard with notes management
- Label organization
- Search and filter functionality
- Responsive UI design

## 📋 Prerequisites

### Backend Requirements
- Python 3.11+
- Django 5.2+
- Redis server
- PostgreSQL/SQLite

### Frontend Requirements
- Node.js 16+
- npm or yarn

## 🔧 Setup Instructions

### Backend Setup

1. **Navigate to backend folder:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   # Copy .env.example to .env and update values
   cp .env.example .env
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start development server:**
   ```bash
   python manage.py runserver
   ```

### Backend Services

In separate terminals:

**Terminal 1: Django Dev Server**
```bash
cd backend
source myenv/bin/activate
python manage.py runserver
```

**Terminal 2: Redis Server**
```bash
redis-server
```

**Terminal 3: Celery Worker**
```bash
cd backend
source myenv/bin/activate
celery -A FundooMain worker -l info
```

**Terminal 4: Celery Beat (Scheduled Tasks)**
```bash
cd backend
source myenv/bin/activate
celery -A FundooMain beat -l info
```

### Frontend Setup (Soon)

```bash
cd frontend
npm install
npm start
```

## 🔌 API Documentation

API documentation available at: `http://localhost:8000/api/schema/swagger/`

### Key Endpoints

#### Authentication
- `POST /api/signup/` - User registration
- `POST /api/login/` - User login (returns OTP)
- `POST /api/verify-otp/` - Verify OTP (returns tokens)
- `POST /api/refresh-token/` - Refresh access token

#### Notes
- `GET /api/notes/` - Get all notes (with filters)
- `POST /api/notes/` - Create a new note
- `GET /api/notes/{id}/` - Get single note
- `PUT /api/notes/{id}/` - Update note
- `DELETE /api/notes/{id}/` - Delete note

#### Labels
- `GET /api/labels/` - Get all labels
- `POST /api/labels/` - Create label
- `PUT /api/labels/{id}/` - Update label
- `DELETE /api/labels/{id}/` - Delete label

## 🔐 Authentication Flow

```
1. User Signup
   ├─ Email + Password → Hashed & Stored
   └─ Verification email sent

2. Email Verification
   ├─ User clicks link
   └─ is_email_verified = True

3. Login
   ├─ Email/Username + Password
   └─ OTP sent to email

4. OTP Verification
   ├─ User enters 6-digit OTP
   └─ Access & Refresh tokens generated

5. API Access
   ├─ Bearer token in Authorization header
   └─ Protected endpoints accessible
```

## 🗄️ Database Schema

### User Model
- id, name, email, phone_number
- is_email_verified, email_verification_token
- otp_code, otp_expires_at
- created_at, updated_at

### Note Model
- id, user_id, title, content
- labels (ManyToMany)
- color, is_pinned, is_archived
- created_at, updated_at

### Label Model
- id, user_id, name
- created_at, updated_at

## 🎯 Development Workflow

1. Create feature branch: `git checkout -b feature/feature-name`
2. Make changes in backend or frontend
3. Test thoroughly
4. Commit: `git commit -m "Add feature"`
5. Push: `git push origin feature/feature-name`
6. Create Pull Request

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest                    # Run all tests
pytest -v               # Verbose output
pytest notes/tests.py   # Specific test file
```

## 📦 Technologies Used

### Backend
- Django 5.2 - Web framework
- Django REST Framework - API framework
- JWT (PyJWT) - Token authentication
- Celery - Async task queue
- Redis - Caching & message broker
- SQLite/PostgreSQL - Database

### Frontend (Planned)
- React 18+ - UI library
- Axios - HTTP client
- React Router - Navigation
- Redux/Context API - State management
- Tailwind CSS - Styling

## 🔒 Security Features

- Password hashing with Django's secure hashers
- Email verification required before login
- OTP-based Multi-Factor Authentication (MFA)
- Rate limiting on sensitive endpoints
- JWT token expiry (1 hour for access, 7 days for refresh)
- CSRF protection
- Secure cookie settings

## 📊 Performance Optimizations

- Redis caching for frequently accessed data
- Database query optimization with select_related/prefetch_related
- Asynchronous email sending with Celery
- Request execution time monitoring via middleware
- Pagination for large datasets

## 🐛 Troubleshooting

### Redis Connection Error
```bash
# Start Redis
redis-server

# Verify Redis is running
redis-cli ping  # Should return PONG
```

### Database Migration Issues
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### Celery Tasks Not Running
```bash
# Ensure Redis and Celery worker are running
celery -A FundooMain worker -l info
```

## 📝 Environment Variables (.env)

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
REDIS_CACHE_LOCATION=redis://127.0.0.1:6379/1

# Database
DATABASE_URL=sqlite:///db.sqlite3
```

## 📞 Support

For issues or questions, please check:
- Backend API docs: `/api/schema/swagger/`
- Code comments in key files
- Git commit history

## 📄 License

MIT License - feel free to use this project as a reference

---

**Status**: Backend Complete ✅ | Frontend In Progress 🚧