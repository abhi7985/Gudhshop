from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes

from .models import Category, Product, Order, OrderItem
from .api_serializers import (
    CategorySerializer,
    ProductSerializer,
    OrderSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_categories(request):
    qs = Category.objects.all().order_by("name")
    serializer = CategorySerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_products(request):
    category_id = request.GET.get("category")
    qs = Product.objects.filter(is_active=True)

    if category_id:
        qs = qs.filter(category_id=category_id)

    qs = qs.order_by("name")
    serializer = ProductSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_orders_list(request):
    qs = Order.objects.filter(user=request.user).order_by("-created_at")
    serializer = OrderSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def api_orders_create(request):
    """
    Create order from app checkout.
    Expected JSON:
    {
      "full_name": "...",
      "phone": "...",
      "address": "...",
      "payment_method": "COD",
      "delivery_slot": "morning",
      "items": [
        {"product_id": 1, "quantity": 2},
        {"product_id": 5, "quantity": 1}
      ]
    }
    """
    data = request.data

    items_data = data.get("items") or []
    if not items_data:
        return Response(
            {"detail": "No items provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        full_name=data.get("full_name", ""),
        phone=data.get("phone", ""),
        address=data.get("address", ""),
        latitude=None,   # app will send later when you add map
        longitude=None,
        payment_method=data.get("payment_method", "COD"),
        status="PLACED",
        delivery_slot=data.get("delivery_slot", "morning"),
    )

    for item in items_data:
        product_id = item.get("product_id")
        qty = int(item.get("quantity", 1))
        if not product_id or qty <= 0:
            continue

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            continue

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=qty,
            price_at_order=product.price,
        )
#nothing changed here
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
