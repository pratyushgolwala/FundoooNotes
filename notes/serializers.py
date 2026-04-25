from rest_framework import serializers
from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    label_id = serializers.PrimaryKeyRelatedField(
        source="label",
        queryset=Note._meta.get_field('label').related_model.objects.all(), #type:ignore
        allow_null=True,
        required=False,
    )
    label_name = serializers.CharField(source="label.name", read_only=True)

    class Meta:
        model = Note
        fields = [
            "id", "title", "content", "label_id", "label_name", 
            "created_at", "updated_at", "is_archived", "is_pinned", "color"
        ]
