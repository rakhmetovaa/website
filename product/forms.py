from django import forms
from django.forms import DateInput, TextInput, NumberInput


class EmailSendForm(forms.Form):
    subject = forms.CharField(max_length=100, widget=TextInput(attrs={'class': 'form-control mb-3'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control mb-3'}), max_length=400)
    email = forms.EmailField(max_length=100, widget=TextInput(attrs={'class': 'form-control mb-3'}))


class GraphFilterForm(forms.Form):
    dateFrom = forms.DateField(widget=DateInput(attrs={'class': 'form-control mb-3', 'type': 'date'}))
    dateTo = forms.DateField(widget=DateInput(attrs={'class': 'form-control mb-3', 'type': 'date'}))


class GraphFilterForm2(forms.Form):
    dateFrom = forms.DateField(label="Date From",
                               widget=DateInput(attrs={'class': 'form-control mb-3', 'type': 'date'}))
    dateTo = forms.DateField(label="Date To", widget=DateInput(attrs={'class': 'form-control mb-3', 'type': 'date'}))
    period = forms.ChoiceField(label="Period", choices=(
        (1, "month"), (3, "3 month"), (5, "5 month"), (7, "7 month"), (9, "9 month"), (12, "12 month")),
                               widget=forms.Select(attrs={'class': 'form-control mb-3'}))


class GraphFilterForm3(forms.Form):
    dateFrom = forms.DateField(label="Date From",
                               widget=DateInput(attrs={'class': 'form-control mb-3', 'type': 'date'}))
    dateTo = forms.DateField(label="Date To", widget=DateInput(attrs={'class': 'form-control mb-3', 'type': 'date'}))
    period = forms.ChoiceField(label="Period", choices=(
        (1, "month"), (3, "3 month"), (5, "5 month"), (7, "7 month"), (9, "9 month"), (12, "12 month")),
                               widget=forms.Select(attrs={'class': 'form-control mb-3'}))
    quality = forms.IntegerField(widget=NumberInput(attrs={'class': 'form-control mb-3'}))
    count = forms.IntegerField(widget=NumberInput(attrs={'class': 'form-control mb-3'}))
