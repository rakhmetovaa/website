from django.urls import path
from .views import (PurchaseChartView, CashierPurchaseChartView, home, SizePurchaseChartView,
                    DiscountPurchaseChartView, DayPurchaseChartView)
urlpatterns = [
    path('purchase/', PurchaseChartView.as_view(), name='purchase'),
    path('cashier/', CashierPurchaseChartView.as_view(), name='cashier'),
    path('size/', SizePurchaseChartView.as_view(), name='size'),
    path('discount/', DiscountPurchaseChartView.as_view(), name='discount'),
    path('day/', DayPurchaseChartView.as_view(), name='day'),
    path('', home, name='shop-home')
]