from django.db import models
# Create your models here.
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class ProductType(models.Model):
    name = models.CharField(max_length=255, verbose_name='наименование')

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('тип продукта')
        verbose_name_plural = _('типы продуктов')


class Season(models.Model):
    name = models.CharField(max_length=255, verbose_name='название')

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = _('сезон')
        verbose_name_plural = _('сезоны')


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='название')
    type = models.ForeignKey(ProductType, on_delete=models.CASCADE, verbose_name='тип продукта')
    season = models.ForeignKey(Season, on_delete=models.CASCADE, verbose_name='сезон')
    code = models.IntegerField(verbose_name='код')
    brand = models.CharField(max_length=255, verbose_name='бренд')
    initial_price = models.IntegerField(verbose_name='начальная цена')
    markup = models.IntegerField(verbose_name='накрутка')
    price_after_markup = models.IntegerField(null=True, blank=True, verbose_name='цена после накрутки')

    def __str__(self):
        return f"{self.name} -- {self.code}"

    def save(self, *args, **kwargs):
        self.price_after_markup = self.initial_price * (100 + self.markup) / 100
        super(Product, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('продукт')
        verbose_name_plural = _('продукты')


class Cashier(models.Model):
    cashier = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='кассир')
    salary = models.IntegerField(default=0, verbose_name='запрлата')
    start_day = models.DateTimeField(default=timezone.now, verbose_name='первый день')
    end_day = models.DateTimeField(default=timezone.now, verbose_name='последний день')

    def __str__(self):
        return self.cashier.username

    class Meta:
        verbose_name = _('кассира')
        verbose_name_plural = _('кассиры')


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='продукт')
    count = models.IntegerField(default=0, verbose_name='количество')
    size = models.IntegerField(default=0, verbose_name='размер')

    def __str__(self):
        return f"{self.product.name} {self.size} "

    class Meta:
        verbose_name = _('продукт с размером')
        verbose_name_plural = _('продукты с размерами')


class Purchase(models.Model):
    CHOICES = (
        ('amount', 'Сумма'),
        ('percentage', 'Процент'),
        ('none', 'Без скидки'),
    )
    product_size = models.ForeignKey(ProductSize, on_delete=models.RESTRICT, verbose_name='продукт с размером')
    discount_type = models.CharField(max_length=16, choices=CHOICES, default='none', verbose_name='тип скидки')
    discount = models.IntegerField(default=0, verbose_name='скидка')
    last_price = models.IntegerField(blank=True, null=True, verbose_name='окончательная цена')
    net_income = models.IntegerField(blank=True, null=True, verbose_name='чистая прибыль')
    date = models.DateTimeField(auto_now_add=True, verbose_name='время продажи')
    cashier = models.ForeignKey(User, on_delete=models.RESTRICT, verbose_name='кассир')

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

    class Meta:
        verbose_name = _('продажу')
        verbose_name_plural = _('продажи')


