from django.shortcuts import render, redirect
from users.models import User
from .models import Label
from .forms import LabelForm


def labels_list(request, user_id):
    user = User.objects.get(pk=user_id)
    labels = Label.objects.filter(user=user).order_by("name")
    return render(request, "labels_list.html", {"user": user, "labels": labels})


def label_create(request, user_id):
    user = User.objects.get(pk=user_id)
    form = LabelForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        label = form.save(commit=False)
        label.user = user
        label.save()
        return redirect("labels-list", user_id=user.id)
    return render(request, "label_form.html", {"form": form, "user": user})


def label_update(request, user_id, label_id):
    user = User.objects.get(pk=user_id)
    label = Label.objects.get(pk=label_id, user=user)
    form = LabelForm(request.POST or None, instance=label)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("labels-list", user_id=user.id)
    return render(request, "label_form.html", {"form": form, "user": user, "label": label})


def label_delete(request, user_id, label_id):
    user = User.objects.get(pk=user_id)
    label = Label.objects.get(pk=label_id, user=user)
    if request.method == "POST":
        label.delete()
        return redirect("labels-list", user_id=user.id)
    return render(request, "label_confirm_delete.html", {"label": label, "user": user})

