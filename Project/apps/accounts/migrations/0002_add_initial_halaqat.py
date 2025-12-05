# -*- coding: utf-8 -*-
from django.db import migrations

def create_initial_halaqat(apps, schema_editor):
    """
    هذه الدالة ستقوم بإنشاء حلقات مع تحديد نطاق الأجزاء لكل حلقة.
    """
    Halaqa = apps.get_model("accounts", "Halaqa") # <-- تأكد من اسم التطبيق هنا
    
    # قائمة بأسماء الحلقات ونطاق الأجزاء لكل منها
    halaqat_data = [
        {"name": "حلقة أبي بكر الصديق", "juz_from": 1, "juz_to": 3},
        {"name": "حلقة عمر بن الخطاب", "juz_from": 4, "juz_to": 6},
        {"name": "حلقة عثمان بن عفان", "juz_from": 7, "juz_to": 9},
        {"name": "حلقة علي بن أبي طالب", "juz_from": 10, "juz_to": 12},
        {"name": "حلقة خديجة بنت خويلد", "juz_from": 13, "juz_to": 15},
        {"name": "حلقة عائشة أم المؤمنين", "juz_from": 16, "juz_to": 18},
        {"name": "حلقة فاطمة الزهراء", "juz_from": 19, "juz_to": 21},
        {"name": "حلقة خالد بن الوليد", "juz_from": 22, "juz_to": 24},
        {"name": "حلقة سعد بن أبي وقاص", "juz_from": 25, "juz_to": 27},
        {"name": "حلقة عبد الرحمن بن عوف", "juz_from": 28, "juz_to": 30},
    ]

    halaqat_to_create = []
    for data in halaqat_data:
        halaqat_to_create.append(
            Halaqa(
                name=data["name"],
                juz_from=data["juz_from"],
                juz_to=data["juz_to"]
            )
        )
    
    Halaqa.objects.bulk_create(halaqat_to_create)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_halaqat),
    ]