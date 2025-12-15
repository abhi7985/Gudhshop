from django.contrib import admin
from .models import Category, Product, CartItem, Order, OrderItem, StoreLocation
from delivery.models import DeliveryPerson


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "created_at")
    list_filter = ("category", "is_active")
    search_fields = ("name",)
    list_editable = ("price", "stock", "is_active")
    prepopulated_fields = {"name": ("name",)}


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "quantity")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ("product", "quantity", "price_at_order")
    can_delete = False
    extra = 0


# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ("id", "full_name", "phone", "status", "payment_method", "created_at")
#     list_filter = ("status", "payment_method", "created_at")
#     search_fields = ("full_name", "phone", "address")
#     readonly_fields = ("created_at",)
#     inlines = [OrderItemInline]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'delivery_person', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'delivery_person__user__username')
    list_editable = ('status', 'delivery_person')

@admin.register(StoreLocation)
class StoreLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude", "delivery_radius_km")
