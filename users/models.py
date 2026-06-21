from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Кастомная модель пользователя"""
    # Убираем username — мы будем использовать email как логин
    username = None

    # Добавляем новые обязательные поля
    email = models.EmailField(unique=True, verbose_name='Email')
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=150, verbose_name='Отчество', blank=True)

    # Добавляем is_active для мягких удалений (Шаг 10)
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    # Ставим email как поле для входа (USERNAME_FIELD)
    USERNAME_FIELD = 'email'

    # Указываем обязательные поля при создании через createsuperuser
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()
