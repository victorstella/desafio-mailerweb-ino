"""Views da API para salas e reservas.

Contém endpoints para listar/criar salas e criar/cancelar/reagendar reservas.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

from .models import Room, Booking
from .serializers import RoomSerializer, BookingSerializer


class RoomListCreateView(generics.ListCreateAPIView):
    queryset = Room.objects.all().order_by('name')
    serializer_class = RoomSerializer

    """Lista salas (pública) e cria salas (autenticado)."""
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class BookingCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    """Cria uma reserva para a sala especificada, validando sobreposição."""
    def post(self, request, room_id):
        room = get_object_or_404(Room, pk=room_id)
        serializer = BookingSerializer(data=request.data, context={'room': room})
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    """Marca a reserva como cancelada (não a remove)."""
    def post(self, request, room_id, booking_id):
        room = get_object_or_404(Room, pk=room_id)
        booking = get_object_or_404(Booking, pk=booking_id, room=room)

        if booking.status == Booking.STATUS_CANCELED:
            return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)

        booking.status = Booking.STATUS_CANCELED
        booking.canceled_at = timezone.now()
        booking.save()

        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)


class BookingRescheduleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    """Reagenda uma reserva existente, validando duração e sobreposição."""
    def put(self, request, room_id, booking_id):
        room = get_object_or_404(Room, pk=room_id)
        booking = get_object_or_404(Booking, pk=booking_id, room=room)

        # Valida regras básicas de data usando o serializer
        serializer = BookingSerializer(instance=booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_start = serializer.validated_data.get('start_at', booking.start_at)
        new_end = serializer.validated_data.get('end_at', booking.end_at)

        # Previne sobreposição com outras reservas
        with transaction.atomic():
            Room.objects.select_for_update().get(pk=room.pk)

            overlap_qs = Booking.objects.filter(
                room=room,
                status=Booking.STATUS_ACTIVE,
            ).exclude(pk=booking.pk).filter(start_at__lt=new_end, end_at__gt=new_start)

            if overlap_qs.exists():
                return Response({'detail': 'Agendamento sobreposto com outro agendamento ativo'}, status=status.HTTP_400_BAD_REQUEST)

            booking.start_at = new_start
            booking.end_at = new_end
            booking.save()

        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)
