from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
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


def get_element_from_path(path: str) -> str | None:
    """Определить элемент по URL (по префиксу пути)"""
    path = path.rstrip('/').lstrip('/')
    parts = path.split('/')

    if not parts:
        return None

    # Упрощённый парсинг: берём первые два сегмента
    # /api/v1/users/ → users
    # /api/v1/products/123 → products
    if parts[0] in ('api', 'v1', 'v2'):
        if len(parts) >= 2:
            return parts[1]  # users, products, shops, orders, etc.

    # Для /users/, /products/ и т.д.
    if len(parts) > 0:
        return parts[0]
    return None


def get_permission_type_from_method(method: str) -> str | None:
    """Сопоставление HTTP-метода с типом разрешения"""
    mapping = {
        'GET': 'read',
        'POST': 'create',
        'PUT': 'update',
        'PATCH': 'update',
        'DELETE': 'delete',
    }
    return mapping.get(method.upper())


def build_expected_permission(element: str, method: str) -> str | None:
    """Составить ожидаемый codename разрешения"""
    element_map = {
        'users': 'customuser',
        'products': 'product',
        'shops': 'shop',
        'orders': 'order',
        'access_rules': 'accessrule',
    }

    # Учитываем, что некоторые модели могут называться иначе (например, Product → product)
    codename_elem = element_map.get(element, element.lower())

    perm_type = get_permission_type_from_method(method)
    if not perm_type or not codename_elem:
        return None

    # Например: 'read_customuser', 'update_product'
    return f'{perm_type}_{codename_elem}'


def check_permission(user, expected_codename: str) -> bool:
    """
    Проверка разрешения:
    - если user is AnonymousUser → False (401)
    - если user.is_staff (админ Django) → True
    - иначе через user.has_perm()
    """
    if not user or not user.is_authenticated:
        return False

    # Админы (is_staff) имеют доступ по умолчанию (можно заменить на user.has_role('Админ'))
    if user.is_staff:
        return True

    # Проверяем через стандартный механизм Django
    return user.has_perm(f'auth.{expected_codename}')


class APIMiddleware:
    """Middleware для API-аутентификации и авторизации"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем для админки — она будет использовать стандартный Django middleware
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # Аутентификация через сессию
        request.user = SimpleLazyObject(lambda: get_user(request))

        # 🔐 Авторизация: проверяем права только для не-админок и не-статики
        if not request.path.startswith(('/static/', '/media/', '/health')):
            self._enforce_permission(request)

        return self.get_response(request)

    def _enforce_permission(self, request):
        """Проверка прав доступа к ресурсу (если требует метод)"""
        # ✅ Для GET, POST, PUT, PATCH, DELETE — проверяем разрешение
        if request.method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
            element = get_element_from_path(request.path)
            if element and element not in ('auth', 'users'):  # /users/ — специальный случай (свой аккаунт)
                expected_perm = build_expected_permission(element, request.method)
                if expected_perm:
                    if not check_permission(request.user, expected_perm):
                        # Возвращаем 403 Forbidden — пользователь не авторизован на этот ресурсе
                        return JsonResponse(
                            {'error': 'Forbidden', 'detail': f'Missing permission: {expected_perm}'},
                            status=403
                        )

            # ✅ Специальный случай: доступ к /users/{id}/ — только к своему профилю
            elif element == 'users':
                path_parts = request.path.rstrip('/').split('/')
                if len(path_parts) > 2 and path_parts[-1].isdigit():
                    user_id = int(path_parts[-1])
                    if request.user.is_authenticated and request.user.id != user_id:
                        # Пользователь пытается получить данные другого пользователя
                        expected_perm = 'read_customuser'
                        if not check_permission(request.user, expected_perm):
                            return JsonResponse(
                                {'error': 'Forbidden', 'detail': 'You can access only your profile'},
                                status=403
                            )

