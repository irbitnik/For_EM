# Система управления пользователями и ограничениями доступа

## 📋 Описание проекта

Это Django-приложение, реализующее комплексную систему управления пользователями с ролевой моделью доступа (RBAC - Role-Based Access Control).

### Ключевые особенности
- **Кастомная модель пользователя** с email-аутентификацией
- **Bcrypt-хеширование** паролей для безопасности
- **Система ролей** через Django Groups
- **Middleware-авторизация** для API-эндпоинтов
- **Cookie-сессии** с поддержкой истечения срока действия
- **Гибкая система разрешений** на уровне объектов

---

## 🏗️ Структура проекта

```
For EM/
├── auth_system/              # Конфигурация Django-проекта
│   ├── __init__.py
│   ├── settings.py          # Основные настройки
│   ├── urls.py              # Главные URL-маршруты
│   ├── asgi.py
│   └── wsgi.py
├── users/                   # Основное приложение
│   ├── models.py            # Модели CustomUser и Session
│   ├── views.py             # API-контроллеры для auth
│   ├── serializers.py       # DRF-сериализаторы
│   ├── middleware.py        # Middleware для авторизации
│   ├── decorators.py        # Декораторы @require_role, @require_permission
│   ├── admin.py             # Настройка админки Django
│   ├── tests.py             # Тесты (MockViewsSimpleTest)
│   ├── mock_views.py        # Демонстрационные эндпоинты
│   ├── mock_urls.py         # Маршруты для демонстрации
│   ├── seeders.py           # Сиды для создания ролей/пользователей
│   └── migrations/          # Миграции БД
├── db.sqlite3               # База данных SQLite
├── manage.py                # Утилита управления Django
└── README.md                # Этот файл
```

---

## 🔐 Схема управления ограничениями доступа

### Архитектура авторизации

```
┌─────────────────────────────────────────────────────────────┐
│                     КЛИЕНТ (браузер)                        │
│                    ┌─────────────────┐                       │
│                    │  Cookie:        │                       │
│                    │  session_id     │                       │
│                    └────────┬────────┘                       │
└─────────────────────────────┼───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              APIMiddleware (middleware.py)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. Аутентификация через cookie session_id          │   │
│  │  2. Проверка активности и срока действия сессии     │   │
│  │  3. Централизованная проверка прав                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              PermissionEnforcer.check_access()              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Пропуск: /admin/, /static/, /media/                │   │
│  │  Пропуск: /api/users/login/, register/, logout/     │   │
│  │                                                       │   │
│  │  Проверка:                                            │   │
│  │  - User is authenticated? → 401                      │   │
│  │  - Админ (is_staff or 'Админ' роль)? → Доступ        │   │
│  │  - Права по codename? → 403                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    КОНТРОЛЛЕР ВИДА                         │
└─────────────────────────────────────────────────────────────┘
```

### Роли и разрешения

#### 🟢 Админ
- **Права**: Полный доступ ко всем системам
- **Разрешения**: Все разрешения (read, create, update, delete для всех элементов)
- **Пример**: Администратор системы

#### 🟡 Менеджер
- **Права**: Управление контентом, без удаления пользователей и ролей
- **Разрешения**: read, create, update для всех элементов; excludes delete_* для customuser и group
- **Пример**: Менеджер магазина, контент-менеджер

#### 🔵 Пользователь
- **Права**: Доступ только к своему аккаунту
- **Разрешения**: read, update, delete только для своего профиля (read_customuser, update_customuser, delete_customuser)
- **Пример**: Обычный пользователь системы

#### ⚪ Гость
- **Права**: Только чтение публичных данных
- **Разрешения**: Только read_* разрешения (без read_all_*)
- **Пример**: Неавторизованный посетитель

---

## 🗄️ Модели данных

### CustomUser
```python
- email (EmailField, unique) - Email для входа
- first_name, last_name, middle_name - ФИО
- is_active (BooleanField) - Активен ли аккаунт
- is_staff (BooleanField) - Доступ в админку
- groups (ManyToMany) - Роли пользователя
- user_permissions (ManyToMany) - Прямые разрешения
```

### Session
```python
- user (ForeignKey to CustomUser) - Пользователь
- session_id (UUID4) - Уникальный ID сессии
- created_at (DateTime) - Время создания
- expires_at (DateTime) - Время истечения
- is_active (Boolean) - Активна ли сессия
```
---

## 🧪 Тесты

### Запуск всех тестов

```bash
python manage.py test
```
### Тестовое покрытие

Тесты проверяют:
- ✅ Аутентификацию (401 Unauthorized)
- ✅ Авторизацию (403 Forbidden)
- ✅ Права ролей (Админ, Менеджер, Пользователь, Гость)
- ✅ Проверку cookie-сессий
- ✅ Истечение срока действия сессий
- ✅ Демонстрационные эндпоинты (mock-views)
- ✅ Формат ответов API

---

## 📡 API-эндпоинты

### Аутентификация

#### POST `/api/users/register/`
Регистрация нового пользователя

**Тело запроса:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "password_confirm": "password123",
  "first_name": "Иван",
  "last_name": "Иванов",
  "middle_name": "Иванович"
}


POST `/api/users/login/`
Вход в систему

**Тело запроса:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Ответ:** Cookie с `session_id` (устанавливается автоматически)

#### POST `/api/users/logout/`
Выход из системы

**Headers:**
- `Cookie: session_id=<id>`

#### GET `/api/users/profile/`
Получение профиля

**Headers:**
- `Cookie: session_id=<id>`

#### PUT/PATCH `/api/users/profile/`
Обновление профиля

**Headers:**
- `Cookie: session_id=<id>`

#### DELETE `/api/users/delete-account/`
Мягкое удаление аккаунта

**Headers:**
- `Cookie: session_id=<id>`

### Управление ролями (админ)

#### POST `/api/users/admin/groups/`
Создание группы

#### GET `/api/users/admin/groups/`
Список всех групп

#### GET `/api/users/admin/groups/{pk}/`
Получение группы

#### PUT `/api/users/admin/groups/{pk}/`
Обновление группы

#### DELETE `/api/users/admin/groups/{pk}/`
Удаление группы

#### POST `/api/users/admin/users/{user_id}/groups/`
Назначение группы пользователю

#### DELETE `/api/users/admin/users/{user_id}/groups/{group_id}/`
Снятие группы с пользователя

---

## 🧪 Демонстрационные эндпоинты

Доступны по `/api/mock/`

| Эндпоинт | Описание | Требуемое разрешение |
|----------|----------|----------------------|
| `GET /api/mock/products/` | Список товаров | read_product |
| `GET /api/mock/products/{id}/` | Детали товара | read_product |
| `GET /api/mock/products/category/{cat}/` | Товары по категории | read_product |
| `GET /api/mock/shops/` | Список магазинов | read_shop |
| `GET /api/mock/shops/{id}/` | Детали магазина | read_shop |
| `GET /api/mock/orders/` | Список заказов | read_order |
| `GET /api/mock/orders/{id}/` | Детали заказа | read_order |
| `GET /api/mock/access-rules/` | Правила доступа | read_accessrule |
| `GET /api/mock/dashboard/` | Панель управления | read_dashboard |

---

## 👥 Демо-пользователи (после запуска seeders)

| Email | Пароль | Роль | Доступ |
|-------|--------|------|--------|
| `admin@example.com` | `123456` | Админ | Полный доступ |
| `manager@example.com` | `123456` | Менеджер | Управление контентом |
| `user@example.com` | `123456` | Пользователь | Только свой профиль |
| `guest@example.com` | `123456` | Гость | Только чтение товаров |

---

## 🛠️ Технологический стек

- **Backend**: Python 3.11+, Django 6.0+, Django REST Framework
- **Database**: SQLite3 (можно заменить на PostgreSQL/MySQL)
- **Hashing**: Bcrypt для паролей
- **Authentication**: Cookie-based sessions with UUID4
- **Authorization**: RBAC via Django Groups + Custom Middleware

---

## 🔒 Безопасность

- Пароли хешируются через bcrypt
- Cookie-сессии с httponly flag
- Поддержка истечения срока действия сессий
- Централизованная проверка прав через middleware
- Разделение прав на уровне объектов
- Админы (is_staff) получают полный доступ по умолчанию

---

## 📝 Примечания

- Проект использует кастомную модель пользователя (CustomUser) вместо стандартной User
- Админка Django работает отдельно от API (использует стандартный Django auth)
- Middleware применяется только к `/api/` роутам, админка использует стандартную аутентификацию
- Мягкое удаление пользователей через `is_active=False` вместо физического удаления

---

