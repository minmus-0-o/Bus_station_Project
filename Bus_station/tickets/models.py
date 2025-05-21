from django.db import models
from django.contrib.auth.models import User

class Trip(models.Model):
    origin = models.CharField(max_length=100)  # Пункт отправления
    destination = models.CharField(max_length=100)  # Пункт назначения
    departure_time = models.DateTimeField()  # Время отправления
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена билета
    seats_available = models.IntegerField()  # Доступные места

    def __str__(self):
        return f"{self.origin} - {self.destination} at {self.departure_time}"

class Order(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)  # Связь с рейсом
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Связь с пользователем
    tickets_count = models.IntegerField()  # Количество билетов
    created_at = models.DateTimeField(auto_now_add=True)  # Дата заказа

    def __str__(self):
        return f"Order by {self.user.username} for {self.trip}"