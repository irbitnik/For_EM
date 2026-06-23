from django.apps import AppConfig
from django.db.models.signals import post_migrate

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        from .seeders import seed_all
        from django.apps import apps

        def post_migration_callback(sender, **kwargs):
            # Запускаем сиды только если не отключено (например, в тестах)
            from django.conf import settings
            if getattr(settings, 'AUTO_SEED_GROUPS', True):
                seed_all()

        post_migrate.connect(post_migration_callback, sender=self)