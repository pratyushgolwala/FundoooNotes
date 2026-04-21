from sqlite3 import IntegrityError

from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from rest_framework.response import Response
from .models import User
from .tasks import send_verification_email


from .models import User




def verify_email(request, token):
    """Verify user email with token"""
    try:
        user = User.objects.get(email_verification_token=token)
        user.is_email_verified = True
        user.email_verification_token = None
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
                    'error': 'Please verify your email first. Check your inbox for the verification link.',
                    'email_pending': user.email
                })
            
            request.session['user_id'] = user.pk
            return redirect('home', user_id=user.pk)
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


def signup_view(request):
    if request.method == 'POST':
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
            # ✅ SEND VERIFICATION EMAIL
            send_verification_email.delay(user.pk)
            
            return render(request, 'email_pending.html', {
                'email': email,
                'message': 'Verification email sent! Check your inbox to verify your email.'
            })
        except IntegrityError:
            return render(request, 'signup.html', {'error': 'Email already exists'})
    return render(request, 'signup.html')

def home(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return render(request, 'home.html', {'user': user})
    except User.DoesNotExist:
        return redirect('login')

