from django import forms


class EmailSendForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea, max_length=400)
    email = forms.EmailField(max_length=100)
