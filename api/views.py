from rest_framework import viewsets, status
from rest_framework.response import Response as APIResponse
from api.serializers import EmojiSerializer, MessageSerializer, ResponseSerializer, ScheduleSerializer
from api.models import Emoji, Message, Response, Schedule, SendLog
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff


class IsOwnerReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS and obj.user == request.user:
            return True
        return request.user.is_staff


class EmojiViewSet(viewsets.ModelViewSet):
    serializer_class = EmojiSerializer
    permission_classes = (IsAdminOrReadOnly,)
    queryset = Emoji.objects.all()


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAdminUser,)
    queryset = Message.objects.all()


class ResponseViewSet(viewsets.ModelViewSet):
    serializer_class = ResponseSerializer
    permission_classes = (IsOwnerReadOnly, permissions.IsAuthenticated)
    def get_queryset(self):
        if self.request.user.is_staff:
            return Response.objects.all()
        return Response.objects.filter(user=self.request.user)

    def create(self, request, format=None):
        emoji = Emoji.objects.get(name=request.data['emoji'])
        response = Response(user=request.user, emoji=emoji)
        sendlog = SendLog.objects.filter(success=True).filter(user=request.user).order_by('-ts')[0]
        if sendlog.response is None:
            response.save()
            sendlog.response = response
            sendlog.save()
            api_response = APIResponse(data=ResponseSerializer(instance=response).data, status=status.HTTP_201_CREATED)
        else:
            api_response = APIResponse(status=status.HTTP_409_CONFLICT)
        return api_response



class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = (permissions.IsAdminUser,)
    queryset = Schedule.objects.all()

