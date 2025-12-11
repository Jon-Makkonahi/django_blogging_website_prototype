from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import Profile


class UserUpdateForm(forms.ModelForm):
    """
    Форма обновления данных пользователя
    """
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control mb-1"})
    )
    email = forms.EmailField(
        widget=forms.TextInput(attrs={"class": "form-control mb-1"})
    )
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control mb-1"})
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control mb-1"})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_email(self):
        """
        Проверка email на уникальность
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Email адрес должен быть уникальным')
        return email


class ProfileUpdateForm(forms.ModelForm):
    """
    Форма обновления данных профиля пользователя
    """
    birth_date = forms.DateField(
        widget=forms.TextInput(attrs={"class": "form-control mb-1"})
    )
    bio = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={'rows': 5, "class": "form-control mb-1"})
    )
    avatar = forms.ImageField(widget=forms.FileInput(attrs={"class": "form-control mb-1"}))

    class Meta:
        model = Profile
        fields = ('birth_date', 'bio', 'avatar')


class UserRegisterForm(UserCreationForm):
    """
    Переопределенная форма регистрации пользователей
    """

    class Meta(UserCreationForm.Meta):
        fields = (
            'username', 'password1', 'password2',
            'email', 'first_name', 'last_name'
        )

    def clean_email(self):
        """
        Проверка email на уникальность
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'Такой email уже используется в системе'
            )
        return email

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы регистрации
        """
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {"placeholder": "Придумайте свой логин"}
        )
        self.fields['password1'].widget.attrs.update(
            {"placeholder": "Придумайте свой пароль"}
        )
        self.fields['password2'].widget.attrs.update(
            {"placeholder": "Повторите придуманный пароль"}
        )
        self.fields['email'].widget.attrs.update(
            {"placeholder": "Введите свой email"}
        )
        self.fields['first_name'].widget.attrs.update(
            {"placeholder": "Ваше имя"}
        )
        self.fields['last_name'].widget.attrs.update(
            {"placeholder": "Ваша фамилия"}
        )
        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {"class": "form-control", "autocomplete": "off"}
            )


class UserLoginForm(AuthenticationForm):
    """
    Форма авторизации на сайте
    """

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы авторизации
        """
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Логин пользователя'
        self.fields['password'].widget.attrs['placeholder'] = 'Пароль пользователя'
        self.fields['username'].label = 'Логин'
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })
