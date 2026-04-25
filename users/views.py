from django.db import IntegrityError
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password, make_password
import redis
from .models import User
from .tasks import send_verification_email, send_otp_email


LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW_SECONDS = 20
SIGNUP_ATTEMPT_LIMIT = 5
SIGNUP_ATTEMPT_WINDOW_SECONDS = 3600

redis_client = redis.Redis(host='localhost', port=6379, db=1)


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _login_attempt_key(request, identifier):
    return f"login_attempts:{_client_ip(request)}:{identifier}"


def _login_disabled_key(request, identifier):
    return f"login_disabled:{_client_ip(request)}:{identifier}"


def _signup_attempt_key(request):
    return f"signup_attempts:{_client_ip(request)}"


def _signup_disabled_key(request):
    return f"signup_disabled:{_client_ip(request)}"


def _increment_with_setex(key, ttl_seconds):
    count = redis_client.get(key)
    if count is None:
        redis_client.setex(key, ttl_seconds, 1)
        return 1
    incr_result = redis_client.incr(key)
    if isinstance(incr_result, int):
        return incr_result
    return 1



def verify_email(request, token):
    """Verify user email with token"""
    try:
        user = User.objects.get(email_verification_token=token)
        user.is_email_verified = True
        user.email_verification_token = None
        user.otp_code = None
        user.otp_expires_at = None
        user.save()
        return render(request, "email_verified.html", {
            "message": "Email verified successfully! You can now login.",
            "user": user
        })
    except User.DoesNotExist:
        return render(request, "email_verified.html", {
            "message": "Invalid or expired verification token.",
            "error": True
        })
        
def resend_verification_email(request):
    """Resend verification email to a user"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_email_verified:
                return render(request, 'resend_email.html', {
                    'message': 'Your email is already verified! You can now login.',
                    'verified': True
                })
            
            # Resend verification email
            send_verification_email.delay(user.pk)
            
            return render(request, 'resend_email.html', {
                'message': f'Verification email resent to {email}. Check your inbox!',
                'success': True
            })
        except User.DoesNotExist:
            return render(request, 'resend_email.html', {
                'error': 'No account found with this email address.'
            })
    
    return render(request, 'resend_email.html')
        
def login_view(request):
    if request.method == 'POST':
        name = request.POST.get('username')
        password = request.POST.get('password')

        attempt_key = _login_attempt_key(request, name)
        disabled_key = _login_disabled_key(request, name)

        if redis_client.exists(disabled_key):
            ttl_raw = redis_client.ttl(disabled_key)
            ttl = ttl_raw if isinstance(ttl_raw, int) else 0
            ttl = max(ttl, 0)
            return render(request, 'login.html', {
                'error': f'Login temporarily disabled. Please try again in {ttl} seconds.'
            })
        
        user = None
        try:
            user = User.objects.get(name=name)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=name)
            except User.DoesNotExist:
                pass
                
        if user and check_password(password, user.password):
            # ✅ CHECK EMAIL VERIFICATION
            if not user.is_email_verified:
                return render(request, 'login.html', {
                    'error': 'Please verify your account first using the verification link sent to your email.',
                    'email_pending': user.email
                })

            redis_client.delete(attempt_key)
            redis_client.delete(disabled_key)
            
            # ✅ SEND OTP FOR LOGIN MFA
            send_otp_email.delay(user.pk)
            
            # Show OTP form to complete login
            return render(request, 'otp_verify.html', {
                'email': user.email,
                'message': 'Login successful. Please complete the final step by entering the 6-digit OTP sent to your email.'
            })
        else:
            attempts = _increment_with_setex(attempt_key, LOGIN_ATTEMPT_WINDOW_SECONDS)
            if attempts >= LOGIN_ATTEMPT_LIMIT:
                redis_client.setex(disabled_key, LOGIN_ATTEMPT_WINDOW_SECONDS, 1)
                return render(request, 'login.html', {
                    'error': 'Login temporarily disabled due to too many failed attempts. Please try again later.'
                })

            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


def signup_view(request):
    if request.method == 'POST':
        signup_attempt_key = _signup_attempt_key(request)
        signup_disabled_key = _signup_disabled_key(request)

        if redis_client.exists(signup_disabled_key):
            ttl_raw = redis_client.ttl(signup_disabled_key)
            ttl = ttl_raw if isinstance(ttl_raw, int) else 0
            ttl = max(ttl, 0)
            return render(request, 'signup.html', {
                'error': f'Signup temporarily disabled. Please try again in {ttl} seconds.'
            })

        attempts = _increment_with_setex(signup_attempt_key, SIGNUP_ATTEMPT_WINDOW_SECONDS)
        if attempts > SIGNUP_ATTEMPT_LIMIT:
            redis_client.setex(signup_disabled_key, SIGNUP_ATTEMPT_WINDOW_SECONDS, 1)
            return render(request, 'signup.html', {
                'error': 'Signup temporarily disabled due to too many attempts. Please try again later.'
            })

        name = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        
        try:
            user = User.objects.create(
                name=name,
                email=email,
                phone_number=phone_number,
                password=make_password(password)
            )
            # Send only the verification link for signup
            send_verification_email.delay(user.pk)
            message = 'Verification link email sent! Click the link from your inbox to verify your account.'
            return render(request, 'email_pending.html', {
                'email': email,
                'message': message,
            })
        except IntegrityError:
            return render(request, 'signup.html', {'error': 'Email already exists'})
    return render(request, 'signup.html')


def verify_otp_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "otp_verify.html", {"error": "User not found.", "email": email})

        if not user.otp_code or not user.otp_expires_at:
            return render(request, "otp_verify.html", {"error": "No OTP found. Please request a new one.", "email": email})

        if timezone.now() > user.otp_expires_at:
            return render(request, "otp_verify.html", {"error": "OTP expired. Please resend OTP.", "email": email})

        if otp != user.otp_code:
            return render(request, "otp_verify.html", {"error": "Invalid OTP.", "email": email})

        user.otp_code = None
        user.otp_expires_at = None
        user.save(update_fields=["otp_code", "otp_expires_at"])

        # OTP is successful, MFA passed, establish session correctly
        request.session['user_id'] = user.pk
        return redirect('home', user_id=user.pk)

    # For GET requests we might pass email if we redirect with query param or just simple render
    email = request.GET.get('email', '')
    return render(request, "otp_verify.html", {"email": email})

def resend_otp_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            send_otp_email.delay(user.pk)
            return render(request, "otp_verify.html", {"success": "OTP resent successfully. Check your inbox.", "email": email})
        except User.DoesNotExist:
            return render(request, "otp_verify.html", {"error": "No account found with this email.", "email": email})

    return render(request, "otp_verify.html")

def home(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return render(request, 'home.html', {'user': user})
    except User.DoesNotExist:
        return redirect('login')

