from django import forms

from .models import User

class LoginForm(forms.Form):
    username = forms.CharField(label='Username or Email', max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

class SignupForm(forms.Form):
    username = forms.CharField(label='Full Name', max_length=100)
    email = forms.EmailField(label='Email')
    phone_number = forms.CharField(label='Phone Number', max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")
            
        email = cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', "Email already exists")
        return cleaned_data