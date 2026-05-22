from django import forms
from .models import Note
from labels.models import Label


class NoteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['labels'].queryset = Label.objects.filter(user=self.user)

    class Meta:
        model = Note
        fields = ["title", "content", "labels", "color", "is_pinned", "is_archived"]
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
            "labels": forms.CheckboxSelectMultiple(attrs={
                "class": "form-check-input",
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
