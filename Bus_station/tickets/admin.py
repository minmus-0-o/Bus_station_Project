from django.contrib import admin
from .models import Trip, Order, TransportCompany

admin.site.register(Trip)
admin.site.register(Order)
admin.site.register(TransportCompany)