from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes

from .models import Address, Category, Product, Order, OrderItem
from .api_serializers import (
    CategorySerializer,
    ProductSerializer,
    OrderSerializer,
    AddressSerializer
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_orders_create(request):
    data = request.data
    items_data = data.get("items") or []
    if not items_data:
        return Response({"detail": "No items provided."},
                        status=status.HTTP_400_BAD_REQUEST)

    address_id = data.get("address_id")
    address_obj = None

    if address_id:
        try:
            address_obj = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            pass

    if address_obj:
        full_name = address_obj.full_name
        phone = address_obj.phone
        address_str = address_obj.address_line
        lat = address_obj.latitude
        lng = address_obj.longitude
    else:
        full_name = data.get("full_name", "")
        phone = data.get("phone", "")
        address_str = data.get("address", "")
        lat = None
        lng = None

    order = Order.objects.create(
        user=request.user,
        address_obj=address_obj,
        full_name=full_name,
        phone=phone,
        address=address_str,
        latitude=lat,
        longitude=lng,
        payment_method=data.get("payment_method", "COD"),
        status="PLACED",
        delivery_slot=data.get("delivery_slot", "morning"),
    )

    # items loop unchanged...

    data = request.data
    items_data = data.get("items") or []
    if not items_data:
        return Response({"detail": "No items provided."},
                        status=status.HTTP_400_BAD_REQUEST)

    # request.user is now the authenticated user from token
    order = Order.objects.create(
        user=request.user,
        full_name=data.get("full_name", ""),
        phone=data.get("phone", ""),
        address=data.get("address", ""),
        latitude=None,
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

    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_address_list(request):
    addresses = Address.objects.filter(user=request.user).order_by('-created_at')
    serializer = AddressSerializer(addresses, many=True)
    return Response(serializer.data)



@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_address_create(request):
    """
    Body: {
      "full_name": "...",
      "phone": "...",
      "address_line": "...",
      "latitude": null,
      "longitude": null
    }
    """
    data = request.data.copy()
    data["user"] = request.user.id  # bind to current user

    serializer = AddressSerializer(data=data)
    if serializer.is_valid():
        address = serializer.save(user=request.user)

        # optional: make it default if this is first address
        if not Address.objects.filter(user=request.user).exclude(id=address.id).exists():
            address.is_default = True
            address.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = OrderSerializer(order)
    return Response(serializer.data)


