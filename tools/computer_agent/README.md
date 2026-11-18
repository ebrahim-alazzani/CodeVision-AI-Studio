# 🤖 CodeVision Computer Agent

وكيل ذكي بسيط وسريع يستخدم الكمبيوتر نيابة عنك. يلتقط الشاشة، يفكر باستخدام نموذج Gemini، وينفذ الإجراءات تلقائياً.

## كيف يعمل؟

```
📸 التقاط الشاشة ──➜ 🧠 Gemini يحلل ويقرر ──➜ ⚡ تنفيذ الإجراء ──➜ 🔄 تكرار
```

| الوحدة | الملف | الوظيفة |
|--------|-------|---------|
| الإعدادات | `config.py` | مفتاح API، أحجام اللقطات، التأخيرات |
| التقاط الشاشة | `screen.py` | أخذ لقطات سريعة بـ mss/pyautogui |
| التفكير | `brain.py` | إرسال اللقطة لـ Gemini والحصول على إجراء JSON |
| التنفيذ | `actions.py` | نقر، كتابة، تمرير، مفاتيح مركبة |
| الحلقة الرئيسية | `agent.py` | ربط كل شيء + الوضع التفاعلي |

## التثبيت السريع

```powershell
pip install pyautogui mss google-generativeai pyperclip
```

## الإعداد

1. احصل على مفتاح Gemini API مجاني من: https://aistudio.google.com/apikey
2. عيّنه كمتغير بيئة:
```powershell
$env:GEMINI_API_KEY = "your_key_here"
```
أو عدّله مباشرة في `config.py`.

## التشغيل

### الوضع التفاعلي (محادثة):
```powershell
python agent.py
```

### مهمة مباشرة:
```powershell
python agent.py "افتح المفكرة واكتب مرحباً بالعالم"
```

### عبر ملف bat:
```powershell
.\run_agent.bat
```

## أمثلة مهام يمكن تنفيذها

| المهمة | ما يفعله الوكيل |
|--------|-----------------|
| `"افتح المفكرة واكتب مرحباً"` | يفتح قائمة Start → يبحث → يفتح Notepad → يكتب |
| `"افتح المتصفح وابحث عن Python"` | يفتح Chrome → يكتب في شريط البحث → Enter |
| `"أغلق النافذة الحالية"` | ينفذ Alt+F4 |
| `"افتح الآلة الحاسبة واحسب 5+3"` | يفتح Calculator → ينقر الأرقام |

## ⚠️ إيقاف الطوارئ

**حرّك الماوس بسرعة للزاوية العليا اليسرى** من الشاشة لإيقاف الوكيل فوراً (ميزة أمان PyAutoGUI).

أو اضغط `Ctrl+C` في نافذة الطرفية.

## الاختبار

```powershell
python test_agent.py
```

## البنية التقنية

```
computer_agent/
├── config.py          # الإعدادات المركزية
├── screen.py          # التقاط الشاشة (mss + PIL)
├── brain.py           # التفكير (Gemini VLM API)
├── actions.py         # تنفيذ الإجراءات (pyautogui)
├── agent.py           # الحلقة الرئيسية
├── test_agent.py      # اختبارات
├── run_agent.bat      # تشغيل سريع
├── requirements.txt   # الاعتماديات
├── screenshots/       # لقطات الشاشة المحفوظة
└── logs/              # سجلات المهام (JSON)
```
