from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("pricing/", views.pricing, name="pricing"),
    path("broker-latency/", views.broker_latency, name="broker_latency"),
    path("dedicated-server/", views.dedicated_server, name="dedicated-server"),
    path("affiliate/", views.affiliate, name="affiliate"),
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout_page, name="checkout"),
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/", views.update_cart, name="update_cart"),
    path(
        "cart/remove/<int:package_id>/", views.remove_from_cart, name="remove_from_cart"
    ),
    path("cart/empty/", views.empty_cart, name="empty_cart"),
    path("payment/<uuid:order_id>/", views.payment_page, name="payment_page"),
    path(
        "payment/flutterwave/callback/",
        views.flutterwave_callback,
        name="flutterwave_callback",
    ),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/failed/", views.payment_failed, name="payment_failed"),
    path(
        "payment/failed/<uuid:order_id>/",
        views.payment_failed,
        name="payment_failed_with_order",
    ),
]
