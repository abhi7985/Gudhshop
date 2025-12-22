from django.urls import path
from . import views
from . import api_views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('cart/', views.cart, name='cart'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('api/check-delivery/', views.api_check_delivery, name='api_check_delivery'),

    path('api/cart/add/', views.api_add_to_cart, name='api_add_to_cart'),
    path('api/cart/update/', views.api_update_cart, name='api_update_cart'),
    
    path('cart/update/<int:item_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('not-deliverable/', views.not_deliverable, name='not_deliverable'),
    
    
    #---admin
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/categories/', views.owner_category_list, name='owner_category_list'),
    path('owner/categories/add/', views.owner_category_create, name='owner_category_create'),
    path('owner/categories/<int:pk>/edit/', views.owner_category_update, name='owner_category_update'),
    path('owner/categories/<int:pk>/delete/', views.owner_category_delete, name='owner_category_delete'),

    path('owner/products/', views.owner_product_list, name='owner_product_list'),
    path('owner/products/add/', views.owner_product_create, name='owner_product_create'),
    path('owner/products/<int:pk>/edit/', views.owner_product_update, name='owner_product_update'),
    path('owner/products/<int:pk>/delete/', views.owner_product_delete, name='owner_product_delete'),
    path('owner/orders/', views.owner_order_list, name='owner_order_list'),
    
    # For delivery person add in admin dashboard 
    path('owner/delivery-persons/', views.owner_deliveryperson_list, name='owner_deliveryperson_list'),
    path('owner/delivery-persons/add/', views.owner_deliveryperson_create, name='owner_deliveryperson_create'),
    path('owner/delivery-persons/<int:pk>/edit/', views.owner_deliveryperson_update, name='owner_deliveryperson_update'),
    path('owner/delivery-persons/<int:pk>/delete/', views.owner_deliveryperson_delete, name='owner_deliveryperson_delete'),



    # API endpoints for mobile app
    path("api/categories/", api_views.api_categories, name="api_categories"),
    path("api/products/", api_views.api_products, name="api_products"),
    path("api/orders/", api_views.api_orders_list, name="api_orders_list"),
    path("api/orders/create/", api_views.api_orders_create, name="api_orders_create"),



    path("api/addresses/", api_views.api_address_list, name="api_address_list"),
    path("api/addresses/create/", api_views.api_address_create, name="api_address_create"),
    # Order detail
    path("api/orders/<int:order_id>/", api_views.api_order_detail, name="api_order_detail"),
]
