from django.forms import ModelForm
from django import forms
from .models import settings


#Forms class to get choices from generate report 

Sensors= [
    ('Temperature', 'Temperature'),
    ('Soil Moisture', 'Soil Moisture'),
    ('Humidity', 'Humidity'),
    ('pH', 'pH'),
 ]

class CHOICES(forms.Form):
    Sensors = forms.CharField(widget=forms.RadioSelect(choices=Sensors))
