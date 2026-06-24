"""Mock-контроллеры для демонстрации работы системы авторизации"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


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
# MOCK-VIEWS
# ============================================================================

@api_view(['GET'])
def mock_products_list(request):
    """Получить список всех товаров"""
    return Response(PRODUCTS)


@api_view(['GET'])
def mock_product_detail(request, pk):
    """Получить товар по ID"""
    try:
        product = next(p for p in PRODUCTS if p['id'] == pk)
        return Response(product)
    except StopIteration:
        return Response({'error': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def mock_products_by_category(request, category):
    """Получить товары по категории"""
    filtered = [p for p in PRODUCTS if p['category'].lower() == category.lower()]
    return Response(filtered)


@api_view(['GET'])
def mock_shops_list(request):
    """Получить список всех магазинов"""
    return Response(SHOPS)


@api_view(['GET'])
def mock_shop_detail(request, pk):
    """Получить магазин по ID"""
    try:
        shop = next(s for s in SHOPS if s['id'] == pk)
        return Response(shop)
    except StopIteration:
        return Response({'error': 'Магазин не найден'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def mock_orders_list(request):
    """Получить список всех заказов"""
    return Response(ORDERS)


@api_view(['GET'])
def mock_order_detail(request, pk):
    """Получить заказ по ID"""
    try:
        order = next(o for o in ORDERS if o['id'] == pk)
        return Response(order)
    except StopIteration:
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def mock_access_rules_list(request):
    """Получить список всех правил доступа"""
    return Response(ACCESS_RULES)


@api_view(['GET'])
def mock_dashboard(request):
    """Получить сводную панель данных (демонстрация прав)"""
    dashboard_data = {
        'products_count': len(PRODUCTS),
        'shops_count': len(SHOPS),
        'orders_count': len(ORDERS),
        'total_revenue': sum(p['price'] for p in PRODUCTS),
        'recent_orders': ORDERS[-3:],  # Последние 3 заказа
    }
    return Response(dashboard_data)
