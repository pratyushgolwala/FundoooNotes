from django.shortcuts import render, redirect

from django.contrib.auth.hashers import check_password, make_password

from .forms import LoginForm, SignupForm
from .models import User


# Create your views here.

def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        identifier = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = User.objects.filter(name=identifier).first() or User.objects.filter(email=identifier).first()
        if user and check_password(password, user.password):
            request.session['user_id'] = user.pk
            return redirect('home', user_id=user.pk)

        form.add_error(None, 'Invalid credentials')

    return render(request, 'login.html', {"form": form})


def signup_view(request):
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        name = form.cleaned_data['username']
        email = form.cleaned_data['email']
        phone_number = form.cleaned_data['phone_number']
        password = form.cleaned_data['password']

        user = User.objects.create(
            name=name,
            email=email,
            phone_number=phone_number,
            password=make_password(password),
        )
        user.save()
        return redirect('login')

    return render(request, 'signup.html', {"form": form})

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