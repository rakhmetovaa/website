from django.urls import path
from .views import (PurchaseChartView, CashierPurchaseChartView, home, SizePurchaseChartView, index,
                    DiscountPurchaseChartView, HourPurchaseChartView, send_email, adding_face, net_income)
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('purchase/', PurchaseChartView.as_view(), name='purchase'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('data-migrate/', views.data_migrate, name='data-migrate'),
    path('import-excel/', views.import_excel, name='import-excel'),
    path('clients/', views.clients, name='clients'),
    path('cashier/', CashierPurchaseChartView.as_view(), name='cashier'),
    path('size/', SizePurchaseChartView.as_view(), name='size'),
    path('discount/', DiscountPurchaseChartView.as_view(), name='discount'),
    path('hour/', HourPurchaseChartView.as_view(), name='hour'),
    path('face-recognition/', index, name="index"),
    path('adding-face/', adding_face, name="adding-face"),
    path('', home, name='shop-home'),
    path('net-income/<int:expences>/<str:from_date>/<str:to_date>/', net_income, name='net-income'),
    path('net-income/', net_income, name='net-income'),
    path("login/", auth_views.LoginView.as_view(template_name="users/signin.html"), name="login"),
    path('logout/', auth_views.LogoutView.as_view(template_name="product/store.html"), name="logout"),
    path("send-email/", send_email, name="send-email"),

]
