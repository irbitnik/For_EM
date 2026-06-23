from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

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
        Group.objects.get_or_create(name=group['name'])
        print(f"✅ Сгруппа создана/найдена: {group['name']}")


def seed_permissions():
    """Создать разрешения для элементов"""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from django.apps import apps

    # Элементы, которые будем защищать
    elements = [
        {'name': 'Пользователи', 'model': 'customuser', 'app_label': 'users'},
        {'name': 'Группы', 'model': 'group', 'app_label': 'auth'},
        {'name': 'Разрешения', 'model': 'permission', 'app_label': 'auth'},
        # В будущем: products, shops, orders, access_rules — добавим модели и обновим список
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
        # Получаем content_type или создаем, если нет (на всякий случай)
        content_type, created = ContentType.objects.get_or_create(
            model=elem['model'],
            app_label=elem['app_label']
        )

        for codename_base, name_ru in permissions_map:
            codename = f'{codename_base}_{elem["model"]}'
            Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': f'{name_ru} {elem["name"]}',
                    'content_type': content_type
                }
            )
        print(f"✅ Разрешения для '{elem['name']}' созданы/найдены")


def seed_group_permissions():
    """Назначить разрешения группам по умолчанию"""
    from django.contrib.auth.models import Group, Permission

    admin_group = Group.objects.get(name='Админ')
    manager_group = Group.objects.get(name='Менеджер')
    user_group = Group.objects.get(name='Пользователь')
    guest_group = Group.objects.get(name='Гость')

    # Админ: все права
    all_permissions = Permission.objects.all()
    admin_group.permissions.set(all_permissions)
    print("✅ Админ получил все разрешения")

    # Менеджер: все права
    manager_group.permissions.set(all_permissions)
    print("✅ Менеджер получил все разрешения")

    # Пользователь: только свои объекты
    user_permissions = Permission.objects.filter(
        codename__in=[
            'read_customuser',  # читать (свой профиль)
            'update_customuser',
            'delete_customuser',
        ]
    )
    user_group.permissions.set(user_permissions)
    print("✅ Пользователь получил права на свой аккаунт")

    # Гость: только чтение
    guest_permissions = Permission.objects.filter(
        codename__startswith='read_'
    ).exclude(codename__endswith='__all')
    guest_group.permissions.set(guest_permissions)
    print("✅ Гость получил права только на чтение общих данных")

def seed_admin_user():
    """Создать админа, если нет"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    username = 'admin'
    email = 'admin@example.com'
    password = 'admin123'  # В продакшене — из .env

    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, email=email, password=password)
        admin_group = Group.objects.get(name='Админ')
        user.groups.add(admin_group)
        user.save()
        print(f"✅ Админ-пользователь создан: {username}")
    else:
        print(f"ℹ️ Админ-пользователь уже существует: {username}")

def seed_all():
    """Полный набор сидов (порядок важен!)"""
    print("\n🔄 Старт сидирования ролей и прав...")
    seed_groups()
    seed_permissions()
    seed_admin_user()
    seed_group_permissions()
    print("\n✅ Сидирование завершено!\n")


# Вызываем при выполнении файла напрямую (например, через shell)
if __name__ == "__main__":
    import django
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auth_system.settings")
    django.setup()
    seed_all()