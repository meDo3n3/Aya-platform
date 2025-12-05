from django.core.management.base import BaseCommand
from apps.accounts.models import Surah

# خرائط مجموعات كل 3 أجزاء (نفس المنطق اللي استخدمناه قبل كده)
GROUPS = {
    (1, 3):  ["الفاتحة","البقرة","آل عمران"],
    (4, 6):  ["آل عمران","النساء","المائدة","الأنعام"],
    (7, 9):  ["الأنعام","الأعراف","الأنفال","التوبة"],
    (10,12): ["التوبة","يونس","هود","يوسف"],
    (13,15): ["الرعد","إبراهيم","الحجر","النحل","الإسراء","الكهف"],
    (16,18): ["الكهف","مريم","طه","الأنبياء","الحج","المؤمنون","النور","الفرقان"],
    (19,21): ["الفرقان","الشعراء","النمل","القصص","العنكبوت","الروم","لقمان","السجدة","الأحزاب"],
    (22,24): ["الأحزاب","سبأ","فاطر","يس","الصافات","ص","الزمر"],
    (25,27): ["الزمر","غافر","فصلت","الشورى","الزخرف","الدخان","الجاثية","الأحقاف","محمد","الفتح","الحجرات","ق","الذاريات"],
    (28,30): [
        "المجادلة","الحشر","الممتحنة","الصف","الجمعة","المنافقون","التغابن","الطلاق","التحريم",
        "الملك","القلم","الحاقة","المعارج","نوح","الجن","المزمل","المدثر","القيامة","الإنسان",
        "المرسلات","النبأ","النازعات","عبس","التكوير","الإنفطار","المطففين","الإنشقاق","البروج",
        "الطارق","الأعلى","الغاشية","الفجر","البلد","الشمس","الليل","الضحى","الشرح","التين",
        "العلق","القدر","البينة","الزلزلة","العاديات","القارعة","التكاثر","العصر","الهمزة",
        "الفيل","قريش","الماعون","الكوثر","الكافرون","النصر","المسد","الإخلاص","الفلق","الناس"
    ],
}

# لو عندك اختلافات تهجئة، ضيف تطبيع بسيط هنا
NORMALIZE = {
    "الانفطار": "الإنفطار",
    "الانشقاق": "الإنشقاق",
    "يس": "يس",
}

def norm(name):
    return NORMALIZE.get(name, name)

class Command(BaseCommand):
    help = "Seed/Update all 114 surahs with coarse juz ranges (merge by min/max across 3-juz groups)."

    def handle(self, *args, **opts):
        # ابني خريطة اسم السورة → (min_juz, max_juz)
        ranges = {}
        for (jf, jt), names in GROUPS.items():
            for raw in names:
                name = norm(raw)
                if name not in ranges:
                    ranges[name] = [jf, jt]
                else:
                    ranges[name][0] = min(ranges[name][0], jf)
                    ranges[name][1] = max(ranges[name][1], jt)

        created = 0
        updated = 0
        for name, (jf, jt) in ranges.items():
            obj, was_created = Surah.objects.get_or_create(
                name=name,
                defaults={"juz_from": jf, "juz_to": jt}
            )
            if was_created:
                created += 1
            else:
                if obj.juz_from != jf or obj.juz_to != jt:
                    obj.juz_from, obj.juz_to = jf, jt
                    obj.save(update_fields=["juz_from","juz_to"])
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Created {created}, Updated {updated}."))
