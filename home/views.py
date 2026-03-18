import requests
import uuid
import urllib.parse
from django.http import HttpResponse
import json
from django.conf import settings
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from .models import Package, Order, OrderItem


def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    return render(
        request,
        "payment.html",
        {
            "order": order,
            "flutterwave_public_key": settings.FLW_PUBLIC_KEY,
            "redirect_url": request.build_absolute_uri(
                "/payment/flutterwave/callback/"
            ),
        },
    )


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def checkout_page(request):
    cart = request.session.get("cart", {})
    items = []
    total = Decimal("0.00")

    for package_id, cart_item in cart.items():
        package = get_object_or_404(Package, id=package_id)
        billing_cycle = cart_item.get("billing_cycle", "1m")
        quantity = int(cart_item.get("quantity", 1))

        unit_price = package.get_price(billing_cycle)
        if unit_price is None:
            continue

        subtotal = unit_price * quantity
        total += subtotal

        items.append(
            {
                "package": package,
                "billing_cycle": billing_cycle,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            }
        )

    if not items:
        return redirect("cart")

    form_data = {}

    if request.method == "POST":
        form_data = request.POST.copy()

        firstname = request.POST.get("firstname", "").strip()
        lastname = request.POST.get("lastname", "").strip()
        email = request.POST.get("email", "").strip()
        phonenumber = request.POST.get("phonenumber", "").strip()
        companyname = request.POST.get("companyname", "").strip()
        address1 = request.POST.get("address1", "").strip()
        address2 = request.POST.get("address2", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        postcode = request.POST.get("postcode", "").strip()
        country = request.POST.get("country", "").strip()
        notes = request.POST.get("notes", "").strip()
        accepttos = request.POST.get("accepttos")

        if not firstname or not lastname or not email or not phonenumber:
            return render(
                request,
                "checkout.html",
                {
                    "total": total,
                    "items": items,
                    "form_data": form_data,
                    "user_ip": get_client_ip(request),
                    "error_message": "Please fill in all required personal information.",
                },
            )

        if not address1 or not city or not state or not postcode or not country:
            return render(
                request,
                "checkout.html",
                {
                    "total": total,
                    "items": items,
                    "form_data": form_data,
                    "user_ip": get_client_ip(request),
                    "error_message": "Please fill in your billing address.",
                },
            )

        if not accepttos:
            return render(
                request,
                "checkout.html",
                {
                    "total": total,
                    "items": items,
                    "form_data": form_data,
                    "user_ip": get_client_ip(request),
                    "error_message": "You must agree to the Terms of Service.",
                },
            )

        order = Order.objects.create(
            first_name=firstname,
            last_name=lastname,
            email=email,
            phone=phonenumber,
            company=companyname,
            address_1=address1,
            address_2=address2,
            city=city,
            state=state,
            postcode=postcode,
            country=country,
            notes=notes,
            total_amount=total,
            currency="USD",
            status="pending",
        )
        order.flutterwave_tx_ref = f"order-{order.id}"
        order.save(update_fields=["flutterwave_tx_ref"])

        for item in items:
            OrderItem.objects.create(
                order=order,
                package=item["package"],
                billing_cycle=item["billing_cycle"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )

        request.session["pending_order_id"] = str(order.id)
        return redirect("payment_page", order_id=order.id)

    return render(
        request,
        "checkout.html",
        {
            "total": total,
            "items": items,
            "form_data": form_data,
            "user_ip": get_client_ip(request),
        },
    )


def add_to_cart(request):
    if request.method == "POST":
        package_id = request.POST.get("package_id")
        billing_cycle = request.POST.get("billing_cycle", "1m")

        package = get_object_or_404(Package, id=package_id)
        price = package.get_price(billing_cycle)

        if price is None:
            return redirect("pricing")

        cart = request.session.get("cart", {})

        if package_id in cart:
            cart[package_id]["quantity"] += 1
            cart[package_id]["billing_cycle"] = billing_cycle
        else:
            cart[package_id] = {
                "billing_cycle": billing_cycle,
                "quantity": 1,
            }

        request.session["cart"] = cart
        request.session.modified = True
        return redirect("cart")


def update_cart(request):
    if request.method == "POST":
        cart = request.session.get("cart", {})

        for package_id in list(cart.keys()):
            qty_value = request.POST.get(f"qty_{package_id}")

            if qty_value is not None:
                try:
                    qty = int(qty_value)

                    if qty > 0:
                        cart[package_id]["quantity"] = qty
                    else:
                        del cart[package_id]

                except ValueError:
                    pass

        request.session["cart"] = cart
        request.session.modified = True

    return redirect("cart")


def remove_from_cart(request, package_id):
    cart = request.session.get("cart", {})
    package_id = str(package_id)

    if package_id in cart:
        del cart[package_id]

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def empty_cart(request):
    request.session["cart"] = {}
    request.session.modified = True
    return redirect("cart")


def home(request):
    return render(request, "index.html")


def pricing(request):
    package = Package.objects.all()
    return render(request, "pricing.html", {"packages": package})


def broker_latency(request):
    return render(request, "broker-latency.html")


def dedicated_server(request):
    return render(request, "dedicated-server.html")


def affiliate(request):
    return render(request, "affiliate.html")


def cart(request):
    cart = request.session.get("cart", {})
    items = []
    total = Decimal("0.00")

    for package_id, item in cart.items():
        package = get_object_or_404(Package, id=package_id)
        billing_cycle = item["billing_cycle"]
        quantity = item["quantity"]
        unit_price = package.get_price(billing_cycle)
        subtotal = unit_price * quantity
        total += subtotal

        items.append(
            {
                "package": package,
                "billing_cycle": billing_cycle,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            }
        )

    return render(
        request,
        "cart.html",
        {
            "items": items,
            "total": total,
        },
    )


def payment_success(request):
    return render(request, "payment_success.html")


def payment_failed(request, order_id=None):
    order = None
    if order_id:
        order = get_object_or_404(Order, id=order_id)
    return render(request, "payment_failed.html", {"order": order})


def flutterwave_callback(request):

    response_data = request.GET.get("response")

    if not response_data:
        return HttpResponse("Flutterwave response missing.")

    # decode the URL encoded JSON
    decoded = urllib.parse.unquote(response_data)

    try:
        data = json.loads(decoded)
    except Exception:
        return HttpResponse("Invalid Flutterwave response.")

    print("FLUTTERWAVE DATA:", data)

    status = data.get("status")
    tx_ref = data.get("txRef")
    transaction_id = data.get("id")

    if not tx_ref:
        return HttpResponse("txRef missing from Flutterwave response.")

    order = get_object_or_404(Order, flutterwave_tx_ref=tx_ref)

    if status != "successful":
        order.status = "failed"
        order.save(update_fields=["status"])
        return redirect("payment_failed_with_order", order_id=order.id)

    # mark order paid
    order.status = "paid"
    order.flutterwave_transaction_id = str(transaction_id)
    order.save(update_fields=["status", "flutterwave_transaction_id"])

    # clear cart
    request.session["cart"] = {}
    request.session.modified = True

    return redirect("payment_success")
