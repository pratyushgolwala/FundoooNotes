from django.shortcuts import render, redirect
from .models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password, make_password


# Create your views here.

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
                user = None
                
        if user and check_password(password, user.password):
            request.session['user_id'] = user.pk  # Store user ID in session
            return redirect('home', user_id=user.pk)  # Redirect to a home page after successful login
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')


def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        
        user = User.objects.create(name=name, email=email, phone_number=phone_number, password=make_password(password))
        user.save()
        return redirect('login')  # Redirect to login page after successful signup  
    return render(request, 'signup.html')

def home(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        # notes = Note.objects.filter(user=user).order_by('-created_at')
        return render(request, 'home.html', {
            'user': user,
            # 'notes': notes
        })
    except User.DoesNotExist:
        return redirect('login')