from django.urls import path
from .views import (PurchaseChartView, CashierPurchaseChartView, home, SizePurchaseChartView, index,
                    DiscountPurchaseChartView, DayPurchaseChartView)
urlpatterns = [
    path('purchase/', PurchaseChartView.as_view(), name='purchase'),
    path('cashier/', CashierPurchaseChartView.as_view(), name='cashier'),
    path('size/', SizePurchaseChartView.as_view(), name='size'),
    path('discount/', DiscountPurchaseChartView.as_view(), name='discount'),
    path('day/', DayPurchaseChartView.as_view(), name='day'),
    path('face-recognition/', index, name="index"),
    path('', home, name='shop-home')
]