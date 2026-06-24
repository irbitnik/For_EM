from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, ProfileSerializer, GroupSerializer
from django.utils import timezone
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from .models import Session, CustomUser


class GroupListView(APIView):
    def post(self, request):
        """Создание новой группы (только для админов)"""
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """Получение списка всех групп (только для админов)"""
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)


class GroupDetailView(APIView):
    def get(self, request, pk):
        """Получение группы по ID (только для админов)"""
        group = get_object_or_404(Group, pk=pk)
        serializer = GroupSerializer(group)
        return Response(serializer.data)

    def put(self, request, pk):
        """Обновление группы по ID (только для админов)"""
        group = get_object_or_404(Group, pk=pk)
        serializer = GroupSerializer(group, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Удаление группы по ID (только для админов)"""
        group = get_object_or_404(Group, pk=pk)
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserGroupAssignmentView(APIView):
    def post(self, request, user_id):
        """Назначить группу пользователю (только для админов)"""
        user = get_object_or_404(CustomUser, pk=user_id)
        group_id = request.data.get('group_id')
        group = get_object_or_404(Group, pk=group_id)
        user.groups.add(group)
        return Response({'message': f'Группа "{group.name}" назначена пользователю {user.email}'})

    def delete(self, request, user_id, group_id):
        """Снять группу с пользователя (только для админов)"""
        user = get_object_or_404(CustomUser, pk=user_id)
        group = get_object_or_404(Group, pk=group_id)
        user.groups.remove(group)
        return Response({'message': f'Группа "{group.name}" снята с пользователя {user.email}'})


@api_view(['POST'])
def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Пользователь успешно зарегистрирован',
                'user_id': user.id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    """Вход в систему"""
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'error': 'Email и пароль обязательны'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'Неверный email или пароль'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Проверяем пароль
        if not user.check_password(password):
            return Response({
                'error': 'Неверный email или пароль'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Проверяем активность
        if not user.is_active:
            return Response({
                'error': 'Аккаунт неактивен (удалён или заблокирован)'
            }, status=status.HTTP_403_FORBIDDEN)

        # Создаем сессию
        session = Session.create_session(user)

        # Создаем ответ и устанавливаем cookie
        response = Response({
            'message': 'Вход выполнен успешно',
            'user_id': user.id,
            'email': user.email
        })
        response = set_session_cookie(response, session)

        return response


@api_view(['POST'])
def logout(request):
    """Выход из системы"""
    if request.method == 'POST':
        session_id = request.COOKIES.get('session_id')

        # Деактивируем сессию в базе (если существует)
        if session_id:
            try:
                session = Session.objects.get(
                    session_id=session_id,
                    is_active=True
                )
                session.is_active = False
                session.save()
            except Session.DoesNotExist:
                pass  # Сессия уже удалена/не найдена

        # Удаляем cookie из браузера
        response = Response({'message': 'Выход выполнен успешно'})
        response.delete_cookie('session_id')

        return response


@api_view(['GET', 'PUT', 'PATCH'])
def profile(request):
    """Получение и обновление профиля"""
    user = request.user

    if request.method == 'GET':
        serializer = ProfileSerializer(user)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        serializer = ProfileSerializer(user, data=request.data, partial=(request.method == 'PATCH'))

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_account(request):
    """Мягкое удаление аккаунта"""
    user = request.user

    if request.method == 'DELETE':
        # 1. Деактивируем все активные сессии пользователя
        Session.objects.filter(user=user, is_active=True).update(is_active=False)

        # 2. Удаляем cookie из браузера
        response = Response({
            'message': 'Аккаунт успешно удален'
        })
        response.delete_cookie('session_id')

        # 3. Мягко удаляем пользователя (is_active=False)
        user.is_active = False
        user.save()

        return response


def set_session_cookie(response, session):
    """Установка cookie с session_id"""
    response.set_cookie(
        key='session_id',
        value=session.session_id,
        max_age=int(session.expires_at.timestamp() - timezone.now().timestamp()),
        httponly=True,  # Защищает от XSS атак
        secure=False,   # True в продакшене с HTTPS
        samesite='Lax'  # Защита от CSRF
    )
    return response


def delete_session_cookie(response):
    """Удаление cookie с session_id"""
    response.delete_cookie('session_id')
    return response
