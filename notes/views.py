from django.shortcuts import render, redirect
from users.models import User
from labels.models import Label
from .models import Note
from .forms import NoteForm


def notes_list(request, user_id):
    user = User.objects.get(pk=user_id)
    labels = Label.objects.filter(user=user).order_by("name")
    selected_label_id = request.GET.get("label")
    notes = Note.objects.filter(user=user).order_by("-created_at")
    if selected_label_id:
        notes = notes.filter(label_id=selected_label_id)
    return render(
        request,
        "notes_list.html",
        {
            "user": user,
            "notes": notes,
            "labels": labels,
            "selected_label_id": selected_label_id,
        },
    )


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

