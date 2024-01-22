from .models import *
from rest_framework import serializers
 
 
class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = Teachers
        # Поля, которые мы сериализуем
        fields = "__all__"
 
class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = Applications
        # Поля, которые мы сериализуем
        fields = "__all__"
 
class ApplicationsteachersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicationsteachers
        fields = '__all__'