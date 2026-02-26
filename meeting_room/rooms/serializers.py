"""Serializers para API de salas e reservas.

Valida duração, limites e previne sobreposição simultânea.
"""

from datetime import timedelta

from django.utils import timezone
from django.db import transaction
from rest_framework import serializers

from .models import Room, Booking


"""Serializador simples para `Room` (leitura/gravação básica)."""
class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name', 'capacity', 'created_at']


"""Serializador para `Booking` com validações e criação concorrente segura.

- valida duração mínima/máxima
- valida ordem start < end
- previne sobreposição usando `select_for_update` no registro da sala
"""
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'title', 'start_at', 'end_at', 'status', 'canceled_at', 'created_at', 'updated_at']
        read_only_fields = ['status', 'canceled_at', 'created_at', 'updated_at', 'id']

    def validate(self, data):
        start = data.get('start_at')
        end = data.get('end_at')
        if not start or not end:
            raise serializers.ValidationError('É necessário definir horários de início e término')
        if start >= end:
            raise serializers.ValidationError('O horário de início deve ser anterior ao de término')
        duration = end - start
        if duration < timedelta(minutes=15):
            raise serializers.ValidationError('A duração mínima é de 15 minutos')
        if duration > timedelta(minutes=540):
            raise serializers.ValidationError('A duração máxima é de 8 horas')
        return data

    def create(self, validated_data):
        room = self.context.get('room')
        if room is None:
            raise serializers.ValidationError('Sala é necessária para criar uma reserva')

        start = validated_data['start_at']
        end = validated_data['end_at']

        # Usa transação e select_for_update na sala para prevenir condições de corrida
        with transaction.atomic():
            Room.objects.select_for_update().get(pk=room.pk)

            overlap_qs = Booking.objects.filter(
                room=room,
                status=Booking.STATUS_ACTIVE,
            ).filter(start_at__lt=end, end_at__gt=start)

            if overlap_qs.exists():
                raise serializers.ValidationError('Já existe uma reserva ativa que se sobrepõe a este período')

            booking = Booking.objects.create(room=room, **validated_data)
            return booking
