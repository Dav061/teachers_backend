from .models import *
from rest_framework import serializers
 
 
class UserSerializer(serializers.ModelSerializer):
    is_moderator = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = Users
        fields = ['email', 'password', 'is_moderator'] 

class UserAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['email']

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = Teachers
        # Поля, которые мы сериализуем
        fields = "__all__"
 
class ApplicationSerializer(serializers.ModelSerializer):
    customer = UserAppSerializer(read_only=True)
    moderator = UserAppSerializer(read_only=True)
    class Meta:
        # Модель, которую мы сериализуем
        model = Applications
        # Поля, которые мы сериализуем
        fields = "__all__"
 
class ApplicationsteachersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicationsteachers
        fields = '__all__'