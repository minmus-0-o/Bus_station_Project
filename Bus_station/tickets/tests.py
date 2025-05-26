from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from tickets.models import Trip, Order, TransportCompany
from datetime import timedelta
from django.utils import timezone  # Для работы с временными зонами
import os
from django.conf import settings
import uuid

class BusStationTests(TestCase):
    def setUp(self):
        # Настройка тестового окружения
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123', email='test@example.com'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser', password='staffpass123', email='staff@example.com', is_staff=True
        )
        self.company = TransportCompany.objects.create(name='TestBus')
        self.trip = Trip.objects.create(
            origin='Москва',
            destination='Санкт-Петербург',
            departure_time=timezone.now() + timedelta(days=1),  # Используем timezone
            price=1000.00,
            seats_available=50,
            company=self.company
        )
        self.order = Order.objects.create(
            user=self.user,
            trip=self.trip,
            tickets_count=2,  # Используем tickets_count
            ticket_number=str(uuid.uuid4())  # Уникальный ticket_number
            # created_at задаётся автоматически
        )

    def test_trip_model(self):
        # Проверка модели Trip
        trip = Trip.objects.get(id=self.trip.id)
        self.assertEqual(trip.origin, 'Москва')
        self.assertEqual(trip.destination, 'Санкт-Петербург')
        self.assertEqual(trip.price, 1000.00)
        self.assertEqual(trip.seats_available, 50)
        self.assertEqual(trip.company, self.company)
        self.assertIn('Москва - Санкт-Петербург', str(trip))

    def test_order_model(self):
        # Проверка модели Order
        order = Order.objects.get(id=self.order.id)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.trip, self.trip)
        self.assertEqual(order.tickets_count, 2)
        self.assertEqual(order.ticket_number, self.order.ticket_number)
        self.assertIn(f'Order {order.ticket_number}', str(order))

    def test_company_model(self):
        # Проверка модели TransportCompany
        company = TransportCompany.objects.get(id=self.company.id)
        self.assertEqual(company.name, 'TestBus')
        self.assertEqual(str(company), 'TestBus')

    def test_trip_list_view(self):
        # Проверка страницы списка рейсов
        response = self.client.get(reverse('trip_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/trip_list.html')
        self.assertContains(response, 'Москва')
        self.assertContains(response, 'Санкт-Петербург')

    def test_create_order_view_unauthenticated(self):
        # Проверка доступа к оформлению заказа без авторизации
        response = self.client.get(reverse('create_order', args=[self.trip.id]))
        self.assertEqual(response.status_code, 302)  # Перенаправление на логин

    def test_create_order_view_authenticated(self):
        # Проверка оформления заказа авторизованным пользователем
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_order', args=[self.trip.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/create_order.html')

        # Создание заказа
        response = self.client.post(reverse('create_order', args=[self.trip.id]), {
            'tickets_count': 3  # Используем tickets_count
        })
        self.assertEqual(response.status_code, 302)  # Перенаправление после успеха
        self.assertEqual(Order.objects.count(), 2)  # Новый заказ создан
        new_order = Order.objects.last()
        self.assertEqual(new_order.tickets_count, 3)
        updated_trip = Trip.objects.get(id=self.trip.id)
        self.assertEqual(updated_trip.seats_available, 47)  # Места уменьшились

    def test_download_ticket_view(self):
        # Проверка скачивания PDF-билета
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('download_ticket', args=[self.order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(f'attachment; filename="ticket_{self.order.ticket_number}.pdf"',
                      response['Content-Disposition'])

    def test_user_profile_view(self):
        # Проверка личного кабинета
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/user_profile.html')
        self.assertContains(response, self.order.ticket_number)  # Номер билета

    def test_add_trip_view_unauthorized(self):
        # Проверка доступа к добавлению рейса без прав
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('add_trip'))
        self.assertEqual(response.status_code, 302)  # Доступ запрещён
        self.assertRedirects(response, '/accounts/login/?next=/add_trip/')

    def test_add_trip_view_authorized(self):
        # Проверка добавления рейса персоналом
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('add_trip'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/add_trip.html')

        # Добавление рейса
        response = self.client.post(reverse('add_trip'), {
            'origin': 'Казань',
            'destination': 'Самара',
            'departure_time': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M'),
            'price': 800.00,
            'seats_available': 40,
            'company': self.company.id
        })
        self.assertEqual(response.status_code, 302)  # Перенаправление после успеха
        self.assertEqual(Trip.objects.count(), 2)  # Новый рейс создан
        new_trip = Trip.objects.last()
        self.assertEqual(new_trip.origin, 'Казань')
        self.assertEqual(new_trip.price, 800.00)

    def test_font_file_exists(self):
        # Проверка наличия шрифта DejaVuSans.ttf
        font_path = os.path.join(settings.BASE_DIR, 'tickets', 'static', 'fonts', 'DejaVuSans.ttf')
        self.assertTrue(os.path.exists(font_path), f"Шрифт не найден по пути: {font_path}")

    def test_user_registration(self):
        # Проверка регистрации нового пользователя
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)  # Перенаправление после успеха
        self.assertTrue(User.objects.filter(username='newuser').exists())