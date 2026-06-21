from django.utils.functional import SimpleLazyObject
from .models import Session  # Импортируем модель Session


def get_user(request):
    """Получение пользователя из сессии"""
    if not hasattr(request, '_cached_user'):
        session_id = request.COOKIES.get('session_id')

        if not session_id:
            request._cached_user = None
        else:
            try:
                session = Session.objects.get(
                    session_id=session_id,
                    is_active=True
                )
                # Проверяем, не истекла ли сессия
                if session.is_expired():
                    session.is_active = False
                    session.save()
                    request._cached_user = None
                else:
                    request._cached_user = session.user
            except Session.DoesNotExist:
                request._cached_user = None

    return request._cached_user


class AuthenticationMiddleware:
    """Middleware для аутентификации по cookie-сессии"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ленивая привязка пользователя (чтобы не вызывать БД лишний раз)
        request.user = SimpleLazyObject(lambda: get_user(request))
        return self.get_response(request)