from django import template

register = template.Library()

DAY_MAP = {
    "Saturday": "السبت",
    "Sunday": "الأحد",
    "Monday": "الإثنين",
    "Tuesday": "الثلاثاء",
    "Wednesday": "الأربعاء",
    "Thursday": "الخميس",
    "Friday": "الجمعة",
}

@register.filter
def arabic_day(value):
    try:
        day_name = value.strftime("%A")  # full English day name
        return DAY_MAP.get(day_name, day_name)
    except Exception:
        return value


# في ملف: apps/accounts/templatetags/custom_tags.py


# ... (الفلتر القديم arabic_day يبقى كما هو) ...

@register.filter
def sub(value, arg):
    """فلتر يقوم بطرح قيمة من أخرى"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value