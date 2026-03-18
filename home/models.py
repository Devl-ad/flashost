from django.db import models
import uuid


class Package(models.Model):
    BILLING_CHOICES = [
        ("1m", "1 Month"),
        ("3m", "3 Months"),
        ("6m", "6 Months"),
        ("12m", "12 Months"),
        ("24m", "24 Months"),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)
    ram = models.CharField(max_length=50, blank=True)
    instances = models.CharField(max_length=100, blank=True)
    disk_space = models.CharField(max_length=50, blank=True)
    cpu = models.CharField(max_length=50, blank=True)

    price_1m = models.DecimalField(max_digits=10, decimal_places=2)
    price_3m = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_6m = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_12m = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_24m = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    def get_price(self, cycle):
        mapping = {
            "1m": self.price_1m,
            "3m": self.price_3m,
            "6m": self.price_6m,
            "12m": self.price_12m,
            "24m": self.price_24m,
        }
        return mapping.get(cycle)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    company = models.CharField(max_length=150, blank=True)
    address_1 = models.CharField(max_length=255, blank=True)
    address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    flutterwave_tx_ref = models.CharField(max_length=200, blank=True)
    flutterwave_transaction_id = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    billing_cycle = models.CharField(max_length=10, default="1m")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.unit_price * self.quantity
