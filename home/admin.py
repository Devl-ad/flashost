from django.contrib import admin
from .models import Package, Order, OrderItem

admin.site.register(Package)
admin.site.register(Order)
admin.site.register(OrderItem)
