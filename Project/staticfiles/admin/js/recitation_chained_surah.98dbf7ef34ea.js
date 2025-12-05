// في ملف: apps/accounts/static/admin/js/recitation_chained_surah.js

'use strict';
{
    document.addEventListener('DOMContentLoaded', function() {
        const halaqaSelect = document.querySelector('#id_halaqa');
        const surahSelect = document.querySelector('#id_surah');
        
        if (!halaqaSelect || !surahSelect) {
            console.error("لم يتم العثور على حقل الحلقة أو السورة.");
            return;
        }

        // ---  منطق ذكي لتحديد الرابط الصحيح ---
        const currentPath = window.location.pathname;
        // مثال: /admin/accounts/recitation/add/
        const pathParts = currentPath.split('/').filter(p => p);
        // النتيجة: ["admin", "accounts", "recitation", "add"]
        // سنستخدم أول 3 أجزاء لبناء الرابط
        const adminModelPath = `/${pathParts[0]}/${pathParts[1]}/${pathParts[2]}/`;
        const url = `${adminModelPath}surah-options/`;
        // سيقوم ببناء الرابط الصحيح تلقائياً سواء كنت في صفحة التسميع أو المراجعة
        
        const updateSurahOptions = () => {
            const halaqaId = halaqaSelect.value;
            surahSelect.innerHTML = '<option value="">---------</option>';

            if (!halaqaId) {
                surahSelect.disabled = true;
                return;
            }
            surahSelect.disabled = false;

            fetch(`${url}?halaqa=${halaqaId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.ok && data.results) {
                        const currentSurahId = surahSelect.value;
                        data.results.forEach(surah => {
                            const option = new Option(surah.name, surah.id);
                            surahSelect.add(option);
                        });
                        if (currentSurahId) {
                           surahSelect.value = currentSurahId;
                        }
                    }
                })
                .catch(error => console.error('حدث خطأ أثناء جلب السور:', error));
        };

        halaqaSelect.addEventListener('change', updateSurahOptions);
        if (halaqaSelect.value) {
            updateSurahOptions();
        } else {
            surahSelect.disabled = true;
        }
    });
}