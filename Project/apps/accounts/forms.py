from django import forms
from django.contrib.auth.models import User
from .models import Halaqa, Profile
from django.contrib.auth.forms import PasswordChangeForm


class RegisterForm(forms.Form):
    ROLE_CHOICES = (
        (Profile.ROLE_STUDENT, "طالب"),
        (Profile.ROLE_TEACHER, "معلّم"),
    )

    username = forms.CharField(max_length=150, label="اسم المستخدم")
    password1 = forms.CharField(widget=forms.PasswordInput, label="كلمة المرور")
    password2 = forms.CharField(widget=forms.PasswordInput, label="تأكيد كلمة المرور")
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="الدور")
    halaqa = forms.ModelChoiceField(
        queryset=Halaqa.objects.all(),
        required=False,
        label="الحلقة (للطلاب)",
    )

    def clean_username(self):
        u = self.cleaned_data["username"]
        if User.objects.filter(username=u).exists():
            raise forms.ValidationError("اسم المستخدم موجود بالفعل.")
        return u

    def clean(self):
        data = super().clean()
        if data.get("password1") != data.get("password2"):
            self.add_error("password2", "كلمتا المرور غير متطابقتين.")
        if data.get("role") == Profile.ROLE_STUDENT and not data.get("halaqa"):
            self.add_error("halaqa", "اختيار الحلقة مطلوب للطالب.")
        return data




class ProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=100, required=True, label="الاسم")
    email = forms.EmailField(required=True, label="البريد الإلكتروني")
    avatar = forms.ImageField(required=False, label="الصورة الشخصية")

    class Meta:
        model = Profile
        fields = ['avatar']

class CustomPasswordChangeForm(PasswordChangeForm):
    # هنا نقوم بتخصيص تصميم حقول تغيير كلمة المرور لتناسب Tailwind CSS
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'w-full p-3 bg-background dark:bg-background-dark border border-border-color dark:border-border-color-dark rounded-lg', 'placeholder': 'كلمة المرور الحالية'})
        self.fields['new_password1'].widget.attrs.update({'class': 'w-full p-3 bg-background dark:bg-background-dark border border-border-color dark:border-border-color-dark rounded-lg', 'placeholder': 'كلمة المرور الجديدة'})
        self.fields['new_password2'].widget.attrs.update({'class': 'w-full p-3 bg-background dark:bg-background-dark border border-border-color dark:border-border-color-dark rounded-lg', 'placeholder': 'تأكيد كلمة المرور الجديدة'})