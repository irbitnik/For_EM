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
        'customuser': 'customuser',
        'users': 'customuser',
        'product': 'product',
        'products': 'product',
        'shop': 'shop',
        'shops': 'shop',
        'order': 'order',
        'orders': 'order',
        'accessrule': 'accessrule',
        'access_rules': 'accessrule',
        # Mock-элементы (не требуют разрешений)
        'mock': None,  # Mock-запросы не требуют проверки разрешений
    }

    codename_elem = element_map.get(element, element.lower())

    # Если элемент не требует разрешений (например, mock)
    if codename_elem is None:
        return None

    perm_type = get_permission_type_from_method(method)
    if not perm_type or not codename_elem:
        return None

    # Например: 'read_customuser', 'update_product'
    return f'{perm_type}_{codename_elem}'


def check_permission(user, expected_codename: str) -> bool:
    """
    Проверка разрешения:
    - если user is AnonymousUser → False
    - если user.is_staff (админ Django) → True
    - если user имеет роль 'Админ' → True
    - иначе через user.has_perm()
    """
    if not user or not user.is_authenticated:
        return False

    # Админы (is_staff или роль 'Админ') имеют доступ по умолчанию
    if user.is_staff:
        return True

    if hasattr(user, 'has_role') and user.has_role('Админ'):
        return True

    # Проверяем через стандартный механизм Django
    return user.has_perm(f'auth.{expected_codename}')


class PermissionEnforcer:
    """Унифицированный обработчик авторизации"""
    
    @staticmethod
    def check_access(request):
        """
        Централизованная проверка доступа.
        Возвращает (is_allowed, response)
        - (True, None) — доступ разрешен, продолжить обработку
        - (False, response) — доступ запрещен, вернуть response
        """
        from django.contrib.auth.models import AnonymousUser
        
        # Пропускаем проверку для админки и статики
        if request.path.startswith(('/admin/', '/static/', '/media/', '/health')):
            return True, None
        
        # Пропускаем проверку для эндпоинтов аутентификации
        if request.path.startswith(('/api/users/login/', '/api/users/register/', '/api/users/logout/')):
            return True, None

        # Проверка на аутентификацию
        user = request.user
        
        # Если пользователь не авторизован → 401
        if not user or user.is_anonymous or not user.is_authenticated:
            return False, JsonResponse(
                {'error': 'Unauthorized', 'detail': 'Authentication required'},
                status=401
            )

        # Для GET, POST, PUT, PATCH, DELETE — проверяем разрешение
        if request.method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
            element = get_element_from_path(request.path)
            
            # Mock-элементы не требуют проверки разрешений (для демонстрации)
            if element == 'mock':
                return True, None
            
            # Специальные случаи, которые не требуют проверки разрешений
            if not element or element in ('auth', 'users', 'auth_system'):
                return True, None
            
            expected_perm = build_expected_permission(element, request.method)
            if expected_perm:
                if not check_permission(user, expected_perm):
                    # Возвращаем 403 Forbidden — пользователь не имеет прав
                    return False, JsonResponse(
                        {'error': 'Forbidden', 'detail': f'Missing permission: {expected_perm}'},
                        status=403
                    )

            # Специальный случай: доступ к /users/{id}/ — только к своему профилю
            elif element == 'users':
                path_parts = request.path.rstrip('/').split('/')
                if len(path_parts) > 2 and path_parts[-1].isdigit():
                    user_id = int(path_parts[-1])
                    if user.id != user_id:
                        # Пользователь пытается получить данные другого пользователя
                        expected_perm = 'read_customuser'
                        if not check_permission(user, expected_perm):
                            return False, JsonResponse(
                                {'error': 'Forbidden', 'detail': 'You can access only your profile'},
                                status=403
                            )

        return True, None


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

        # Авторизация: проверяем права
        is_allowed, response = PermissionEnforcer.check_access(request)
        if not is_allowed:
            return response

        return self.get_response(request)
