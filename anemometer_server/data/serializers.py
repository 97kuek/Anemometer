from rest_framework import serializers
from .models import Data

class UseData(serializers.ModelSerializer):
    class Meta:
        model=Data
        fields='__all__'