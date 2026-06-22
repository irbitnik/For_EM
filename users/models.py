import bcrypt
import uuid
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """Менеджер кастомной модели пользователя"""

    def create_user(self, email, password=None, **extra_fields):
        """Создание пользователя с хешированным паролем"""
        if not email:
            raise ValueError('Email обязателен')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        # ХЕШИРУЕМ ПАРОЛЬ ЧЕРЕЗ BCRYPT
        if password:
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt)
            user.password = hashed_password.decode('utf-8')
        else:
            user.password = ''

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Кастомная модель пользователя"""
    username = None
    email = models.EmailField(unique=True, verbose_name='Email')
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=150, verbose_name='Отчество', blank=True)
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_staff = models.BooleanField(default=False, verbose_name='Может входить в админку')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    def check_password(self, raw_password):
        """Проверка пароля через bcrypt"""
        try:
            password_bytes = raw_password.encode('utf-8')
            stored_hash = self.password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, stored_hash)
        except Exception:
            return False


class Session(models.Model):
    """Модель сессии для хранения cookie-сессий"""
    user = models.ForeignKey(
        CustomUser,  # 🟢 Связь с пользователем
        on_delete=models.CASCADE,  # При удалении пользователя — удаляем все его сессии
        verbose_name='Пользователь'
    )
    session_id = models.CharField(
        max_length=36,  # UUID4 = 36 символов
        unique=True,    # Обязательно для идентификации
        verbose_name='ID сессии'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    expires_at = models.DateTimeField(verbose_name='Истекает')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Сессия'
        verbose_name_plural = 'Сессии'

    def __str__(self):
        return f"Сессия {self.user} (до {self.expires_at.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        """Генерация session_id при первом сохранении (если не задан)"""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())  # 🔑 Генерируем UUID4
        super().save(*args, **kwargs)

    def is_expired(self):
        """Проверка, истекла ли сессия"""
        return timezone.now() > self.expires_at

    @classmethod
    def create_session(cls, user, expires_in_hours=24):
        """Создание новой сессии (удобный метод для login)"""
        session = cls(
            user=user,
            expires_at=timezone.now() + timedelta(hours=expires_in_hours)
        )
        session.save()
        return session