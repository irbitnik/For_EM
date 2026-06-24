def seed_groups():
    """Создать группы (роли) по умолчанию"""
    from django.contrib.auth.models import Group

    groups_data = [
        {'name': 'Админ', 'code': 'admin', 'description': 'Полный доступ ко всем системам'},
        {'name': 'Менеджер', 'code': 'manager', 'description': 'Управление контентом, без удаления пользователей'},
        {'name': 'Пользователь', 'code': 'user', 'description': 'Доступ к своему аккаунту и базовым функциям'},
        {'name': 'Гость', 'code': 'guest', 'description': 'Только чтение публичных данных'},
    ]

    for group in groups_data:
        obj, created = Group.objects.get_or_create(name=group['name'])
        status = "✅ Создана" if created else "✅ Уже существует"
        print(f"{status}: {group['name']} ({group['description']})")


def seed_permissions():
    """Создать разрешения для элементов"""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from django.apps import apps

    # Получаем content type для CustomUser
    User = apps.get_model('users.CustomUser')
    user_content_type, _ = ContentType.objects.get_or_create(
        model='customuser',
        app_label='users'
    )

    # Получаем content type для Group
    group_content_type, _ = ContentType.objects.get_or_create(
        model='group',
        app_label='auth'
    )

    permissions_map = [
        ('read', 'Чтение'),
        ('read_all', 'Чтение всех'),
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('update_all', 'Обновление всех'),
        ('delete', 'Удаление'),
        ('delete_all', 'Удаление всех'),
    ]

    # Создаем разрешения для CustomUser
    for codename_base, name_ru in permissions_map:
        codename = f'{codename_base}_customuser'
        perm, created = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                'name': f'{name_ru} пользователей',
                'content_type': user_content_type
            }
        )

    # Создаем разрешения для Group (ролей)
    for codename_base, name_ru in permissions_map:
        codename = f'{codename_base}_group'
        perm, created = Permission.objects.get_or_create(
            codename=codename,
            defaults={
                'name': f'{name_ru} ролей',
                'content_type': group_content_type
            }
        )

    print("Разрешения для пользователей и ролей созданы/найдены")


def seed_group_permissions():
    """Назначить разрешения группам по умолчанию"""
    from django.contrib.auth.models import Group, Permission

    # 🟢 Проверка существования всех необходимых групп
    required_groups = ['Админ', 'Менеджер', 'Пользователь', 'Гость']
    for name in required_groups:
        if not Group.objects.filter(name=name).exists():
            print(f"Ошибка: группа '{name}' не найдена. Выполните сначала seed_groups()")
            return

    admin_group = Group.objects.get(name='Админ')
    manager_group = Group.objects.get(name='Менеджер')
    user_group = Group.objects.get(name='Пользователь')
    guest_group = Group.objects.get(name='Гость')

    # АДМИН: все разрешения
    all_permissions = Permission.objects.all()
    admin_group.permissions.set(all_permissions)
    print("Админ получил все разрешения (полный доступ)")

    # МЕНЕДЖЕР: все права, кроме критичных операций удаления
    # Исключаем удаление пользователей и ролей
    manager_permissions = all_permissions.exclude(
        codename__in=[
            'delete_customuser', 'delete_all_customuser',
            'delete_group', 'delete_all_group',
        ]
    )
    manager_group.permissions.set(manager_permissions)
    print("Менеджер получил все права, кроме удаления пользователей и ролей")
    print("   (может читать, создавать и обновлять всё)")

    # ПОЛЬЗОВАТЕЛЬ: права только на свой аккаунт
    user_permissions = Permission.objects.filter(
        codename__in=[
            'read_customuser',           # Читать свои данные
            'update_customuser',         # Обновлять свои данные
            'delete_customuser',         # Удалять свой аккаунт
        ]
    )
    user_group.permissions.set(user_permissions)
    print("Пользователь получил права только на свой аккаунт")
    print("   (чтение, обновление, удаление только своего профиля)")

    # ГОСТЬ: только чтение публичных данных
    guest_permissions = Permission.objects.filter(
        codename__startswith='read_'
    ).exclude(
        codename__in=['read_all_customuser', 'read_all_group']
    )
    guest_group.permissions.set(guest_permissions)
    print("Гость получил права только на чтение")
    print("   (может читать свои данные и публичную информацию)")


def seed_users():
    """Создать пользователей с ролями для демонстрации"""
    from django.contrib.auth.models import Group
    from django.apps import apps

    User = apps.get_model('users.CustomUser')

    # Данные пользователей для демонстрации
    users_data = [
        {
            'email': 'admin@example.com',
            'password': '123456',
            'first_name': 'Администратор',
            'last_name': 'Системы',
            'middle_name': 'Олегович',
            'role': 'Админ',
            'is_staff': True,
            'description': 'Админ с полным доступом'
        },
        {
            'email': 'manager@example.com',
            'password': '123456',
            'first_name': 'Менеджер',
            'last_name': 'Торговли',
            'middle_name': 'Андреевич',
            'role': 'Менеджер',
            'is_staff': False,
            'description': 'Менеджер — управляет контентом, не может удалять пользователей'
        },
        {
            'email': 'user@example.com',
            'password': '123456',
            'first_name': 'Обычный',
            'last_name': 'Пользователь',
            'middle_name': 'Иванович',
            'role': 'Пользователь',
            'is_staff': False,
            'description': 'Пользователь — работает со своим профилем'
        },
        {
            'email': 'guest@example.com',
            'password': '123456',
            'first_name': 'Гость',
            'last_name': 'Гостевой',
            'middle_name': '',
            'role': 'Гость',
            'is_staff': False,
            'description': 'Гость — только чтение публичных данных'
        },
    ]

    for user_data in users_data:
        # Проверяем, существует ли пользователь
        if not User.objects.filter(email=user_data['email']).exists():
            user = User.objects.create_user(
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                middle_name=user_data.get('middle_name', ''),
                is_staff=user_data['is_staff']
            )
            
            # Назначаем роль (группу)
            try:
                role_group = Group.objects.get(name=user_data['role'])
                user.groups.add(role_group)
                user.save()
                print(f"Создан пользователь: {user_data['email']}")
                print(f"   Роль: {user_data['role']} ({user_data['description']})")
                print(f"   Пароль: {user_data['password']}")
            except Group.DoesNotExist:
                print(f"Ошибка: группа '{user_data['role']}' не найдена")
        else:
            print(f"ℹ️ Пользователь уже существует: {user_data['email']}")
            # Проверяем, есть ли у него роль
            try:
                role_group = Group.objects.get(name=user_data['role'])
                user = User.objects.get(email=user_data['email'])
                if not user.groups.filter(name=user_data['role']).exists():
                    user.groups.add(role_group)
                    user.save()
                    print(f"   Роль '{user_data['role']}' назначена")
            except Group.DoesNotExist:
                pass


def seed_all():
    """Полный набор сидов (порядок важен!)"""
    print("\nСтарт сидирования ролей и прав...\n")
    seed_groups()
    print()
    seed_permissions()
    print()
    seed_group_permissions()
    print()
    seed_users()
    print("\nСидирование завершено!\n")


def print_role_summary():
    """Вывести сводку по ролям и правам"""
    from django.contrib.auth.models import Group
    from django.apps import apps

    User = apps.get_model('users.CustomUser')

    print("\nСВОДКА ПО РОЛЯМ И ПРАВАХ\n")
    print("=" * 80)

    for group_name in ['Админ', 'Менеджер', 'Пользователь', 'Гость']:
        group = Group.objects.get(name=group_name)
        permissions = group.permissions.all()
        permission_names = [p.name for p in permissions]
        users = group.user_set.all()

        print(f"\n🔹 {group_name}")
        print(f"   Разрешений: {permissions.count()}")
        print(f"   Пользователей: {users.count()}")
        
        # Список пользователей
        if users.count() > 0:
            print(f"   Пользователи:")
            for u in users:
                print(f"      • {u.email} ({u.last_name} {u.first_name})")
        
        # Список разрешений
        print(f"   Разрешения (первые 10):")
        for name in sorted(permission_names)[:10]:
            print(f"      • {name}")
        if permissions.count() > 10:
            print(f"      ... и ещё {permissions.count() - 10}")

    print("\n" + "=" * 80)


def print_users_summary():
    """Вывести сводку по всем пользователям"""
    from django.apps import apps

    User = apps.get_model('users.CustomUser')

    print("\nВСЕ ПОЛЬЗОВАТЕЛИ СИСТЕМЫ\n")
    print("=" * 80)
    print(f"{'ID':<5} {'Email':<30} {'ФИО':<30} {'Роли':<20}")
    print("-" * 80)

    for user in User.objects.all().select_related():
        roles = ', '.join(user.groups.values_list('name', flat=True)) or 'Без роли'
        fio = f"{user.last_name} {user.first_name} {user.middle_name}".strip()
        print(f"{user.id:<5} {user.email:<30} {fio:<30} {roles:<20}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import django
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auth_system.settings")
    django.setup()
    seed_all()
    print_role_summary()
    print_users_summary()
