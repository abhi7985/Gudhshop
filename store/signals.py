from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import CartItem

@receiver(user_logged_in)
def merge_cart(sender, user, request, **kwargs):
    # get the key used before login
    
    old_session_key = request.session.get('old_session_key')
    print("merge created ",old_session_key)
    if not old_session_key:
        return

    anon_items = CartItem.objects.filter(
        session_key=old_session_key,
        user__isnull=True
    )

    for item in anon_items:
        existing, created = CartItem.objects.get_or_create(
            user=user,
            product=item.product,
            defaults={'quantity': item.quantity},
        )
        if not created:
            existing.quantity += item.quantity
            existing.save()
        item.delete()

    # clean up
    request.session.pop('old_session_key', None)
