import numpy as np
from django.views.generic import TemplateView
from .forms import EmailSendForm, GraphFilterForm2, GraphFilterForm3, GraphFilterForm
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
from django.conf import settings
from django.core.files.storage import FileSystemStorage


def data_migrate(request):
    data = pd.read_excel(request.FILES.get('excel_data'))
    df = pd.DataFrame(data)
    print(df)
    for dbframe in df.itertuples():
        type = ProductType.objects.filter(name=dbframe[1])[0]
        print(type)
        season = Season.objects.filter(name=dbframe[5])[0]
        print(season)
        obj = Product.objects.create(type=type,
                                     name=dbframe[2],
                                     brand=dbframe[3],
                                     code=dbframe[4],
                                     season=season,
                                     initial_price=dbframe[6],
                                     markup=dbframe[7],
                                     quality=dbframe[9]
                                     )
        print(obj)
        obj.save()
    print(df)
    return redirect("import-excel")


def import_excel(request):
    return render(request, 'product/import_excel.html')


def clients(request):
    return render(request, 'product/clients.html', {'segment': 'clients'})


def dashboard(request):
    if request.GET.get('count') == None and request.GET.get('quality') == None:
        graph_count = 4
        graph_quality = 9
    else:
        graph_count = int(request.GET.get('count'))
        graph_quality = int(request.GET.get('quality'))
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
        incomes['quality'].append(quality / purchases_count)
        incomes['count'].append(purchases_count)

    monthPrediction = []
    incomesMonth = incomes['income'].copy()
    preIncomesMonth = incomes['income'].copy()

    periodFrom = unique_list[-1] + 1
    periodTo = periodFrom + 1
    print(preIncomesMonth)

    print(periodFrom)
    if request.GET.get('period') != None:
        periodTo = int(request.GET.get('period')) + periodFrom
    print(periodTo)
    for i in range(periodFrom, periodTo):
        df = pd.DataFrame(incomes)
        X = df[['month', 'count', 'quality']]
        Y = df['income']

        clf = LinearRegression()
        clf.fit(X, Y)
        print(i)
        print(graph_count)
        print(graph_quality)
        result = clf.predict([[i, graph_count, graph_quality]])[0]
        print(result)
        monthPrediction.append(int(result))
        print(monthPrediction)
        preIncomesMonth.append(int(result))
        print(preIncomesMonth)
        incomes['month'].append(i)
        incomes['income'].append(int(result))
        incomes['count'].append(int(graph_count))
        incomes['quality'].append(int(graph_quality))
    current_user = request.user
    monthsString = []
    for m in incomes['month']:
        if m > 12:
            m = m - 12
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
                   'salesByCashiers': salesByCashiers,
                   'segment': 'dashboard'
                   })


def getTotalIncome(purchases):
    total = 0
    for p in purchases:
        total += p.product_size.product.price_after_markup * p.count
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
    template_name = 'product/graph.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('product_size__product__name')).annotate(
            income=Sum('net_income')).order_by('item')
        context['title'] = 'Продукты'
        context['segment'] = 'purchase'
        print(context['qs'])
        max_income = 0
        max_item_text = "["
        for p in context['qs']:
            if p['income'] == max_income:
                max_item_text += f", {p['item']} - {p['income']}"
                max_income = p['income']
            elif p['income'] > max_income:
                max_item_text = f"[{p['item']} - {p['income']}"
                max_income = p['income']
        max_item_text += "]"

        min_item_text = "["
        min_income = 999999999999
        for p in context['qs']:
            if p['income'] == min_income:
                min_item_text += f", {p['item']} - {p['income']}"
                min_income = p['income']
            elif p['income'] < min_income:
                min_item_text = f"[{p['item']} - {p['income']}"
                min_income = p['income']
        min_item_text += "]"
        context['graph_text'] = "Данный график показывает, какой товар наиболее востребован среди покупателей. Это " \
                                "дает возможность пользователю сузить свою нишу. И уделять внимание определенным " \
                                "категориям товара на который всегда есть спрос и  уделить внимание определенным " \
                                "категориям, на которые всегда есть спрос среди потребителей. Самый продаваемый товар " \
                                f"за это время это – {max_item_text},мин значение у товара {min_item_text}. Если товар остается в " \
                                "остатках и не имеет спроса среди потребилей, то следует обратиться в маркетинговый " \
                                "отдел и продумать стратегию для продаж этих товаров. Самое элементарное, " \
                                "что можно сделать это поставить товар на скидки, придумать акции, задействовать " \
                                "" \
                                ".рекламу через соц сети. "

        return context


class CashierPurchaseChartView(TemplateView):
    template_name = 'product/graph.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('cashier__username')).annotate(
            income=Sum('net_income')).order_by('item')
        context['title'] = 'Кассиры'
        context['segment'] = 'cashier'
        max_income = 0
        max_item_text = "["
        for p in context['qs']:
            if p['income'] == max_income:
                max_item_text += ", " + p['item'] + " - " + p['income'].__str__()
                max_income = p['income']
            elif p['income'] > max_income:
                max_item_text = "[" + p['item'] + " - " + p['income'].__str__()
                max_income = p['income']
        max_item_text += "]"
        context['graph_text'] = "Работа сотрудников очень важный аспект в ведении подобного бизнеса. С " \
                                "помощью этого графика можно сделать отбор команды. Сотрудник, показывающий " \
                                "наилучшие результаты является наиболее активным, трудолюбивым и " \
                                "ответственным. Во избежание набора 'серого кардинала' был создан этот " \
                                "анализ. Больше продает кассир " + max_item_text + ", можно прибавить 15% бонуса," \
                                                                                   "чтобы он дальше еще " \
                                                                                   "больше старался. "

        return context


class HourPurchaseChartView(TemplateView):
    template_name = 'product/graph.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Время'
        morning = int(
            Purchase.objects.filter(
                date__hour__lt=12,
                date__hour__gte=0
            ).aggregate(
                total=Sum('total_sum')
            ).get('total')
            or 0
        )
        noon = int(
            Purchase.objects.filter(
                date__hour__lt=18,
                date__hour__gte=12
            ).aggregate(
                total=Sum('total_sum')
            ).get('total')
            or 0
        )
        evening = int(
            Purchase.objects.filter(
                date__hour__lt=24,
                date__hour__gte=18
            ).aggregate(
                total=Sum('total_sum')
            ).get('total')
            or 0
        )
        max_purchases = {}
        min_purchases = {}
        max_val = max(morning, noon, evening)
        min_val = min(morning, noon, evening)
        if max_val == morning:
            max_purchases = {max_val: 'Утром'}
        elif max_val == noon:
            max_purchases = {max_val: 'В обед'}
        else:
            max_purchases = {max_val: 'Вечером'}

        if min_val == morning:
            min_purchases = {min_val: 'Утром'}
        elif min_val == noon:
            min_purchases = {min_val: 'В обед'}
        else:
            min_purchases = {min_val: 'Вечером'}

        res = [{'item': 'утро', 'income': str(morning)}, {'item': 'обед', 'income': str(noon)},
               {'item': 'вечер', 'income': str(evening)}]
        context['qs'] = res
        context['max_hour_text'] = max_purchases.get(
            max_val) + " (" + max_val.__str__() + ") больше дохода,получается нужно подготовить в это время новинки, сделать до этого времени  мини уборку магазина,красиво рассортировать товары по местам и подготовится к большому притоку клиентов."
        context['min_hour_text'] = min_purchases.get(
            min_val) + " (" + min_val.__str__() + ") меньше дохода, тогда можно устроить часы скидок определенных товаров, продавать купоны со скидкой,чтобы потом покупатели купили на эти купоны товары магазина"
        context['segment'] = 'hour'
        return context


def get_time_text(month):
    if month == 1:
        return 'January'
    if month == 2:
        return 'February'
    if month == 3:
        return 'March'

    raise ValueError('Undefined unit: {}'.format(month))


class SizePurchaseChartView(TemplateView):
    template_name = 'product/graph.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('product_size__size')).annotate(income=Count('id')).order_by(
            'item')
        context['title'] = 'Размеры'
        context['segment'] = 'size'
        print(context['qs'])
        max_income = 0
        max_item_text = "["
        for p in context['qs']:
            if p['income'] == max_income:
                max_item_text += f", размер({p['item']}) - {p['income']}"
                max_income = p['income']
            elif p['income'] > max_income:
                max_item_text = f"[размер({p['item']}) - {p['income']}"
                max_income = p['income']
        max_item_text += "]"
        context['graph_text'] = "Данный график показывает самые ходовые размеры. Это дает возможность понять " \
                                "пользователю, какие размеры нужно заказывать дополнительно. Востребованный размер " \
                                "среди покупателей " + max_item_text + " размер, следовательно нужно завозить товар в " \
                                                                       "этом размере в " \
                                                                       "больших количествах. "

        return context


class DiscountPurchaseChartView(TemplateView):
    template_name = 'product/graph.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['qs'] = Purchase.objects.values(item=F('discount_type')).annotate(income=Count('id')).order_by('item')
        context['title'] = 'Скидки'
        context['segment'] = 'discount'
        max_income = 0
        max_item_text = "["
        for p in context['qs']:
            if p['income'] == max_income:
                max_item_text += ", " + p['item'] + " - " + p['income'].__str__()
                max_income = p['income']
            elif p['income'] > max_income:
                max_item_text = "[" + p['item'] + " - " + p['income'].__str__()
                max_income = p['income']
        max_item_text += "]"
        context['graph_text'] = "Этот график показывает проходимость товаров со скидкой или без. В торговле " \
                                "бывают так называемые 'мертвые сезоны', когда товар без скидки не востребован. " \
                                "Для прогнозирования начала таких сезонов был создан этот анализ.Больше " \
                                "продается колонка " + max_item_text + ", поэтому нужно уделить " \
                                                                       "внимание  на другую колонку. "

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
        return render(request, "product/net_income_2.html", {})
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

    max_income = 0
    ind = 0
    net_income_labels.sort()
    for i in net_income_labels:
        ind += 1
        if i > max_income:
            max_income = i
    max_income_date = labels[ind-1]
    print(net_income_labels.__len__())
    print(labels.__len__())
    print(max_income_date)
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

    context['graph_text'] = f"Данная вкладка позволяет посчитать чистую прибыль с учетом всех дополнительных затрат, " \
                            "при этом у вас есть возможность выбрать временной промежуток, что очень удобно для " \
                            f"совершения анализа. [Max income] показан в [" \
                            f"{max_income_date}] день в размере [{net_income_labels[net_income_labels.__len__() - 1]}]тг.Прогнозирование " \
                            "прибыли зависит от нескольких факторов, указанных выше таблицы. При изменении одного из " \
                            "которых можно наблюдать изменение траектории линии в графике. При анализе, " \
                            "у пользователя есть возможность понять, как каждый фактор влияет на всю картину. "
    context['segment'] = 'net-income'
    return render(request, "product/net_income_2.html", context)
