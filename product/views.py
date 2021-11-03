from django.views.generic import TemplateView

from .forms import EmailSendForm
from .models import Purchase, Product
from django.db.models import Sum, F, Count
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
import itertools
import datetime
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
import base64
import random
import string
from .models import *
from django.http import JsonResponse
from face_recognition import validate_face, create_dataset, train_faces
from django.core.mail import send_mail
from shop.settings import EMAIL_HOST


class PurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('product_size__product__name')).annotate(income=Sum('net_income'))
        context['title'] = 'Продукты'
        return context


class CashierPurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('cashier__username')).annotate(income=Sum('net_income'))
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
        return context


class SizePurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('product_size__size')).annotate(income=Count('id'))
        context['title'] = 'Размеры'
        return context


class DiscountPurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('discount_type')).annotate(income=Count('id'))
        context['title'] = 'Скидки'
        return context


def home(request):
    if not request.user.is_authenticated:
        return redirect('index')
    context = {
        "posts": Product.objects.all()
    }
    return render(request, "product/store.html", context)

@login_required
@csrf_exempt
def adding_face(request):
    if request.method == "POST":
        data = request.body
        data = json.loads(data[0:len(data)])
        temp = len('data:image/jpeg;base64,')
        i = 0
        for d in data:
            d = d[temp:len(d)]
            imgdata = base64.b64decode(d)
            filename = str(request.user.id)+f'.{i}.jpg'  # I assume you have a way of picking unique filenames
            with open(f"media/{filename}", 'wb') as f:
                f.write(imgdata)
            i += 1
        create_dataset(request.user.id)
        train_faces()
        return JsonResponse({'data': 'Error'})
    return render(request, 'adding_face.html')


@csrf_exempt
def index(request):
    if request.method == "POST":
        data = request.body
        data = json.loads(data[0:len(data)])
        temp = len('data:image/jpeg;base64,')
        for d in data:
            d = d[temp:len(d)]
            imgdata = base64.b64decode(d)
            filename = randomString()+'.jpg'  # I assume you have a way of picking unique filenames
            with open(f"media/{filename}", 'wb') as f:
                f.write(imgdata)
            confidence = validate_face(filename)
            print(confidence)
            if confidence >= 50:
                return JsonResponse({'data': 'Success'})
        return JsonResponse({'data': 'Error'})
    return render(request, 'index.html')


def randomString(stringLength=5):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def send_email(request):
    if request.method == "POST":
        form = EmailSendForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            subject = form.cleaned_data.get("subject")
            message = form.cleaned_data.get("message")

            send_mail(subject, message, EMAIL_HOST, [email])
            return redirect('/')
    else:
        form = EmailSendForm()
    return render(request, 'email.html', {'form': form})
