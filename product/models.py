from django.db import models
# Create your models here.
from django.contrib.auth.models import User
from django.utils import timezone


class ProductType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class Season(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class Product(models.Model):
    name = models.CharField(max_length=255)
    type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    code = models.IntegerField()
    brand = models.CharField(max_length=255)
    initial_price = models.IntegerField()
    markup = models.IntegerField()
    price_after_markup = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} -- {self.code}"

    def save(self, *args, **kwargs):
        self.price_after_markup = self.initial_price * (100 + self.markup) / 100
        super(Product, self).save(*args, **kwargs)


class Cashier(models.Model):
    cashier = models.OneToOneField(User, on_delete=models.CASCADE)
    salary = models.IntegerField(default=0)
    start_day = models.DateTimeField(default=timezone.now)
    end_day = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.cashier.username


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    size = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} {self.size} "


class Purchase(models.Model):
    CHOICES = (
        ('amount', 'Сумма'),
        ('percentage', 'Процент'),
        ('none', 'Без скидки'),
    )
    product_size = models.ForeignKey(ProductSize, on_delete=models.RESTRICT)
    discount_type = models.CharField(max_length=16, choices=CHOICES, default='none')
    discount = models.IntegerField(default=0)
    last_price = models.IntegerField(blank=True, null=True)
    net_income = models.IntegerField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    cashier = models.ForeignKey(User, on_delete=models.RESTRICT)

    def save(self, *args, **kwargs):
        if self.discount_type == 'percentage':
            self.last_price = self.product_size.product.price_after_markup * (100 - self.discount) / 100
        if self.discount_type == 'amount':
            self.last_price = self.product_size.product.price_after_markup - self.discount
        if self.discount_type == 'none':
            self.last_price = self.product_size.product.price_after_markup
        self.net_income = self.last_price - self.product_size.product.initial_price
        if not self.id:
            self.product_size.count -= 1
            self.product_size.save()
        super(Purchase, self).save(*args, **kwargs)

    def __str__(self):
        return f"Product:{self.product_size} -- LastPrice:{self.last_price}"


