from django import forms
from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "content", "label", "color", "is_pinned", "is_archived"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Note title",
            }),
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Note content",
                "rows": 10,
            }),
            "label": forms.Select(attrs={
                "class": "form-control",
            }),
            "color": forms.TextInput(attrs={
                "type": "color",
                "class": "form-control",
                "style": "height: 40px;",
            }),
            "is_pinned": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "is_archived": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }
