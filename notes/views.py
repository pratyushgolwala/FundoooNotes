from django.shortcuts import render, redirect
from django.db import models
from django.core.paginator import Paginator
from users.models import User
from labels.models import Label
from .models import Note
from .forms import NoteForm


def notes_list(request, user_id):
    user = User.objects.get(pk=user_id)
    labels = Label.objects.filter(user=user).order_by("name")
    
    # Start with all notes for the user
    notes = Note.objects.filter(user=user)
    
    # Search filter
    search_query = request.GET.get("search", "")
    if search_query:
        notes = notes.filter(
            models.Q(title__icontains=search_query) |
            models.Q(content__icontains=search_query)
        )
    
    # Pin filter
    pin_filter = request.GET.get("pin")
    if pin_filter and pin_filter.lower() == "true":
        notes = notes.filter(is_pinned=True)
    
    # Archive filter
    archive_filter = request.GET.get("archive")
    if archive_filter and archive_filter.lower() == "true":
        notes = notes.filter(is_archived=True)
    else:
        # By default, don't show archived notes unless explicitly viewing them
        if not archive_filter:
            notes = notes.filter(is_archived=False)
    
    # Label filter
    selected_label_id = request.GET.get("label")
    if selected_label_id:
        notes = notes.filter(label_id=selected_label_id)
    
    # Color filter
    color_filter = request.GET.get("color")
    if color_filter:
        notes = notes.filter(color=color_filter)
    
    # Sorting: Pinned notes first, then by creation date
    notes = notes.order_by("-is_pinned", "-created_at")
    
    # Pagination: 6 notes per page
    paginator = Paginator(notes, 6)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    
    return render(
        request,
        "notes_list.html",
        {
            "user": user,
            "notes": page_obj,
            "page_obj": page_obj,
            "labels": labels,
            "selected_label_id": selected_label_id,
            "selected_search": search_query,
            "selected_pin": pin_filter,
            "selected_archive": archive_filter,
        },
    )


def note_create(request, user_id):
    user = User.objects.get(pk=user_id)
    form = NoteForm(request.POST or None, user=user)
    if request.method == "POST" and form.is_valid():
        note = form.save(commit=False)
        note.user = user
        note.save()
        return redirect("notes-list", user_id=user.pk)
    return render(request, "note_form.html", {"form": form, "user": user})


def note_update(request, user_id, note_id):
    user = User.objects.get(pk=user_id)
    note = Note.objects.get(pk=note_id, user=user)
    form = NoteForm(request.POST or None, instance=note, user=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("notes-list", user_id=user.pk)
    return render(request, "note_form.html", {"form": form, "user": user, "note": note})


def note_delete(request, user_id, note_id):
    user = User.objects.get(pk=user_id)
    note = Note.objects.get(pk=note_id, user=user)
    if request.method == "POST":
        note.is_archived = True
        note.save()
        return redirect("notes-list", user_id=user.pk)
    return render(request, "note_confirm_delete.html", {"note": note, "user": user, "action": "archive"})


def note_unarchive(request, user_id, note_id):
    user = User.objects.get(pk=user_id)
    note = Note.objects.get(pk=note_id, user=user)
    if request.method == "POST":
        note.is_archived = False
        note.save()
        return redirect(f"/users/{user.pk}/notes/?archive=true")
    return render(request, "note_confirm_delete.html", {"note": note, "user": user, "action": "unarchive"})


def note_permanent_delete(request, user_id, note_id):
    user = User.objects.get(pk=user_id)
    note = Note.objects.get(pk=note_id, user=user)
    if request.method == "POST":
        note.delete()
        return redirect(f"/users/{user.pk}/notes/?archive=true")
    return render(request, "note_confirm_delete.html", {"note": note, "user": user, "action": "delete"})


def note_toggle_pin(request, user_id, note_id):
    """Toggle pin status of a note"""
    user = User.objects.get(pk=user_id)
    note = Note.objects.get(pk=note_id, user=user)
    if request.method == "POST":
        note.is_pinned = not note.is_pinned
        note.save()
        # Redirect back to the current page
        return redirect(request.META.get('HTTP_REFERER', f'/users/{user.pk}/notes/'))
    return redirect(request.META.get('HTTP_REFERER', f'/users/{user.pk}/notes/'))

