from functools import wraps
from django.http import JsonResponse


def require_role(role_name: str):
    """
    Декоратор, требующий наличия у пользователя указанной роли (по имени группы).

    Пример:
        @require_role('Админ')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Проверка авторизации
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return JsonResponse({'error': 'Unauthorized'}, status=401)

            # Проверка наличия роли
            if not request.user.has_role(role_name):
                return JsonResponse({'error': 'Forbidden'}, status=403)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def require_permission(permission_codename: str):
    """
    Декоратор, требующий наличия у пользователя указанного разрешения (по codename).

    Пример:
        @require_permission('read_customuser')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Проверка авторизации
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return JsonResponse({'error': 'Unauthorized'}, status=401)

            # Проверка наличия разрешения
            if not request.user.has_permission(permission_codename):
                return JsonResponse({'error': 'Forbidden'}, status=403)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator