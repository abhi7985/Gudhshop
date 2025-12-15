from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Product, CartItem,Order, OrderItem, StoreLocation,Category
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .forms import CategoryForm, ProductForm
from delivery.models import DeliveryPerson
from delivery.forms import DeliveryPersonForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt   # or use CSRF token in JS
from .models import CartItem, Product

def owner_required(view_func):
    def _wrapped(request, *args, **kwargs):
        # Only allow superusers
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped

def home(request):
    categories = Category.objects.all().order_by('name')
    products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    cart_quantities = _get_cart_quantities(request)

    # location gate flag from session
    delivery_allowed = request.session.get('delivery_allowed', False)

    return render(request, 'store/home.html', {
        'products': products,
        'categories': categories,
        'active_category': None,
        'cart_quantities': cart_quantities,
        'delivery_allowed': delivery_allowed,
    })

def product_list(request):
  categories = Category.objects.all().order_by('name')
  category_slug = request.GET.get('category')
  q = request.GET.get('q', '')
  products = Product.objects.filter(is_active=True)
  if category_slug:
      products = products.filter(category__slug=category_slug)
  if q:
      products = products.filter(name__icontains=q)
  products = products.order_by('name')
  cart_quantities = _get_cart_quantities(request)
  return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'active_category': category_slug,
        'search_query': q,
        'cart_quantities': cart_quantities,
    })


def cart(request):
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart_items = CartItem.objects.filter(session_key=request.session.session_key)

    cart_total = sum(item.subtotal() for item in cart_items)
    delivery_fee = 25
    grand_total = cart_total + delivery_fee
    total_items = sum(item.quantity for item in cart_items)

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total,
        'total_items': total_items,
    })


@require_POST
def api_check_delivery(request):
    """
    Called from home page JS with lat/lng.
    Stores result in session and returns JSON.
    """
    try:
        lat = float(request.POST.get('lat'))
        lng = float(request.POST.get('lng'))
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Invalid coordinates'})

    # store center + radius in settings.py
    store_lat = getattr(settings, 'STORE_LAT', None)
    store_lng = getattr(settings, 'STORE_LNG', None)
    radius_km = getattr(settings, 'DELIVERY_RADIUS_KM', 5)

    if store_lat is None or store_lng is None:
        return JsonResponse({'ok': False, 'error': 'Store location not configured'})

    dist = _haversine_km(store_lat, store_lng, lat, lng)
    allowed = dist <= radius_km

    request.session['delivery_allowed'] = allowed
    request.session['delivery_lat'] = lat
    request.session['delivery_lng'] = lng

    return JsonResponse({'ok': allowed, 'distance_km': round(dist, 2)})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': 1},
        )
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart_item, created = CartItem.objects.get_or_create(
            session_key=session_key,
            user=None,
            product=product,
            defaults={'quantity': 1},
        )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('store:cart')
def update_cart(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id)

    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    return redirect('store:cart')

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('store:cart')





def _get_cart_items_qs(request):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        return CartItem.objects.filter(session_key=request.session.session_key, user__isnull=True)

def _cart_count(request):
    items = _get_cart_items_qs(request)
    return sum(i.quantity for i in items)
def _get_cart_quantities(request):
    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        items = CartItem.objects.filter(session_key=request.session.session_key, user__isnull=True)
    data = {}
    for ci in items:
        data[ci.product_id] = data.get(ci.product_id, 0) + ci.quantity
    return data


@require_POST
def api_add_to_cart(request):
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)

    qs = _get_cart_items_qs(request)
    if request.user.is_authenticated:
        cart_item, created = qs.get_or_create(product=product, user=request.user, defaults={'quantity': 1})
    else:
        cart_item, created = qs.get_or_create(product=product, session_key=request.session.session_key, user=None, defaults={'quantity': 1})

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return JsonResponse({'ok': True, 'quantity': cart_item.quantity, 'cart_count': _cart_count(request)})

@require_POST
def api_update_cart(request):
    product_id = request.POST.get('product_id')
    action = request.POST.get('action')  # 'increase' or 'decrease'

    product = get_object_or_404(Product, id=product_id)
    qs = _get_cart_items_qs(request)
    cart_item = qs.filter(product=product).first()

    if not cart_item:
        return JsonResponse({'ok': False, 'quantity': 0, 'cart_count': _cart_count(request)})

    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
            return JsonResponse({'ok': True, 'quantity': 0, 'cart_count': _cart_count(request)})
        else:
            cart_item.save()

    return JsonResponse({'ok': True, 'quantity': cart_item.quantity, 'cart_count': _cart_count(request)})



@login_required
def checkout(request):
    
    if request.method == 'POST':
        # get cart items for this user/session
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            cart_items = CartItem.objects.filter(
                session_key=request.session.session_key,
                user__isnull=True
            )

        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('store:product_list')
    
    
    if not request.user.is_authenticated:
        # Redirect anonymous users to login before checkout
        return redirect('store:login')

    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('store:product_list')

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        payment_method = request.POST.get('payment_method', 'COD')
        delivery_slot = request.POST.get('slot', 'morning')
        print(f"Received latitude: {latitude}, longitude: {longitude}")


        # Basic validation:
        if not all([full_name, phone, address, latitude, longitude]):
            messages.error(request, "Please fill all required fields and capture location.")
            return render(request, 'store/checkout.html', {
                'cart_items': cart_items,
                'cart_total': sum(item.subtotal for item in cart_items),
            })

        # Check delivery radius
        store = StoreLocation.objects.first()
        if not store:
            messages.error(request, "Store location is not set. Cannot proceed.")
            return redirect('store:cart')

        distance_km = haversine(latitude, longitude, store.latitude, store.longitude)
        print("the distance km is ",distance_km)
        if distance_km > store.delivery_radius_km:
            return redirect('store:not_deliverable')

        # Create order inside transaction to keep data consistency
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                address=address,
                latitude=latitude,
                longitude=longitude,
                payment_method=payment_method,
                delivery_slot=delivery_slot,
                status='PLACED',
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price_at_order=item.product.price,
                )

            # Clear user's cart
            cart_items.delete()

        return redirect(reverse('store:order_success', kwargs={'order_id': order.id}))

    else:
        # GET request, show form with cart summary
        cart_total = sum(item.subtotal for item in cart_items)
        return render(request, 'store/checkout.html', {
            'cart_items': cart_items,
            'cart_total': cart_total,
        })


def order_success(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'store/order_success.html', {'order': order})


def not_deliverable(request):
    return render(request, 'store/not_deliverable.html')



def my_orders(request):
    if not request.user.is_authenticated:
        # no orders / filters for anonymous users
        return render(request, 'store/my_orders.html', {
            'orders': [],
            'current_order': None,
            'status_filter': 'ALL',
        })

    status_filter = request.GET.get('status', 'ALL')

    qs = Order.objects.filter(user=request.user).order_by('-created_at')
    if status_filter == 'DELIVERED':
        qs = qs.filter(status='DELIVERED')
    elif status_filter == 'CANCELLED':
        qs = qs.filter(status='CANCELLED')
    elif status_filter == 'PROCESSING':
        qs = qs.exclude(status__in=['DELIVERED', 'CANCELLED'])

    orders = qs
    current_order = orders.filter(
        status__in=['PLACED', 'CONFIRMED', 'OUT_FOR_DELIVERY']
    ).first()

    context = {
        'orders': orders,
        'current_order': current_order,
        'status_filter': status_filter,
    }
    return render(request, 'store/my_orders.html', context)

import math

def haversine(lat1, lon1, lat2, lon2):
    # Converts degrees to radians and calculates distance in km
    R = 6371  # Earth radius in km
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def _haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))






#-----admin panel

@owner_required
def owner_dashboard(request):
    category_count = Category.objects.count()
    product_count = Product.objects.count()
    context = {
        'category_count': category_count,
        'product_count': product_count,
    }
    return render(request, 'store/owner/dashboard.html', context)

# ----- Category CRUD -----

@owner_required
def owner_category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'store/owner/category_list.html', {'categories': categories})

@owner_required
def owner_category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('store:owner_category_list')
    else:
        form = CategoryForm()
    return render(request, 'store/owner/category_form.html', {'form': form, 'title': 'Add Category'})

@owner_required
def owner_category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            return redirect('store:owner_category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'store/owner/category_form.html', {'form': form, 'title': 'Edit Category'})

@owner_required
def owner_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('store:owner_category_list')
    return render(request, 'store/owner/confirm_delete.html', {'object': category, 'type': 'Category'})

# ----- Product CRUD -----

@owner_required
def owner_product_list(request):
    products = Product.objects.select_related('category').order_by('name')
    return render(request, 'store/owner/product_list.html', {'products': products})

@owner_required
def owner_product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('store:owner_product_list')
    else:
        form = ProductForm()
    return render(request, 'store/owner/product_form.html', {'form': form, 'title': 'Add Product'})

@owner_required
def owner_product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('store:owner_product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/owner/product_form.html', {'form': form, 'title': 'Edit Product'})

@owner_required
def owner_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('store:owner_product_list')
    return render(request, 'store/owner/confirm_delete.html', {'object': product, 'type': 'Product'})


@owner_required
def owner_order_list(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        delivery_person_id = request.POST.get('delivery_person')

        order = get_object_or_404(Order, id=order_id)

        # update status
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status

        # update delivery person
        if delivery_person_id:
            dp = get_object_or_404(DeliveryPerson, id=delivery_person_id)
            order.delivery_person = dp
        else:
            order.delivery_person = None

        order.save()

    orders = Order.objects.select_related('user', 'delivery_person').order_by('-created_at')
    delivery_people = DeliveryPerson.objects.filter(active=True).select_related('user')

    context = {
        'orders': orders,
        'delivery_people': delivery_people,
    }
    return render(request, 'store/owner/order_list.html', context)


#------------  for add delivery person by owner 



@owner_required
def owner_deliveryperson_list(request):
    persons = DeliveryPerson.objects.select_related('user').order_by('user__username')
    return render(request, 'store/owner/deliveryperson_list.html', {'persons': persons})


@owner_required
def owner_deliveryperson_create(request):
    if request.method == 'POST':
        form = DeliveryPersonForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('store:owner_deliveryperson_list')
    else:
        form = DeliveryPersonForm()
    return render(request, 'store/owner/deliveryperson_form.html', {
        'form': form,
        'title': 'Add Delivery Person',
    })


@owner_required
def owner_deliveryperson_update(request, pk):
    person = get_object_or_404(DeliveryPerson, pk=pk)
    if request.method == 'POST':
        form = DeliveryPersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            return redirect('store:owner_deliveryperson_list')
    else:
        form = DeliveryPersonForm(instance=person)
    return render(request, 'store/owner/deliveryperson_form.html', {
        'form': form,
        'title': 'Edit Delivery Person',
    })


@owner_required
def owner_deliveryperson_delete(request, pk):
    person = get_object_or_404(DeliveryPerson, pk=pk)
    if request.method == 'POST':
        person.delete()
        return redirect('store:owner_deliveryperson_list')
    return render(request, 'store/owner/confirm_delete.html', {
        'object': person,
        'type': 'Delivery Person',
    })
