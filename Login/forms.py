from django import forms

class LoginForm(forms.Form):
    email = forms.CharField(label='Email',  max_length=100, required=True, widget=forms.EmailInput(attrs={'id': 'EmailEntry'}))
    password = forms.CharField(label='Password', max_length=32, required=True, widget=forms.PasswordInput(attrs={'id': 'PasswordEntry'}))

class ForgotPasswordForm(forms.Form):
    email = forms.CharField(label='Email',  max_length=100, required=True, widget=forms.EmailInput(attrs={'id': 'EmailEntry'}))