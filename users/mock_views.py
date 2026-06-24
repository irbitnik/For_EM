"""Mock-контроллеры для демонстрации работы системы авторизации"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from .middleware import (
    check_permission
)


# ============================================================================
# MOCK-ДАННЫЕ (в памяти, без БД)
# ============================================================================

# Товары
PRODUCTS = [
    {"id": 1, "name": "Смартфон iPhone 15 Pro", "price": 129999, "category": "Электроника"},
    {"id": 2, "name": "Ноутбук MacBook Air M3", "price": 159999, "category": "Электроника"},
    {"id": 3, "name": "Наушники AirPods Pro", "price": 25999, "category": "Аксессуары"},
    {"id": 4, "name": "Умные часы Apple Watch Ultra", "price": 99999, "category": "Аксессуары"},
    {"id": 5, "name": "Кейс для iPhone", "price": 2999, "category": "Аксессуары"},
]

# Магазины
SHOPS = [
    {"id": 1, "name": "Apple Store Марет", "address": "г. Москва, ул. Арбат, 25", "rating": 4.8},
    {"id": 2, "name": "Apple Store Пятницкая", "address": "г. Москва, ул. Пятницкая, 10", "rating": 4.9},
    {"id": 3, "name": "Ситилинк Калужская", "address": "г. Москва, ул. Калужская, 1", "rating": 4.7},
    {"id": 4, "name": "М.Видео Триумф", "address": "г. Москва, ш. Энтузиастов, 80", "rating": 4.5},
]

# Заказы
ORDERS = [
    {"id": 1, "user_id": 1, "user_name": "Администратор Системы", "products": [1, 3], "total": 155998, "status": "confirmed"},
    {"id": 2, "user_id": 2, "user_name": "Менеджер Торговли", "products": [2], "total": 159999, "status": "processing"},
    {"id": 3, "user_id": 3, "user_name": "Обычный Пользователь", "products": [5], "total": 2999, "status": "delivered"},
]

# Правила доступа (для расширенных сценариев)
ACCESS_RULES = [
    {"id": 1, "name": "Админ-доступ ко всем", "permissions": ["read", "create", "update", "delete"], "applies_to": ["products", "shops", "orders", "access_rules"]},
    {"id": 2, "name": "Менеджер-чтение и обновление", "permissions": ["read", "update"], "applies_to": ["products", "shops", "orders"]},
    {"id": 3, "name": "Пользователь-только чтение", "permissions": ["read"], "applies_to": ["products", "shops"]},
    {"id": 4, "name": "Гость-публичный доступ", "permissions": ["read"], "applies_to": ["products"]},
]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def authenticate_request(request):
    """
    Проверяет аутентификацию пользователя.
    Возвращает (user, error_response):
    - (user, None) — пользователь авторизован
    - (None, error_response) — ошибка (401 или 403)
    """
    # Проверка на анонимного пользователя
    user = getattr(request, 'user', None)
    
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return None, JsonResponse(
            {'error': 'Unauthorized', 'detail': 'Authentication required'},
            status=401
        )
    
    return user, None


def check_resource_access(request, resource_type: str, permission_type: str = None):
    """
    Проверяет доступ пользователя к ресурсу.
    Возвращает (is_allowed, error_response):
    - (True, None) — доступ разрешен
    - (False, error_response) — ошибка (403)
    
    Args:
        request: HTTP request
        resource_type: Тип ресурса (products, shops, orders, access_rules, dashboard)
        permission_type: Тип операции (read, create, update, delete)
    """
    user = getattr(request, 'user', None)
    
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False, JsonResponse(
            {'error': 'Unauthorized', 'detail': 'Authentication required'},
            status=401
        )
    
    # Админы (is_staff или роль 'Админ') имеют полный доступ
    if user.is_staff:
        return True, None
    
    if hasattr(user, 'has_role') and user.has_role('Админ'):
        return True, None
    
    # Сопоставление ресурсов и требуемых разрешений
    resource_permission_map = {
        'products': 'product',
        'shops': 'shop',
        'orders': 'order',
        'access_rules': 'accessrule',
        'dashboard': 'dashboard',
    }
    
    codename = resource_permission_map.get(resource_type)
    if not codename:
        return False, JsonResponse(
            {'error': 'Forbidden', 'detail': f'Resource {resource_type} is not accessible'},
            status=403
        )
    
    # Проверяем через has_role (так как разрешения могут не находиться через has_perm)
    if hasattr(user, 'has_role'):
        # Гость не может читать orders, access_rules, dashboard
        if user.has_role('Гость'):
            if resource_type in ['orders', 'access_rules', 'dashboard']:
                return False, JsonResponse(
                    {'error': 'Forbidden', 'detail': f'Гость не имеет доступа к {resource_type}'},
                    status=403
                )
        
        # Пользователь не может читать access_rules и dashboard
        if user.has_role('Пользователь'):
            if resource_type in ['access_rules', 'dashboard']:
                return False, JsonResponse(
                    {'error': 'Forbidden', 'detail': f'Пользователь не имеет доступа к {resource_type}'},
                    status=403
                )
    
    # Всё в порядке, доступ разрешен
    return True, None


# ============================================================================
# MOCK-VIEWS
# ============================================================================

@api_view(['GET'])
def mock_products_list(request):
    """Получить список всех товаров"""
    # Проверка аутентификации
    user, error = authenticate_request(request)
    if error:
        return error
    
    # Проверка доступа к ресурсу (требуется разрешение read_product)
    is_allowed, error = check_resource_access(request, 'products', 'read')
    if not is_allowed:
        return error
    
    return Response(PRODUCTS)


@api_view(['GET'])
def mock_product_detail(request, pk):
    """Получить товар по ID"""
    # Проверка аутентификации
    user, error = authenticate_request(request)
    if error:
        return error
    
    # Проверка доступа к ресурсу (требуется разрешение read_product)
    is_allowed, error = check_resource_access(request, 'products', 'read')
    if not is_allowed:
        return error
    
    try:
        product = next(p for p in PRODUCTS if p['id'] == pk)
        return Response(product)
    except StopIteration:
        return Response({'error': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def mock_products_by_category(request, category):
    """Получить товары по категории"""
    # Проверка аутентификации
    user, error = authenticate_request(request)
    if error:
        return error
    
    # Проверка доступа к ресурсу (требуется разрешение read_product)
    is_allowed, error = check_resource_access(request, 'products', 'read')
    if not is_allowed:
        return error
    
    filtered = [p for p in PRODUCTS if p['category'].lower() == category.lower()]
    return Response(filtered)


@api_view(['GET'])
def mock_shops_list(request):
    """Получить список всех магазинов"""
    # Проверка аутентификации
    user, error = authenticate_request(request)
    if error:
        return error
    
    # Проверка доступа к ресурсу (требуется разрешение read_shop)
    is_allowed, error = check_resource_access(request, 'shops', 'read')
    if not is_allowed:
        return error
    
    return Response(SHOPS)


@api_view(['GET'])
def mock_shop_detail(request, pk):
    """Получить магазин по ID"""
    # Проверка аутентификации
    user, error = authenticate_request(request)
    if error:
        return error
    
    # Проверка доступа к ресурсу (требуется разрешение read_shop)
    is_allowed, error = check_resource_access(request, 'shops', 'read')
    if not is_allowed:
        return error
    
    try:
        shop = next(s for s in SHOPS if s['id'] == pk)
        return Response(shop)
    except StopIteration:
        return Response({'error': 'Магазин не найден'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def mock_orders_list(request):
    """Получить список всех заказов"""
    # Проверка аутентификации
    user, error = authenticate_request(request)
    if error:
        return error
    
    # Проверка доступа к ресурсу (требуется разрешение read_order)
    is_allowed, error = check_resource_access(request, 'orders', 'read')
    if not is_allowed:
        return error
    
    return Response(ORDERS)


@api_view(['GET'])
def mock_order_detail(request, pk):
    """Получить заказ по ID"""
    # Проверка аутентификации
    user, error = authenticate_request(request)
    if error:
        return error
    
    # Проверка доступа к ресурсу (требуется разрешение read_order)
    is_allowed, error = check_resource_access(request, 'orders', 'read')
    if not is_allowed:
        return error
    
    try:
        order = next(o for o in ORDERS if o['id'] == pk)
        return Response(order)
    except StopIteration:
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def mock_access_rules_list(request):
    """Получить список всех правил доступа"""
    # Проверка аутентификации
    user, error = authenticate_request(request)
    if error:
        return error
    
    # Проверка доступа к ресурсу (требуется разрешение read_accessrule)
    is_allowed, error = check_resource_access(request, 'access_rules', 'read')
    if not is_allowed:
        return error
    
    return Response(ACCESS_RULES)


@api_view(['GET'])
def mock_dashboard(request):
    """Получить сводную панель данных (демонстрация прав)"""
    # Проверка аутентификации
    user, error = authenticate_request(request)
    if error:
        return error
    
    # Проверка доступа к ресурсу (требуется разрешение read_dashboard)
    is_allowed, error = check_resource_access(request, 'dashboard', 'read')
    if not is_allowed:
        return error
    
    dashboard_data = {
        'products_count': len(PRODUCTS),
        'shops_count': len(SHOPS),
        'orders_count': len(ORDERS),
        'total_revenue': sum(p['price'] for p in PRODUCTS),
        'recent_orders': ORDERS[-3:],  # Последние 3 заказа
    }
    return Response(dashboard_data)
