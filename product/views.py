from django.views.generic import TemplateView
from .models import Purchase, Product
from django.db.models import Sum, F, Count
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import itertools
import datetime


class PurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('product_size__product__name')).annotate(income=Sum('net_income'))
        print(context['qs'])
        context['title'] = 'Продукты'
        return context


class CashierPurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('cashier__username')).annotate(income=Sum('net_income'))
        print(context['qs'])
        context['title'] = 'Кассиры'
        return context


class DayPurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Время'
        objs = Purchase.objects.filter()
        groups = itertools.groupby(objs, lambda x: x.date.hour)
        res = []
        for group, matches in groups:  # now you are traversing the list ...
            key = str(group) + ':00'
            res.append({'item': key, 'income': sum(1 for _ in matches)})
        res = sorted(res, key=lambda d: d['item'])
        context['qs'] = res
        print(context['qs'])
        return context


class SizePurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('product_size__size')).annotate(income=Count('id'))
        print(context['qs'])
        context['title'] = 'Размеры'
        return context


class DiscountPurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('discount_type')).annotate(income=Count('id'))
        print(context['qs'])
        context['title'] = 'Скидки'
        return context


@login_required
def home(request):
    context = {
        "posts": Product.objects.all()
    }
    return render(request, "product/store.html", context)
