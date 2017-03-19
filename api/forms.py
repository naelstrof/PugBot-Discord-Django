#log/forms.py
from django.contrib.auth.forms import AuthenticationForm 
from django import forms
from multiupload.fields import MultiFileField
from captcha.fields import CaptchaField
from .models import *
from django.utils.safestring import mark_safe
# If you don't do this you cannot use Bootstrap CSS


Position_Choices = [
    ('Defender', 'Defender'),
    ('Mid', 'Mid'),
    ('Offense', 'Offense'),
]

Day_Choices = [
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
]

Time_Choices = [
    ('Evenings', 'Evenings'),
    ('Afternoons', 'Afternoons'),
    ('Mornings', 'Mornings'),
]

Region_Choices = [

    ('North America', 'North America'),
    ('Europe', 'Europe'),
    ('South America', 'South America'),
    ('Central America', 'Central America'),
]


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=30, 
                               widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'username'}))
    password = forms.CharField(label="Password", max_length=30, 
                               widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'password'}))

class UploadForm(forms.Form):
    attachments = MultiFileField(min_num=1, max_num=10)


class SignupForm(forms.ModelForm):
    display_name = forms.CharField(label="Display Name", max_length="24", widget=forms.TextInput(attrs={'class': 'w3-input', 'name': 'UT_Display_Name', 'placeholder': 'Epic Account Name'}))    
    epicID = forms.CharField(label="EpicID", max_length="32", widget=forms.TextInput(attrs={'class': 'w3-input', 'name': 'EpicID', 'placeholder': 'Find EpicID by clicking on your player Card'}))   
    email = forms.EmailField(max_length="70", widget=forms.TextInput(attrs={'class': 'w3-input', 'name': 'email', 'placeholder': 'Valid email address'}))
    position = forms.ChoiceField(choices=Position_Choices,widget=forms.RadioSelect)
    region = forms.ChoiceField(choices=Region_Choices, widget=forms.RadioSelect)
    day_most_available = forms.ChoiceField(choices=Day_Choices)
    time_most_available = forms.ChoiceField(choices=Time_Choices)
    Availability_Explained = forms.CharField(max_length=40, widget=forms.TextInput(attrs={'class': 'w3-input', 'name': 'Availability_Explained', 'placeholder': 'Any notes or ALTERNATE availability'}))
    captcha = CaptchaField()
    class Meta:
        model = SignUp       
        fields = ('display_name', 'epicID', 'email', 'position', 'region', 'day_most_available', 'time_most_available', 'Availability_Explained')
