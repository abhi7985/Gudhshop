from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .twilio_verify import send_otp, check_otp
from store.models import CartItem


def phone_login(request):
    """
    STEP 1: send OTP to phone.

    - If normal form POST (non-AJAX): behave like before, redirect to verify_otp page.
    - If AJAX (popup): return JSON {ok: True / False, error: "..."}.
    """
    if request.method == 'POST':
        phone = request.POST.get('phone')

        # AJAX request?
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        if not phone:
            if is_ajax:
                return JsonResponse({'ok': False, 'error': 'Enter phone number'})
            return render(request, 'accounts/phone_login.html', {'error': 'Enter phone number'})

        try:
            send_otp(phone)
        except Exception as e:
            print('Twilio send error:', e)
            if is_ajax:
                return JsonResponse({'ok': False, 'error': 'Could not send OTP'})
            return render(request, 'accounts/phone_login.html', {'error': 'Could not send OTP'})

        request.session['phone_for_otp'] = phone

        if is_ajax:
            # popup flow just needs success info
            return JsonResponse({'ok': True})

        # old full-page flow
        return redirect('accounts:verify_otp')

    # GET – keep old page for fallback
    return render(request, 'accounts/phone_login.html')


def verify_otp(request):
    """
    STEP 2: verify OTP and log the user in.

    - If AJAX: returns JSON.
    - If normal POST: behaves like earlier, redirects to home or shows error page.
    """
    phone = request.session.get('phone_for_otp')
    if not phone:
        # no phone in session, send user back
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'Session expired. Please try again.'})
        return redirect('accounts:phone_login')

    if request.method == 'POST':
        code = request.POST.get('otp')
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        if check_otp(phone, code):
            user, created = User.objects.get_or_create(username=phone)

            # 1) save old anonymous session key
            old_session_key = request.session.session_key

            # 2) log in (session key may rotate here)
            login(request, user)

            # 3) merge anonymous cart into user cart
            if old_session_key:
                anon_items = CartItem.objects.filter(
                    session_key=old_session_key,
                    user__isnull=True
                )
                print("Merging items from", old_session_key, "count:", anon_items.count())
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

            # clear phone from session
            request.session.pop('phone_for_otp', None)

            if is_ajax:
                return JsonResponse({'ok': True})

            return redirect('/')

        # invalid OTP
        if is_ajax:
            return JsonResponse({'ok': False, 'error': 'Invalid OTP'})

        return render(
            request,
            'accounts/verify_otp.html',
            {'error': 'Invalid OTP', 'phone': phone}
        )

    # GET – keep old page for fallback
    return render(request, 'accounts/verify_otp.html', {'phone': phone})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('/')
