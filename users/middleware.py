from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
from .models import Session


def get_user(request):
    """Получение пользователя из сессии (только для API)"""
    if not hasattr(request, '_cached_user'):
        session_id = request.COOKIES.get('session_id')

        if not session_id:
            request._cached_user = AnonymousUser()
        else:
            try:
                session = Session.objects.get(
                    session_id=session_id,
                    is_active=True
                )
                if session.is_expired():
                    session.is_active = False
                    session.save()
                    request._cached_user = AnonymousUser()
                else:
                    request._cached_user = session.user
            except Session.DoesNotExist:
                request._cached_user = AnonymousUser()

    return request._cached_user


class APIMiddleware:
    """Middleware только для API (не для админки)"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем для админки - она будет использовать стандартный Django middleware
        if request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # Для API эндпоинтов используем нашу систему сессий
        request.user = SimpleLazyObject(lambda: get_user(request))
        return self.get_response(request)
