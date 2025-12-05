from django import template
from django.utils import timezone
import datetime

register = template.Library()

@register.filter(name='arabic_timesince')
def arabic_timesince(value):
    """
    فلتر مخصص لعرض الفارق الزمني باللغة العربية بشكل دقيق.
    يعالج التواريخ الماضية والمستقبلية.
    """
    if not value or not isinstance(value, (datetime.datetime, datetime.date)):
        return "غير محدد"

    now = timezone.now()
    
    # تحويل كائن date إلى datetime لضمان دقة المقارنة
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        value = timezone.make_aware(datetime.datetime.combine(value, datetime.time.min))

    is_future = value > now
    
    if is_future:
        diff = value - now
        prefix = "بعد"
    else:
        diff = now - value
        prefix = "منذ"

    seconds = diff.total_seconds()
    minutes = int(seconds / 60)
    hours = int(minutes / 60)
    days = int(hours / 24)
    weeks = int(days / 7)
    months = int(days / 30)
    years = int(days / 365)

    if seconds < 10:
        return "الآن"
    elif minutes < 60:
        if minutes == 1: return f"{prefix} دقيقة"
        if minutes == 2: return f"{prefix} دقيقتين"
        if 3 <= minutes <= 10: return f"{prefix} {minutes} دقائق"
        return f"{prefix} {minutes} دقيقة"
    elif hours < 24:
        if hours == 1: return f"{prefix} ساعة"
        if hours == 2: return f"{prefix} ساعتين"
        if 3 <= hours <= 10: return f"{prefix} {hours} ساعات"
        return f"{prefix} {hours} ساعة"
    elif days < 7:
        if not is_future:
            if days == 1: return "أمس"
            if days == 2: return "منذ يومين"
        else:
            if days == 1: return "غدًا"
            if days == 2: return "بعد يومين"
            
        if 3 <= days <= 10: return f"{prefix} {days} أيام"
        return f"{prefix} {days} يوم"
    elif weeks < 4:
        if weeks == 1: return f"{prefix} أسبوع"
        if weeks == 2: return f"{prefix} أسبوعين"
        if 3 <= weeks <= 10: return f"{prefix} {weeks} أسابيع"
        return f"{prefix} {weeks} أسبوع"
    elif months < 12:
        if months == 1: return f"{prefix} شهر"
        if months == 2: return f"{prefix} شهرين"
        if 3 <= months <= 10: return f"{prefix} {months} أشهر"
        return f"{prefix} {months} شهر"
    else:
        if years == 1: return f"{prefix} سنة"
        if years == 2: return f"{prefix} سنتين"
        if 3 <= years <= 10: return f"{prefix} {years} سنوات"
        return f"{prefix} {years} سنة"