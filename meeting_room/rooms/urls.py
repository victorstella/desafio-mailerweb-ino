from django.urls import path
from . import views

# Rotas do aplicativo `rooms`: CRUD mínimo para salas e reservas
urlpatterns = [
    path('rooms/', views.RoomListCreateView.as_view(), name='rooms-list-create'),
    path('rooms/<uuid:room_id>/bookings', views.BookingCreateView.as_view(), name='room-bookings-create'),
    path('rooms/<uuid:room_id>/bookings/<uuid:booking_id>/cancel', views.BookingCancelView.as_view(), name='booking-cancel'),
    path('rooms/<uuid:room_id>/bookings/<uuid:booking_id>', views.BookingRescheduleView.as_view(), name='booking-reschedule'),
]
