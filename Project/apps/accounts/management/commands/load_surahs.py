from django.core.management.base import BaseCommand
from apps.accounts.models import Surah

SURAH_DATA = [
    # name, juz_from, juz_to  (تقريبية/إدارية – عدّلها لاحقًا كما تشاء)
    ("الفاتحة", 1, 1),
    ("البقرة", 1, 3),
    ("آل عمران", 3, 4),
    ("النساء", 4, 6),
    ("المائدة", 6, 7),
    ("الأنعام", 7, 8),
    ("الأعراف", 8, 9),
    ("الأنفال", 9, 10),
    ("التوبة", 10, 11),
    ("يونس", 11, 11),
    ("هود", 11, 12),
    ("يوسف", 12, 13),
    ("الرعد", 13, 13),
    ("إبراهيم", 13, 13),
    ("الحجر", 14, 14),
    ("النحل", 14, 14),
    ("الإسراء", 15, 15),
    # كمّل بقية السور لاحقًا...
]

class Command(BaseCommand):
    help = "Load or update Surah data (name ↔ juz range)."

    def handle(self, *args, **kwargs):
        for name, jf, jt in SURAH_DATA:
            Surah.objects.update_or_create(
                name=name,
                defaults={"juz_from": jf, "juz_to": jt},
            )
        self.stdout.write(self.style.SUCCESS("Surah data loaded/updated."))
