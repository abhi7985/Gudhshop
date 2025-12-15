from .models import CartItem

def cart_count(request):
    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        items = CartItem.objects.filter(session_key=request.session.session_key, user__isnull=True)
    count = sum(i.quantity for i in items)
    return {'cart_count': count}
