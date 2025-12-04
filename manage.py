#!/usr/bin/env python
import os
import sys
# 1. استدعاء مكتبة dotenv
from dotenv import load_dotenv

def main():
    # 2. تحميل المتغيرات من ملف .env فور التشغيل
    load_dotenv()

    # لاحظ أنني تركت اسم الإعدادات كما هو في كودك الأصلي
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hifztracker.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()