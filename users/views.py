from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password, make_password

from .models import User


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
        
        user = User.objects.create(
            name=name,
            email=email,
            phone_number=phone_number,
            password=make_password(password)
        )
        user.save()
        return redirect('login')
    return render(request, 'signup.html')


def home(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return render(request, 'home.html', {'user': user})
    except User.DoesNotExist:
        return redirect('login')

