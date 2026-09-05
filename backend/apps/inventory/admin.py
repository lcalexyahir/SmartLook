from django.contrib import admin
from .models import StockItem, InventoryMovement

admin.site.register(StockItem)
admin.site.register(InventoryMovement)