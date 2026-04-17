from django.shortcuts import render, redirect

from django.contrib.auth.hashers import check_password, make_password

from .forms import *
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
    

def notes_list(request, user_id):
    user = User.objects.get(pk=user_id)
    notes = Note.objects.filter(user=user).order_by("-created_at")
    return render(request, "notes_list.html", {"user": user, "notes": notes})

def note_create(request, user_id):
    user = User.objects.get(pk=user_id)
    form = NoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        note = form.save(commit=False)
        note.user = user
        note.save()
        return redirect("notes-list", user_id=user.id)
    return render(request, "note_form.html", {"form": form, "user": user})

def note_update(request, user_id, note_id):
    user = User.objects.get(pk=user_id)
    note = Note.objects.get(pk=note_id, user=user)
    form = NoteForm(request.POST or None, instance=note)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("notes-list", user_id=user.id)
    return render(request, "note_form.html", {"form": form, "user": user, "note": note})

def note_delete(request, user_id, note_id):
    user = User.objects.get(pk=user_id)
    note = Note.objects.get(pk=note_id, user=user)
    if request.method == "POST":
        note.delete()
        return redirect("notes-list", user_id=user.id)
    return render(request, "note_confirm_delete.html", {"note": note, "user": user})


def logout_view(request):
    if request.method == "POST":
        request.session.flush()
        return redirect('login')
    return render(request, "logout_confirm.html")