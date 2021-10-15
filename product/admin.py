from .models import Product, ProductType, Purchase, Season, ProductSize, Cashier
from django.contrib import admin
from django.db.models import Sum, F


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'code', 'initial_price', 'markup', 'price_after_markup')
    search_fields = ('type', 'code', 'name')
    autocomplete_fields = ('type',)
    read_only_fields = ('price_after_markup',)


@admin.action(description='Рассчитать запрлату')
def calculate_salary(modeladmin, request, queryset):
    for cashier in queryset:
        p = Purchase.objects.filter(
            date__lte=cashier.end_day,
            date__gte=cashier.start_day,
            cashier=cashier.cashier,
        ).values('cashier').annotate(income=Sum('net_income'))
        if p:
            cashier.salary = p[0]['income']*0.03
        else:
            cashier.salary = 0
        cashier.save()


@admin.register(Cashier)
class CashierAdmin(admin.ModelAdmin):
    list_display = ('cashier', 'start_day', 'end_day', 'salary',)
    raw_id_fields = ('cashier',)
    actions = [calculate_salary]


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('product_size', 'discount_type', 'discount', 'last_price', 'net_income', 'date', 'cashier')
    raw_id_fields = ('product_size', 'cashier')
    read_only_fields = ('last_price', 'net_income', 'date')
    list_filter = ('cashier', 'product_size', 'discount')


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'count')
    raw_id_fields = ('product',)
