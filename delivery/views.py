from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from store.models import Order
from .models import DeliveryPerson
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
@login_required
def delivery_dashboard(request):
    # check user is a delivery person
    try:
        delivery_person = request.user.deliveryperson
    except DeliveryPerson.DoesNotExist:
        return redirect('store:home')  # or render permission denied

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id, delivery_person=delivery_person)

        # Don't allow changes once delivered or cancelled
        if order.status in ['DELIVERED', 'CANCELLED']:
            return redirect('delivery:dashboard')

        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()

    orders = Order.objects.filter(delivery_person=delivery_person).order_by('-created_at')
    return render(request, 'delivery/dashboard.html', {'orders': orders})


def delivery_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check user is delivery person
            if hasattr(user, 'deliveryperson'):
                login(request, user)
                return redirect('delivery:dashboard')
            else:
                error = "You are not authorized as a delivery person."
        else:
            error = "Invalid username or password."
        return render(request, 'delivery/login.html', {'error': error})

    return render(request, 'delivery/login.html')

@login_required
def delivery_logout(request):
    logout(request)
    return redirect('delivery:login')