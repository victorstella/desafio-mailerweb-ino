import os
from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase


class TestRoomsAPI(APITestCase):
    """Testes de API para salas e reservas (integração básica)."""

    def setUp(self):
        # garante que o token está presente para autenticação
        os.environ['API_TOKEN'] = 'test-token'
        self.auth_header = {'HTTP_AUTHORIZATION': 'Bearer test-token'}

    def test_health(self):
        r = self.client.get('/health')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'status': 'ok'})

    def test_create_room_unauthenticated(self):
        data = {"name": "Atlantic", "capacity": 10}
        r = self.client.post('/rooms/', data, format='json')
        self.assertEqual(r.status_code, 401)

    def test_create_room(self):
        data = {"name": "Atlantic", "capacity": 10}
        r = self.client.post('/rooms/', data, format='json', **self.auth_header)
        self.assertEqual(r.status_code, 201)
        self.assertIn('id', r.json())

    def test_create_duplicate_room(self):
        data = {"name": "Atlantic", "capacity": 10}
        r1 = self.client.post('/rooms/', data, format='json', **self.auth_header)
        self.assertEqual(r1.status_code, 201)
        r2 = self.client.post('/rooms/', data, format='json', **self.auth_header)
        self.assertIn(r2.status_code, (400, 409))

    def test_list_rooms(self):
        # cria duas salas
        for i in range(2):
            self.client.post('/rooms/', {"name": f"R{i}", "capacity": 5}, format='json', **self.auth_header)
        r = self.client.get('/rooms/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.json().get('results', r.json())) >= 2)

    def test_create_booking(self):
        # cria sala
        room = self.client.post('/rooms/', {"name": "B1", "capacity": 4}, format='json', **self.auth_header).json()
        start = (timezone.now() + timedelta(hours=1)).isoformat()
        end = (timezone.now() + timedelta(hours=2)).isoformat()
        r = self.client.post(f"/rooms/{room['id']}/bookings", {"title": "Meeting", "start_at": start, "end_at": end}, format='json', **self.auth_header)
        self.assertEqual(r.status_code, 201)

    def test_overlapping_booking_prevented(self):
        room = self.client.post('/rooms/', {"name": "B2", "capacity": 4}, format='json', **self.auth_header).json()
        now = timezone.now()
        s1 = (now + timedelta(hours=1))
        e1 = (now + timedelta(hours=2))
        data1 = {"title": "A", "start_at": s1.isoformat(), "end_at": e1.isoformat()}
        r1 = self.client.post(f"/rooms/{room['id']}/bookings", data1, format='json', **self.auth_header)
        self.assertEqual(r1.status_code, 201)
        # tentativa de booking que sobrepõe
        s2 = (now + timedelta(hours=1, minutes=30))
        e2 = (now + timedelta(hours=2, minutes=30))
        data2 = {"title": "B", "start_at": s2.isoformat(), "end_at": e2.isoformat()}
        r2 = self.client.post(f"/rooms/{room['id']}/bookings", data2, format='json', **self.auth_header)
        self.assertEqual(r2.status_code, 400)

    def test_edge_touching_allowed(self):
        room = self.client.post('/rooms/', {"name": "B3", "capacity": 4}, format='json', **self.auth_header).json()
        now = timezone.now()
        s1 = (now + timedelta(hours=1))
        e1 = (now + timedelta(hours=2))
        data1 = {"title": "A", "start_at": s1.isoformat(), "end_at": e1.isoformat()}
        r1 = self.client.post(f"/rooms/{room['id']}/bookings", data1, format='json', **self.auth_header)
        self.assertEqual(r1.status_code, 201)
        # borda-exata: começa exatamente em e1 (permitido)
        s2 = e1
        e2 = (now + timedelta(hours=3))
        data2 = {"title": "B", "start_at": s2.isoformat(), "end_at": e2.isoformat()}
        r2 = self.client.post(f"/rooms/{room['id']}/bookings", data2, format='json', **self.auth_header)
        self.assertEqual(r2.status_code, 201)

    def test_booking_duration_bounds(self):
        room = self.client.post('/rooms/', {"name": "B4", "capacity": 4}, format='json', **self.auth_header).json()
        now = timezone.now()
        min_minutes = 15
        max_minutes = 540
        s = now + timedelta(minutes=60)

        # muito curto: abaixo de min_minutes (min_minutes - 1)
        e = s + timedelta(minutes=(min_minutes - 1))
        r = self.client.post(f"/rooms/{room['id']}/bookings", {"title": "Short", "start_at": s.isoformat(), "end_at": e.isoformat()}, format='json', **self.auth_header)
        self.assertEqual(r.status_code, 400)

        # muito longo: acima de max_minutes (max_minutes + 1)
        e2 = s + timedelta(minutes=(max_minutes + 1))
        r2 = self.client.post(f"/rooms/{room['id']}/bookings", {"title": "Long", "start_at": s.isoformat(), "end_at": e2.isoformat()}, format='json', **self.auth_header)
        self.assertEqual(r2.status_code, 400)

    def test_cancel_booking(self):
        room = self.client.post('/rooms/', {"name": "C1", "capacity": 4}, format='json', **self.auth_header).json()
        now = timezone.now()
        s = now + timedelta(hours=1)
        e = now + timedelta(hours=2)
        b = self.client.post(f"/rooms/{room['id']}/bookings", {"title": "ToCancel", "start_at": s.isoformat(), "end_at": e.isoformat()}, format='json', **self.auth_header).json()

        r = self.client.post(f"/rooms/{room['id']}/bookings/{b['id']}/cancel", format='json', **self.auth_header)
        self.assertEqual(r.status_code, 200)
        jb = r.json()
        self.assertEqual(jb.get('status'), 'canceled')
        self.assertIsNotNone(jb.get('canceled_at'))

    def test_reschedule_booking(self):
        room = self.client.post('/rooms/', {"name": "Rsch", "capacity": 4}, format='json', **self.auth_header).json()
        now = timezone.now()
        s1 = now + timedelta(hours=1)
        e1 = now + timedelta(hours=2)
        b = self.client.post(f"/rooms/{room['id']}/bookings", {"title": "Orig", "start_at": s1.isoformat(), "end_at": e1.isoformat()}, format='json', **self.auth_header).json()

        new_s = now + timedelta(hours=3)
        new_e = now + timedelta(hours=4)
        r = self.client.put(f"/rooms/{room['id']}/bookings/{b['id']}", {"start_at": new_s.isoformat(), "end_at": new_e.isoformat()}, format='json', **self.auth_header)
        self.assertEqual(r.status_code, 200)
        jb = r.json()
        # parse returned datetime and compare as aware datetimes to avoid formatting differences (Z vs +00:00)
        from django.utils.dateparse import parse_datetime
        parsed = parse_datetime(jb.get('start_at'))
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.replace(microsecond=parsed.microsecond), new_s.replace(microsecond=parsed.microsecond))

    def test_reschedule_overlapping_prevented(self):
        room = self.client.post('/rooms/', {"name": "Rov", "capacity": 4}, format='json', **self.auth_header).json()
        now = timezone.now()
        s1 = now + timedelta(hours=1)
        e1 = now + timedelta(hours=2)
        # booking A
        a = self.client.post(f"/rooms/{room['id']}/bookings", {"title": "A", "start_at": s1.isoformat(), "end_at": e1.isoformat()}, format='json', **self.auth_header).json()
        # booking B
        s2 = now + timedelta(hours=3)
        e2 = now + timedelta(hours=4)
        b = self.client.post(f"/rooms/{room['id']}/bookings", {"title": "B", "start_at": s2.isoformat(), "end_at": e2.isoformat()}, format='json', **self.auth_header).json()

        # try to reschedule B to overlap A
        r = self.client.put(f"/rooms/{room['id']}/bookings/{b['id']}", {"start_at": (now + timedelta(hours=1, minutes=30)).isoformat(), "end_at": (now + timedelta(hours=2, minutes=30)).isoformat()}, format='json', **self.auth_header)
        self.assertEqual(r.status_code, 400)
