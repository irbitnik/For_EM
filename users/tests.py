from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model


class MockViewsSimpleTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        try:
            cls.admin_group = Group.objects.get(name='Админ')
        except Group.DoesNotExist:
            cls.admin_group = Group.objects.create(name='Админ')
        try:
            cls.manager_group = Group.objects.get(name='Менеджер')
        except Group.DoesNotExist:
            cls.manager_group = Group.objects.create(name='Менеджер')
        try:
            cls.user_group = Group.objects.get(name='Пользователь')
        except Group.DoesNotExist:
            cls.user_group = Group.objects.create(name='Пользователь')
        try:
            cls.guest_group = Group.objects.get(name='Гость')
        except Group.DoesNotExist:
            cls.guest_group = Group.objects.create(name='Гость')


        cls.admin, _ = get_user_model().objects.get_or_create(
            email='admin@example.com',
            defaults={
                'first_name': 'Админ',
                'last_name': 'Админов',
                'is_staff': True,
                'is_active': True
            }
        )
        cls.admin.set_password('123456')
        cls.admin.groups.add(cls.admin_group)
        cls.admin.save()

        cls.manager, _ = get_user_model().objects.get_or_create(
            email='manager@example.com',
            defaults={
                'first_name': 'Менеджер',
                'last_name': 'Менеджеров',
                'is_staff': False,
                'is_active': True
            }
        )
        cls.manager.set_password('123456')
        cls.manager.groups.add(cls.manager_group)
        cls.manager.save()

        cls.user, _ = get_user_model().objects.get_or_create(
            email='user@example.com',
            defaults={
                'first_name': 'Пользователь',
                'last_name': 'Пользователев',
                'is_staff': False,
                'is_active': True
            }
        )
        cls.user.set_password('123456')
        cls.user.groups.add(cls.user_group)
        cls.user.save()

        cls.guest, _ = get_user_model().objects.get_or_create(
            email='guest@example.com',
            defaults={
                'first_name': 'Гость',
                'last_name': 'Гостев',
                'is_staff': False,
                'is_active': True
            }
        )
        cls.guest.set_password('123456')
        cls.guest.groups.add(cls.guest_group)
        cls.guest.save()

        # Назначаем разрешения группам

        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType


        content_type, _ = ContentType.objects.get_or_create(
            model='Mock',
            app_label='users'
        )


        read_product_perm, _ = Permission.objects.get_or_create(
            codename='read_product',
            defaults={'name': 'Чтение товаров', 'content_type': content_type}
        )
        read_shop_perm, _ = Permission.objects.get_or_create(
            codename='read_shop',
            defaults={'name': 'Чтение магазинов', 'content_type': content_type}
        )
        read_order_perm, _ = Permission.objects.get_or_create(
            codename='read_order',
            defaults={'name': 'Чтение заказов', 'content_type': content_type}
        )
        read_accessrule_perm, _ = Permission.objects.get_or_create(
            codename='read_accessrule',
            defaults={'name': 'Чтение правил доступа', 'content_type': content_type}
        )
        read_dashboard_perm, _ = Permission.objects.get_or_create(
            codename='read_dashboard',
            defaults={'name': 'Чтение дашборда', 'content_type': content_type}
        )

        # Гость: только чтение товаров и магазинов
        cls.guest_group.permissions.add(read_product_perm, read_shop_perm)

        # Пользователь: чтение товаров, магазинов, заказов
        cls.user_group.permissions.add(
            read_product_perm, read_shop_perm, read_order_perm
        )

        # Менеджер: все чтения
        cls.manager_group.permissions.add(
            read_product_perm, read_shop_perm, read_order_perm,
            read_accessrule_perm, read_dashboard_perm
        )

        # Админ: все разрешения
        cls.admin_group.permissions.set(Permission.objects.all())

        # Создаем сессии
        from users.models import Session
        cls.admin_session, _ = Session.objects.get_or_create(
            user=cls.admin,
            session_id='admin-session-id',
            defaults={'expires_at': timezone.now() + timedelta(hours=24)}
        )
        cls.manager_session, _ = Session.objects.get_or_create(
            user=cls.manager,
            session_id='manager-session-id',
            defaults={'expires_at': timezone.now() + timedelta(hours=24)}
        )
        cls.user_session, _ = Session.objects.get_or_create(
            user=cls.user,
            session_id='user-session-id',
            defaults={'expires_at': timezone.now() + timedelta(hours=24)}
        )
        cls.guest_session, _ = Session.objects.get_or_create(
            user=cls.guest,
            session_id='guest-session-id',
            defaults={'expires_at': timezone.now() + timedelta(hours=24)}
        )

    def setUp(self):
        self.client = Client()
        self.base_url = '/api/mock'
        # Копируем ссылки на сессии в instance variables для каждого теста
        self.admin_session = self.__class__.admin_session
        self.manager_session = self.__class__.manager_session
        self.user_session = self.__class__.user_session
        self.guest_session = self.__class__.guest_session

    def _login(self, user, session):
        """Установить cookie сессии"""
        self.client.cookies['session_id'] = session.session_id

    def _logout(self):
        """Удалить cookie"""
        self.client.cookies.clear()

    # ТЕСТЫ 401 Unauthorized (неавторизованный доступ)

    def test_401_no_session(self):
        """401: Запрос без cookie сессии"""
        self._logout()
        response = self.client.get(f'{self.base_url}/products/')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'Unauthorized')

    def test_401_invalid_session(self):
        """401: Запрос с невалидной cookie сессией"""
        self.client.cookies['session_id'] = 'invalid-session-id'
        response = self.client.get(f'{self.base_url}/products/')
        self.assertEqual(response.status_code, 401)

    def test_401_expired_session(self):
        """401: Запрос с истекшей сессией"""
        from users.models import Session
        expired = Session.objects.create(
            user=self.admin,
            session_id='expired-id',
            expires_at=timezone.now() - timedelta(hours=1),
            is_active=True
        )
        self._login(self.admin, expired)
        response = self.client.get(f'{self.base_url}/products/')
        self.assertEqual(response.status_code, 401)
        expired.is_active = False
        expired.save()

    # ТЕСТЫ 200 Success (доступ авторизованных пользователей)

    def test_200_admin_products(self):
        """200: Админ получает список товаров"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)

    def test_200_manager_products(self):
        """200: Менеджер получает список товаров"""
        self._login(self.manager, self.manager_session)
        response = self.client.get(f'{self.base_url}/products/')
        self.assertEqual(response.status_code, 200)

    def test_200_user_products(self):
        """200: Обычный пользователь получает список товаров"""
        self._login(self.user, self.user_session)
        response = self.client.get(f'{self.base_url}/products/')
        self.assertEqual(response.status_code, 200)

    def test_200_guest_products(self):
        """200: Гость получает список товаров"""
        self._login(self.guest, self.guest_session)
        response = self.client.get(f'{self.base_url}/products/')
        self.assertEqual(response.status_code, 200)

    def test_200_admin_shops(self):
        """200: Админ получает список магазинов"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/shops/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)

    def test_200_guest_shops(self):
        """200: Гость получает список магазинов"""
        self._login(self.guest, self.guest_session)
        response = self.client.get(f'{self.base_url}/shops/')
        self.assertEqual(response.status_code, 200)

    def test_200_admin_orders(self):
        """200: Админ получает список заказов"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/orders/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

    def test_200_manager_orders(self):
        """200: Менеджер получает список заказов"""
        self._login(self.manager, self.manager_session)
        response = self.client.get(f'{self.base_url}/orders/')
        self.assertEqual(response.status_code, 200)

    def test_200_user_orders(self):
        """200: Обычный пользователь получает список заказов"""
        self._login(self.user, self.user_session)
        response = self.client.get(f'{self.base_url}/orders/')
        self.assertEqual(response.status_code, 200)

    def test_200_admin_access_rules(self):
        """200: Админ получает правила доступа"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/access-rules/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 4)

    def test_200_manager_access_rules(self):
        """200: Менеджер получает правила доступа"""
        self._login(self.manager, self.manager_session)
        response = self.client.get(f'{self.base_url}/access-rules/')
        self.assertEqual(response.status_code, 200)

    def test_200_admin_dashboard(self):
        """200: Админ получает дашборд"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/dashboard/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('products_count', data)
        self.assertEqual(data['products_count'], 5)

    def test_200_manager_dashboard(self):
        """200: Менеджер получает дашборд"""
        self._login(self.manager, self.manager_session)
        response = self.client.get(f'{self.base_url}/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_200_user_dashboard(self):
        """200: Обычный пользователь получает дашборд"""
        self._login(self.user, self.user_session)
        response = self.client.get(f'{self.base_url}/dashboard/')
        # Пользователь не имеет доступа к dashboard - получит 403
        # Это проверка 403, а не 200
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'Forbidden')

    # ТЕСТЫ 401 Unauthorized (дополнительные проверки)

    def test_401_invalid_session_for_shops(self):
        """401: Невалидная сессия для shops"""
        self.client.cookies['session_id'] = 'invalid-shops-id'
        response = self.client.get(f'{self.base_url}/shops/')
        self.assertEqual(response.status_code, 401)

    def test_401_invalid_session_for_orders(self):
        """401: Невалидная сессия для orders"""
        self.client.cookies['session_id'] = 'invalid-orders-id'
        response = self.client.get(f'{self.base_url}/orders/')
        self.assertEqual(response.status_code, 401)

    def test_401_invalid_session_for_dashboard(self):
        """401: Невалидная сессия для dashboard"""
        self.client.cookies['session_id'] = 'invalid-dashboard-id'
        response = self.client.get(f'{self.base_url}/dashboard/')
        self.assertEqual(response.status_code, 401)

    def test_401_expired_session_for_orders(self):
        """401: Истекшая сессия для orders"""
        from users.models import Session
        expired = Session.objects.create(
            user=self.admin,
            session_id='expired-orders-id',
            expires_at=timezone.now() - timedelta(hours=1),
            is_active=True
        )
        self._login(self.admin, expired)
        response = self.client.get(f'{self.base_url}/orders/')
        self.assertEqual(response.status_code, 401)
        expired.is_active = False
        expired.save()

    def test_401_no_session_for_access_rules(self):
        """401: Без сессии для access-rules"""
        self._logout()
        response = self.client.get(f'{self.base_url}/access-rules/')
        self.assertEqual(response.status_code, 401)

    # ТЕСТЫ ДЛЯ БЕЗОПАСНОСТИ

    def test_all_mock_endpoints_require_auth(self):
        """401: Все mock-эндпоинты требуют аутентификации"""
        endpoints = [
            '/products/',
            '/products/1/',
            '/products/category/электроника/',
            '/shops/',
            '/shops/1/',
            '/orders/',
            '/orders/1/',
            '/access-rules/',
            '/dashboard/',
        ]

        self._logout()
        for endpoint in endpoints:
            response = self.client.get(f'{self.base_url}{endpoint}')
            self.assertEqual(
                response.status_code, 401,
                f'Эндпоинт {endpoint} должен вернуть 401 без аутентификации'
            )
            data = response.json()
            self.assertIn('error', data)
            self.assertIn('detail', data)

    # ТЕСТЫ ДЕТАЛЬНЫХ ОБЪЕКТОВ

    def test_200_product_detail(self):
        """200: Получение конкретного товара"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/products/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], 1)

    def test_404_product_not_found(self):
        """404: Товар не найден"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/products/999/')
        self.assertEqual(response.status_code, 404)

    def test_200_shop_detail(self):
        """200: Получение конкретного магазина"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/shops/1/')
        self.assertEqual(response.status_code, 200)

    def test_200_order_detail(self):
        """200: Получение конкретного заказа"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/orders/1/')
        self.assertEqual(response.status_code, 200)

    def test_200_products_by_category(self):
        """200: Фильтрация товаров по категории"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/products/category/электроника/')
        self.assertEqual(response.status_code, 200)
        for item in response.json():
            self.assertEqual(item['category'].lower(), 'электроника')

    # ПРОВЕРКА СТРУКТУРЫ ОТВЕТОВ

    def test_error_response_format(self):
        """Проверка формата ошибки 401"""
        self._logout()
        response = self.client.get(f'{self.base_url}/products/')
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('detail', data)
        self.assertEqual(data['error'], 'Unauthorized')

    def test_success_response_format(self):
        """Проверка формата успешного ответа"""
        self._login(self.admin, self.admin_session)
        response = self.client.get(f'{self.base_url}/products/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        # Проверяем структуру товара
        first = data[0]
        self.assertIn('id', first)
        self.assertIn('name', first)
        self.assertIn('price', first)
        self.assertIn('category', first)

    # ТЕСТЫ 403 Forbidden (запрещенный доступ)

    def test_403_guest_no_access_to_orders(self):
        """403: Гость не может получить заказы (нет разрешения)"""
        self._login(self.guest, self.guest_session)
        response = self.client.get(f'{self.base_url}/orders/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'Forbidden')
        self.assertIn('Гость', response.json()['detail'])

    def test_403_guest_no_access_to_access_rules(self):
        """403: Гость не может получить правила доступа (нет разрешения)"""
        self._login(self.guest, self.guest_session)
        response = self.client.get(f'{self.base_url}/access-rules/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'Forbidden')

    def test_403_guest_no_access_to_dashboard(self):
        """403: Гость не может получить дашборд (нет разрешения)"""
        self._login(self.guest, self.guest_session)
        response = self.client.get(f'{self.base_url}/dashboard/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'Forbidden')

    def test_403_user_no_access_to_access_rules(self):
        """403: Обычный пользователь не может получить правила доступа"""
        self._login(self.user, self.user_session)
        response = self.client.get(f'{self.base_url}/access-rules/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'Forbidden')

    def test_403_user_no_access_to_dashboard(self):
        """403: Обычный пользователь не может получить дашборд"""
        self._login(self.user, self.user_session)
        response = self.client.get(f'{self.base_url}/dashboard/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'Forbidden')

    def test_403_permission_detail_format(self):
        """403: Формат сообщения об ошибке"""
        self._login(self.guest, self.guest_session)
        response = self.client.get(f'{self.base_url}/orders/')
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('detail', data)
        self.assertEqual(data['error'], 'Forbidden')
        self.assertIn('Гость', data['detail'])
