import numpy as np
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
        context['qs'] = Purchase.objects.values(item=F('product_size__product__name')).annotate(
            income=Sum('net_income')).order_by('item')
        context['title'] = 'Продукты'
        return context


class CashierPurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('cashier__username')).annotate(income=Sum('net_income')).order_by('item')
        context['title'] = 'Кассиры'
        return context


class HourPurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Время'
        morning = int(
            Purchase.objects.filter(
                date__hour__lt=12,
                date__hour__gte=0
            ).aggregate(
                total=Sum('net_income')
            ).get('total')
            or 0
        )
        noon = int(
            Purchase.objects.filter(
                date__hour__lt=18,
                date__hour__gte=12
            ).aggregate(
                total=Sum('net_income')
            ).get('total')
            or 0
        )
        evening = int(
            Purchase.objects.filter(
                date__hour__lt=24,
                date__hour__gte=18
            ).aggregate(
                total=Sum('net_income')
            ).get('total')
            or 0
        )
        res = [{'item': 'утро', 'income': str(morning)}, {'item': 'обед', 'income': str(noon)}, {'item': 'вечер', 'income': str(evening)}]
        context['qs'] = res
        return context


class SizePurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('product_size__size')).annotate(income=Count('id')).order_by('item')
        context['title'] = 'Размеры'
        return context


class DiscountPurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('discount_type')).annotate(income=Count('id')).order_by('item')
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
            filename = str(request.user.id) + f'.{i}.jpg'  # I assume you have a way of picking unique filenames
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
            filename = randomString() + '.jpg'  # I assume you have a way of picking unique filenames
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


def slope(x, y):
    x = np.array(x)
    y = np.array(y)
    m = (((np.mean(x) * np.mean(y)) - np.mean(x*y))/((np.mean(x) * np.mean(x)) - np.mean(x*x)))
    m = round(m, 2)
    b = np.mean(y) - np.mean(x)*m
    b = round(b, 2)
    return m, b


@csrf_exempt
def net_income(request, from_date="2020-11-02", to_date="2020-11-02", expences=0, *args, **kwargs):
    if to_date <= from_date:
        return render(request, "product/net_income.html", {})
    f_from_date = from_date
    t_to_date = to_date
    from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d')
    labels = []
    net_income_labels = []
    min_number = 15
    if (to_date - from_date).days >= min_number:
        diff = (to_date - from_date) // min_number
    else:
        diff = datetime.timedelta(days=1)
    temp = from_date
    while temp <= to_date:
        labels.append(temp)
        temp += diff
    exp_diff = expences / len(labels)
    for day_count in range(len(labels) - 1):
        net_income_labels.append(
            int((Purchase.objects.filter(
                date__lt=labels[day_count + 1],
                date__gte=labels[day_count]).aggregate(
                total=Sum('net_income')
            ).get('total') or 0) - exp_diff)
        )
    net_income = sum(net_income_labels)
    x = [i for i in range(len(net_income_labels))]
    if len(x) > 1:
        m, b = slope(x, net_income_labels)
    else:
        m, b = 0, 0
    for i in range(1, 6):
        labels.append(to_date + i * diff)
    predict_labels = [int((i * m + b) or 0) for i in range(len(labels))]
    context = {
        'labels': labels,
        'net_income': net_income,
        'net_income_labels': net_income_labels,
        'predict_labels': predict_labels,
        'from_date': f_from_date,
        'to_date': t_to_date,
        'expences': expences,
    }
    return render(request, "product/net_income.html", context)
