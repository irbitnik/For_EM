from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Session


class CustomUserCreationForm(UserCreationForm):
    """Форма создания пользователя с bcrypt хешированием"""
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'middle_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Убедимся, что пароль захеширован через bcrypt
        if not user.password.startswith('bcrypt$'):
            from users.models import CustomUser
            user = CustomUser.objects.create_user(
                email=user.email,
                password=self.cleaned_data['password1'],
                first_name=user.first_name,
                last_name=user.last_name,
                middle_name=user.middle_name
            )
            return user
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """Форма изменения пользователя"""
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = '__all__'


@admin.register(CustomUser)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'middle_name')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    filter_horizontal = ('groups', 'user_permissions')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'created_at', 'expires_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['session_id', 'user__email']
    readonly_fields = ['session_id', 'created_at']
