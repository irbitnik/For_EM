def seed_groups():
    """Создать группы (роли) по умолчанию"""
    from django.contrib.auth.models import Group

    groups_data = [
        {'name': 'Админ', 'code': 'admin'},
        {'name': 'Менеджер', 'code': 'manager'},
        {'name': 'Пользователь', 'code': 'user'},
        {'name': 'Гость', 'code': 'guest'},
    ]

    for group in groups_data:
        obj, created = Group.objects.get_or_create(name=group['name'])
        status = "✅ Создана" if created else "✅ Уже существует"
        print(f"{status}: {group['name']}")


def seed_permissions():
    """Создать разрешения для элементов"""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    elements = [
        {'name': 'Пользователи', 'model': 'customuser', 'app_label': 'users'},
        {'name': 'Группы', 'model': 'group', 'app_label': 'auth'},
        {'name': 'Разрешения', 'model': 'permission', 'app_label': 'auth'},
    ]

    permissions_map = [
        ('read', 'Чтение'),
        ('read_all', 'Чтение всех'),
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('update_all', 'Обновление всех'),
        ('delete', 'Удаление'),
        ('delete_all', 'Удаление всех'),
    ]

    for elem in elements:
        content_type, created = ContentType.objects.get_or_create(
            model=elem['model'],
            app_label=elem['app_label']
        )

        for codename_base, name_ru in permissions_map:
            codename = f'{codename_base}_{elem["model"]}'
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': f'{name_ru} {elem["name"]}',
                    'content_type': content_type
                }
            )
            # Необязательно: для отладки можно раскомментировать
            # print(f"  { '✅ Создано' if created else '✅ Уже есть' }: {perm.codename}")

        print(f"✅ Разрешения для '{elem['name']}' созданы/найдены")


def seed_group_permissions():
    """Назначить разрешения группам по умолчанию"""
    from django.contrib.auth.models import Group, Permission

    # 🟢 Проверка существования всех необходимых групп
    required_groups = ['Админ', 'Менеджер', 'Пользователь', 'Гость']
    for name in required_groups:
        if not Group.objects.filter(name=name).exists():
            print(f"❌ Ошибка: группа '{name}' не найдена. Выполните сначала seed_groups()")
            return

    admin_group = Group.objects.get(name='Админ')
    manager_group = Group.objects.get(name='Менеджер')
    user_group = Group.objects.get(name='Пользователь')
    guest_group = Group.objects.get(name='Гость')

    all_permissions = Permission.objects.all()
    admin_group.permissions.set(all_permissions)
    print("✅ Админ получил все разрешения (полный доступ)")

    # 🟡 Менеджер: все права, кроме критичных операций
    # Исключаем: delete_customuser, delete_all_customuser,
    #            delete_group, delete_all_group,
    #            delete_permission, delete_all_permission
    manager_permissions = all_permissions.exclude(
        codename__in=[
            'delete_customuser', 'delete_all_customuser',
            'delete_group', 'delete_all_group',
            'delete_permission', 'delete_all_permission',
        ]
    )
    manager_group.permissions.set(manager_permissions)
    print("✅ Менеджер получил все права, кроме удаления пользователей и ролей")

    user_permissions = Permission.objects.filter(
        codename__in=[
            'read_customuser',
            'update_customuser',
            'delete_customuser',
        ]
    )
    user_group.permissions.set(user_permissions)
    print("✅ Пользователь получил права на свой аккаунт")

    guest_permissions = Permission.objects.filter(
        codename__startswith='read_'
    ).exclude(codename__endswith='__all')
    guest_group.permissions.set(guest_permissions)
    print("✅ Гость получил права только на чтение")


def seed_admin_user():
    from django.contrib.auth.models import Group
    from django.apps import apps

    User = apps.get_model('users.CustomUser')

    email = 'admin@example.com'
    password = 'admin123'

    if not User.objects.filter(email=email).exists():
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name='Администратор',
            last_name='Системы',
            is_staff=True
        )
        try:
            admin_group = Group.objects.get(name='Админ')
            user.groups.add(admin_group)
            user.save()
            print(f"✅ Админ-пользователь создан: {email}")
        except Group.DoesNotExist:
            print("❌ Ошибка: группа 'Админ' не найдена. Запустите сначала seed_groups()")
            return
    else:
        print(f"ℹ️ Админ-пользователь уже существует: {email}")


def seed_all():
    """Полный набор сидов (порядок важен!)"""
    print("\n🔄 Старт сидирования ролей и прав...")
    seed_groups()
    seed_permissions()
    seed_admin_user()
    seed_group_permissions()
    print("\n✅ Сидирование завершено!\n")


if __name__ == "__main__":
    import django
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auth_system.settings")
    django.setup()
    seed_all()