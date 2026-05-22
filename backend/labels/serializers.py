from rest_framework import serializers
from .models import Label


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['id', 'name', 'user']
        read_only_fields = ['id', 'user']