import numpy as np
from django.views.generic import TemplateView
from .forms import EmailSendForm, GraphFilterForm2, GraphFilterForm3,GraphFilterForm
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
import pandas as pd
import sklearn
from sklearn.linear_model import LinearRegression


# def dashboard(request):
#     if request.GET.get('dateFrom') != None and request.GET.get('dateTo') != None:
#         first_date = request.GET.get('dateFrom')
#         last_date = request.GET.get('dateTo')
#         purchases = Purchase.objects.filter(date__range=(first_date, last_date)).order_by('date')
#     else:
#         purchases = Purchase.objects.order_by('date')
#     dates = []
#     data = []
#     incomes = {
#         'month': [],
#         'income': []
#     }
#     unique_list = []
#     for x in purchases:
#         if x.date.month not in unique_list:
#             unique_list.append(x.date.month)
#     for m in unique_list:
#         incomes['month'].append(m)
#         for p in purchases:
#             if unique_list.__contains__(p.date.month) and p.date.month == m:
#                 date_string = p.date.strftime("%m")
#                 try:
#                     ind = dates.index(date_string)
#                     data[ind] = data[ind] + p.product_size.product.price_after_markup * p.product_size.count
#                     incomes['income'][ind] = (data[ind])
#                 except ValueError:
#                     dates.append(date_string)
#                     data.append(p.product_size.product.price_after_markup * p.product_size.count)
#                     incomes['income'].append(p.product_size.product.price_after_markup * p.product_size.count)
#
#     monthPrediction = []
#     incomesMonth = incomes['income'].copy()
#     preIncomesMonth = incomes['income'].copy()
#
#     for i in range(4, 11):
#         df = pd.DataFrame(incomes)
#         X = df[['month']]
#         Y = df['income']
#         X = df.iloc[:, 0].values.reshape(-1, 1)  # values converts it into a numpy array
#         Y = df.iloc[:, 1].values.reshape(-1, 1)
#         clf = LinearRegression()
#         clf.fit(X, Y)
#         result = clf.predict([[i]])
#         monthPrediction.append(int((result[0])[0]))
#         preIncomesMonth.append(int((result[0])[0]))
#         incomes['month'].append(i)
#         incomes['income'].append(int((result[0])[0]))
#     current_user = request.user
#     monthsString = []
#     for m in incomes['month']:
#         monthsString.append(get_month(m))
#     filterForm = GraphFilterForm()
#     return render(request, 'product/dashboard.html',
#                   {'title': 'qwerty', 'data': data, 'dates': dates, 'user': current_user, 'filterForm': filterForm,
#                    'months': monthsString
#                       , 'monthPrediction': monthPrediction, 'result': (int((result[0])[0])), 'incomesMonth': incomesMonth,
#                    'preIncomesMonth': preIncomesMonth})

def dashboard(request):
    if request.GET.get('dateFrom') != None and request.GET.get('dateTo') != None:
        first_date = request.GET.get('dateFrom')
        last_date = request.GET.get('dateTo')
        purchases = Purchase.objects.filter(date__range=(first_date, last_date)).order_by('date')
        first_date = purchases.first().date.strftime("%b %d")
        last_date = purchases.last().date.strftime("%b %d")
    else:
        purchases = Purchase.objects.order_by('date')
        first_date = purchases.first().date.strftime("%b %d")
        last_date = purchases.last().date.strftime("%b %d")
    cashiers = Cashier.objects.all()
    last_month_purchases = Purchase.objects.filter(date__month=purchases.last().date.month).order_by('date')
    dates = []
    data = []
    incomes = {
        'month': [],
        'income': []
    }
    totalIncome = getTotalIncome(purchases)
    unique_list = []
    for x in purchases:
        if x.date.month not in unique_list:
            unique_list.append(x.date.month)

    for m in unique_list:
        incomes['month'].append(m)
        for p in purchases:
            if unique_list.__contains__(p.date.month) and p.date.month == m:
                date_string = p.date.strftime("%m")
                try:
                    ind = dates.index(date_string)
                    data[ind] = data[ind] + p.total_sum
                    incomes['income'][ind] = (data[ind])
                except ValueError:
                    dates.append(date_string)
                    data.append(p.total_sum)
                    incomes['income'].append(p.total_sum)

    monthPrediction = []
    incomesMonth = incomes['income'].copy()
    preIncomesMonth = incomes['income'].copy()
    periodFrom = unique_list[-1] + 1
    periodTo = periodFrom + 1
    print(preIncomesMonth)
    print(periodTo)
    print(periodFrom)
    if request.GET.get('period') != None:
        periodTo = int(request.GET.get('period')) + periodFrom

    for i in range(periodFrom, periodTo):
        if i > 12:
            i = i - 12
        df = pd.DataFrame(incomes)
        X = df[['month']]
        Y = df['income']
        X = df.iloc[:, 0].values.reshape(-1, 1)  # values converts it into a numpy array
        Y = df.iloc[:, 1].values.reshape(-1, 1)
        clf = LinearRegression()
        clf.fit(X, Y)
        result = clf.predict([[i]])
        print(result)
        monthPrediction.append(int((result[0])[0]))
        preIncomesMonth.append(int((result[0])[0]))
        incomes['month'].append(i)
        incomes['income'].append(int((result[0])[0]))
    current_user = request.user
    monthsString = []
    for m in incomes['month']:
        monthsString.append(get_month(m))
    filterForm = GraphFilterForm2()
    cashiersNames = getCashiers()
    salesByCashiers = getPurchasesByCashiers()
    print(incomes['income'])
    print(incomes['month'])
    return render(request, 'product/dashboard.html',
                  {'title': 'qwerty', 'data': data, 'dates': dates, 'user': current_user, 'filterForm': filterForm,
                   'months': monthsString
                      , 'monthPrediction': monthPrediction, 'result': (int((result[0])[0])),
                   'incomesMonth': incomesMonth,
                   'preIncomesMonth': preIncomesMonth,
                   'last_month_purchases': last_month_purchases,
                   'last_month_name': last_month_purchases.last().date.strftime("%B"),
                   'totalIncome': totalIncome,
                   'purchases': purchases,
                   'first_date': first_date,
                   'last_date': last_date,
                   'cashiers': cashiers,
                   'cashiersNames': cashiersNames,
                   'salesByCashiers': salesByCashiers
                   })


def dashboard3(request):
    if request.GET.get('dateFrom') != None and request.GET.get('dateTo') != None:
        first_date = request.GET.get('dateFrom')
        last_date = request.GET.get('dateTo')
        purchases = Purchase.objects.filter(date__range=(first_date, last_date)).order_by('date')
        first_date = purchases.first().date.strftime("%b %d")
        last_date = purchases.last().date.strftime("%b %d")
    else:
        purchases = Purchase.objects.order_by('date')
        first_date = purchases.first().date.strftime("%b %d")
        last_date = purchases.last().date.strftime("%b %d")
    cashiers = Cashier.objects.all()
    last_month_purchases = Purchase.objects.filter(date__month=purchases.last().date.month).order_by('date')
    dates = []
    data = []
    incomes = {
        'month': [],
        'income': [],
        'quality': [],
        'count': []
    }
    totalIncome = getTotalIncome(purchases)
    unique_list = []
    for x in purchases:
        if x.date.month not in unique_list:
            unique_list.append(x.date.month)

    for m in unique_list:
        incomes['month'].append(m)
        purchases_count = 0
        quality = 0
        for p in purchases:
            if unique_list.__contains__(p.date.month) and p.date.month == m:
                purchases_count += 1
                date_string = p.date.strftime("%m")
                try:
                    ind = dates.index(date_string)
                    data[ind] = data[ind] + p.total_sum
                    incomes['income'][ind] = (data[ind])
                    quality += int(p.product_size.product.quality)
                except ValueError:
                    quality += int(p.product_size.product.quality)
                    dates.append(date_string)
                    data.append(p.total_sum)
                    incomes['income'].append(p.total_sum)
        incomes['quality'].append(quality/purchases_count)
        incomes['count'].append(purchases_count)

    monthPrediction = []
    incomesMonth = incomes['income'].copy()
    preIncomesMonth = incomes['income'].copy()

    periodFrom = unique_list[-1] + 1
    periodTo = periodFrom + 1
    print(preIncomesMonth)
    print(periodTo)
    print(periodFrom)
    if request.GET.get('period') != None:
        periodTo = int(request.GET.get('period')) + periodFrom

    for i in range(periodFrom, periodTo):
        if i > 12:
            i = i - 12
        df = pd.DataFrame(incomes)
        X = df[['month', 'count', 'quality']]
        Y = df['income']

        clf = LinearRegression()
        clf.fit(X, Y)
        result = clf.predict([[i, request.GET.get('count'), request.GET.get('quality')]])[0]
        print(result)
        print("wefwef")
        monthPrediction.append(int(result))
        preIncomesMonth.append(int(result))
        incomes['month'].append(i)
        incomes['income'].append(int(result))
        incomes['count'].append(4)
        incomes['quality'].append(9)
    current_user = request.user
    monthsString = []
    for m in incomes['month']:
        monthsString.append(get_month(m))
    filterForm = GraphFilterForm3()
    cashiersNames = getCashiers()
    salesByCashiers = getPurchasesByCashiers()
    print(incomes)
    return render(request, 'product/dashboard.html',
                  {'title': 'qwerty', 'data': data, 'dates': dates, 'user': current_user, 'filterForm': filterForm,
                   'months': monthsString
                      , 'monthPrediction': monthPrediction, 'result': (int(result)),
                   'incomesMonth': incomesMonth,
                   'preIncomesMonth': preIncomesMonth,
                   'last_month_purchases': last_month_purchases,
                   'last_month_name': last_month_purchases.last().date.strftime("%B"),
                   'totalIncome': totalIncome,
                   'purchases': purchases,
                   'first_date': first_date,
                   'last_date': last_date,
                   'cashiers': cashiers,
                   'cashiersNames': cashiersNames,
                   'salesByCashiers': salesByCashiers
                   })


def getTotalIncome(purchases):
    total = 0
    for p in purchases:
        total += p.product_size.product.price_after_markup * p.product_size.count
    return total


def getPurchasesByCashiers():
    purchases = Purchase.objects.all()
    cashiers = Cashier.objects.all()
    sales = []
    for c in cashiers:
        count = 0
        for p in purchases:
            if p.cashier_id == c.id:
                count += 1
        sales.append(count)
    return sales


def getCashiers():
    cashiers = Cashier.objects.all()
    cas = []
    for c in cashiers:
        cas.append(c.cashier.username)
    return cas


def dashboard2(request):
    if request.GET.get('dateFrom') != None and request.GET.get('dateTo') != None:
        first_date = request.GET.get('dateFrom')
        last_date = request.GET.get('dateTo')
        purchases = Purchase.objects.filter(date__range=(first_date, last_date)).order_by('date')
    else:
        purchases = Purchase.objects.order_by('date')
    dates = []
    data = []
    print(purchases)
    for p in purchases:
        date_string = p.date.strftime("%d.%m.%y")
        try:
            ind = dates.index(date_string)
            data[ind] = data[ind] + p.product_size.product.price_after_markup * p.discount
        except ValueError:
            dates.append(date_string)
            data.append(p.product_size.product.price_after_markup * p.discount)

    current_user = request.user
    filterForm = GraphFilterForm()
    return render(request, 'product/dashboard.html',
                  {'title': 'qwerty', 'data': data, 'dates': dates, 'user': current_user, 'filterForm': filterForm})


def get_month(month):
    if month == 1:
        return 'January'
    if month == 2:
        return 'February'
    if month == 3:
        return 'March'
    if month == 4:
        return 'April'
    if month == 5:
        return 'May'
    if month == 6:
        return 'June'
    if month == 7:
        return 'Jule'
    if month == 8:
        return 'August'
    if month == 9:
        return 'September'
    if month == 10:
        return 'October'
    if month == 11:
        return 'November'
    if month == 12:
        return 'December'
    raise ValueError('Undefined unit: {}'.format(month))


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
        context['qs'] = Purchase.objects.values(item=F('cashier__username')).annotate(
            income=Sum('net_income')).order_by('item')
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
        res = [{'item': 'утро', 'income': str(morning)}, {'item': 'обед', 'income': str(noon)},
               {'item': 'вечер', 'income': str(evening)}]
        context['qs'] = res
        return context


class SizePurchaseChartView(TemplateView):
    template_name = 'product/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('product_size__size')).annotate(income=Count('id')).order_by(
            'item')
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
    m = (((np.mean(x) * np.mean(y)) - np.mean(x * y)) / ((np.mean(x) * np.mean(x)) - np.mean(x * x)))
    m = round(m, 2)
    b = np.mean(y) - np.mean(x) * m
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
