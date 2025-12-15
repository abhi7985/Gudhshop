from django.contrib import admin
from .models import DeliveryPerson

@admin.register(DeliveryPerson)
class DeliveryPersonAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'active')
    search_fields = ('user__username', 'phone')
