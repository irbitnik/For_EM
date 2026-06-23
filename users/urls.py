from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('delete-account/', views.delete_account, name='delete_account'),

    # API для управления ролями (админка)
    path('admin/groups/', views.GroupListView.as_view(), name='group-list'),
    path('admin/groups/<int:pk>/', views.GroupDetailView.as_view(), name='group-detail'),
    path('admin/users/<int:user_id>/groups/', views.UserGroupAssignmentView.as_view(), name='user-group-assignment'),
]