from django.urls import path
from . import mock_views

urlpatterns = [
    # Товары
    path('products/', mock_views.mock_products_list, name='mock-products-list'),
    path('products/<int:pk>/', mock_views.mock_product_detail, name='mock-product-detail'),
    path('products/category/<str:category>/', mock_views.mock_products_by_category, name='mock-products-by-category'),
    
    # Магазины
    path('shops/', mock_views.mock_shops_list, name='mock-shops-list'),
    path('shops/<int:pk>/', mock_views.mock_shop_detail, name='mock-shop-detail'),
    
    # Заказы
    path('orders/', mock_views.mock_orders_list, name='mock-orders-list'),
    path('orders/<int:pk>/', mock_views.mock_order_detail, name='mock-order-detail'),
    
    # Правила доступа
    path('access-rules/', mock_views.mock_access_rules_list, name='mock-access-rules-list'),
    
    # Панель управления
    path('dashboard/', mock_views.mock_dashboard, name='mock-dashboard'),
]
