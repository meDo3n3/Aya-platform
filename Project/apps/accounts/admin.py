from django.contrib import admin
from django import forms
from django.urls import path
from django.http import JsonResponse

from .models import (
    Profile, Halaqa,
    Recitation, RecitationSubmission,
    Review, ReviewSubmission,
    Surah,
)

# ========== Helpers ==========
def _range_title(obj):
    surah = getattr(obj, "surah", None)
    s = getattr(obj, "start_ayah", None)
    e = getattr(obj, "end_ayah", None)
    if surah and s and e:
        return f"سورة {surah} من آية {s} إلى آية {e}"
    # تم تعديل السطر التالي ليعمل بشكل أفضل بعد حذف range_text
    elif surah:
        return f"سورة {surah}"
    return getattr(obj, "range_text", None) or "-"


class BaseRangeForm(forms.ModelForm):
    def clean(self):
        cleaned = super().clean()
        s = cleaned.get("start_ayah")
        e = cleaned.get("end_ayah")
        if s and e and s > e:
            raise forms.ValidationError("رقم آية البداية يجب أن يكون أقل من أو يساوي رقم آية النهاية.")
        return cleaned


# ========== Profile ==========
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ("user", "role", "halaqa_name", "teacher_status_display")
    list_filter   = ("role", "teacher_status", "halaqa")
    search_fields = ("user__username", "user__first_name", "user__last_name")

    # --- بداية التعديلات ---

    def get_fieldsets(self, request, obj=None):
        """
        هذه الدالة هي مفتاح الحل.
        تقوم بتغيير مجموعات الحقول المعروضة بناءً على دور المستخدم.
        """
        # الحقول الأساسية المشتركة دائمًا
        base_fields = ('user', 'role', 'photo')

        if obj and obj.role == Profile.ROLE_TEACHER:
            # إذا كان الدور "معلم"، اعرض هذه الحقول
            return (
                ('المعلومات الأساسية', {'fields': base_fields}),
                ('بيانات المعلم', {'fields': ('institution', 'bio', 'certificate', 'teacher_status')}),
            )
        
        # في أي حالة أخرى (بما في ذلك عند إنشاء بروفايل جديد أو لو كان الدور "طالب")
        # اعرض حقول الطالب
        return (
            ('المعلومات الأساسية', {'fields': base_fields}),
            ('بيانات الطالب', {'fields': ('halaqa', 'gender', 'birth_date', 'guardian_phone')}),
        )

    # --- نهاية التعديلات ---

    def halaqa_name(self, obj):
        return obj.halaqa.name if obj.halaqa else "-"
    halaqa_name.short_description = "الحلقة"

    def teacher_status_display(self, obj):
        # The correction is on this line: ROLE_TEACHER instead of ROLE_TECH
        return obj.teacher_status.title() if obj.role == Profile.ROLE_TEACHER else "-"
    teacher_status_display.short_description = "حالة المعلم"


# ========== Halaqa ==========
@admin.register(Halaqa)
class HalaqaAdmin(admin.ModelAdmin):
    list_display  = ("name",)
    search_fields = ("name",)
    filter_horizontal = ("teachers",)


# ========== Recitation ==========
class RecitationAdminForm(BaseRangeForm):
    surah = forms.ModelChoiceField(
        label="السورة",
        queryset=Surah.objects.none(),
        required=True
    )

    class Meta:
        model = Recitation
        fields = ("halaqa", "created_by", "surah", "start_ayah", "end_ayah", "deadline")
        widgets = {
            "start_ayah": forms.NumberInput(attrs={"min": 1}),
            "end_ayah": forms.NumberInput(attrs={"min": 1}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        halaqa_pk = self.initial.get("halaqa") or self.data.get("halaqa")
        if halaqa_pk:
            h = Halaqa.objects.filter(pk=halaqa_pk).first()
            if h and h.juz_from and h.juz_to:
                self.fields["surah"].queryset = Surah.objects.filter(
                    juz_from__lte=h.juz_to,
                    juz_to__gte=h.juz_from
                ).order_by("id")
            else:
                self.fields["surah"].queryset = Surah.objects.none()
        else:
            self.fields["surah"].queryset = Surah.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=False)
        s_obj = self.cleaned_data.get("surah")
        instance.surah = s_obj.name if isinstance(s_obj, Surah) else str(s_obj or "")
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(Recitation)
class RecitationAdmin(admin.ModelAdmin):
    form = RecitationAdminForm
    fields = ("halaqa", "created_by", "surah", "start_ayah", "end_ayah", "deadline")

    list_display  = ("title_display", "halaqa", "created_by", "deadline")
    list_filter   = ("halaqa",)
    search_fields = ("surah", "halaqa__name", "created_by__user__username")

    class Media:
        js = ("admin/js/recitation_chained_surah.js",)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "surah-options/",
                self.admin_site.admin_view(self.surah_options_view),
                name="recitation_surah_options"
            ),
        ]
        return custom + urls

    def surah_options_view(self, request):
        hid = request.GET.get("halaqa")
        qs = Surah.objects.none()
        if hid:
            h = Halaqa.objects.filter(pk=hid).first()
            if h and h.juz_from and h.juz_to:
                qs = Surah.objects.filter(
                    juz_from__lte=h.juz_to,
                    juz_to__gte=h.juz_from
                ).order_by("id")
        data = [{"id": s.id, "name": s.name} for s in qs]
        return JsonResponse({"ok": True, "results": data})

    def title_display(self, obj):
        return _range_title(obj)
    title_display.short_description = "المهمة"

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by", None) and hasattr(request.user, "profile"):
            obj.created_by = request.user.profile
        super().save_model(request, obj, form, change)


@admin.register(RecitationSubmission)
class RecitationSubmissionAdmin(admin.ModelAdmin):
    list_display  = ("recitation_title", "student", "status", "created_at")
    list_filter   = ("status", "recitation__halaqa")
    search_fields = ("recitation__surah", "student__user__username")

    def recitation_title(self, obj):
        return _range_title(obj.recitation)
    recitation_title.short_description = "التسميع"


# ========== Review ==========
# تم نسخ وتعديل هذا القسم بالكامل ليعمل مثل قسم التسميع

class ReviewAdminForm(BaseRangeForm):
    surah = forms.ModelChoiceField(
        label="السورة",
        queryset=Surah.objects.none(),
        required=True
    )

    class Meta:
        model = Review
        fields = ("halaqa", "created_by", "surah", "start_ayah", "end_ayah", "deadline")
        widgets = {
            "start_ayah": forms.NumberInput(attrs={"min": 1}),
            "end_ayah": forms.NumberInput(attrs={"min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        halaqa_pk = self.initial.get("halaqa") or self.data.get("halaqa")
        if halaqa_pk:
            h = Halaqa.objects.filter(pk=halaqa_pk).first()
            if h and h.juz_from and h.juz_to:
                self.fields["surah"].queryset = Surah.objects.filter(
                    juz_from__lte=h.juz_to,
                    juz_to__gte=h.juz_from
                ).order_by("id")
            else:
                self.fields["surah"].queryset = Surah.objects.none()
        else:
            self.fields["surah"].queryset = Surah.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=False)
        s_obj = self.cleaned_data.get("surah")
        instance.surah = s_obj.name if isinstance(s_obj, Surah) else str(s_obj or "")
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm
    fields = ("halaqa", "created_by", "surah", "start_ayah", "end_ayah", "deadline")

    list_display  = ("title_display", "halaqa", "created_by")
    list_filter   = ("halaqa",)
    search_fields = ("surah", "halaqa__name", "created_by__user__username")

    class Media:
        js = ("admin/js/recitation_chained_surah.js",)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "surah-options/",
                self.admin_site.admin_view(self.surah_options_view),
                name="review_surah_options"
            ),
        ]
        return custom + urls

    def surah_options_view(self, request):
        hid = request.GET.get("halaqa")
        qs = Surah.objects.none()
        if hid:
            h = Halaqa.objects.filter(pk=hid).first()
            if h and h.juz_from and h.juz_to:
                qs = Surah.objects.filter(
                    juz_from__lte=h.juz_to,
                    juz_to__gte=h.juz_from
                ).order_by("id")
        data = [{"id": s.id, "name": s.name} for s in qs]
        return JsonResponse({"ok": True, "results": data})

    def title_display(self, obj):
        return _range_title(obj)
    title_display.short_description = "المراجعة"

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by", None) and hasattr(request.user, "profile"):
            obj.created_by = request.user.profile
        super().save_model(request, obj, form, change)


@admin.register(ReviewSubmission)
class ReviewSubmissionAdmin(admin.ModelAdmin):
    list_display  = ("review_title", "student", "status", "created_at")
    list_filter   = ("status", "review__halaqa")
    search_fields = ("review__surah", "student__user__username")

    def review_title(self, obj):
        return _range_title(obj.review)
    review_title.short_description = "المراجعة"