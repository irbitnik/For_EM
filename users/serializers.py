from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth.models import Group


class RegisterSerializer(serializers.Serializer):
    """Сериализатор для регистрации"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    middle_name = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Валидация данных"""
        # Проверяем, что пароли совпадают
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают'})

        # Проверяем, что email уникален
        if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'Пользователь с таким email уже существует'})

        return attrs

    def create(self, validated_data):
        """Создание пользователя"""
        return CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            middle_name=validated_data.get('middle_name', '')
        )

class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'middle_name']
        read_only_fields = ['id', 'email']  # ID и email нельзя менять

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']