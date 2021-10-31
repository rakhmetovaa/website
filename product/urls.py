from django.urls import path
from .views import (PurchaseChartView, CashierPurchaseChartView, home, SizePurchaseChartView, index,
                    DiscountPurchaseChartView, DayPurchaseChartView, send_email)
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('purchase/', PurchaseChartView.as_view(), name='purchase'),
    path('cashier/', CashierPurchaseChartView.as_view(), name='cashier'),
    path('size/', SizePurchaseChartView.as_view(), name='size'),
    path('discount/', DiscountPurchaseChartView.as_view(), name='discount'),
    path('day/', DayPurchaseChartView.as_view(), name='day'),
    path('face-recognition/', index, name="index"),
    path('', home, name='shop-home'),
    path("login/", auth_views.LoginView.as_view(template_name="users/login.html"), name="login"),
    path("send-email/", send_email, name="send-email"),

]