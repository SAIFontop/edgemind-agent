# EdgeMind Agent 🧠

> نظام ذكاء اصطناعي يعمل كطبقة تحكم ذكية فوق Raspberry Pi OS

## 🎯 ما هو EdgeMind Agent؟

نظام ذكاء اصطناعي يعمل كـ **طبقة تحكم ذكية** فوق Raspberry Pi OS:
- ليس جزءًا من النظام
- لا يملك صلاحيات مباشرة
- يعمل كـ **عقل تحليل وتخطيط**

```
النظام الحقيقي = Raspberry Pi OS
الذكاء = Gemini API
التنفيذ = Security Gateway (آمن)
```

## 🏗️ هيكل المشروع

```
edgemind-agent/
├── src/
│   ├── core/
│   │   ├── agent.py           # العقل الرئيسي
│   │   ├── context_builder.py # جامع السياق
│   │   └── decision_engine.py # محرك القرارات
│   ├── gateway/
│   │   ├── security_gateway.py # بوابة الأمان
│   │   ├── whitelist.py        # قائمة الأوامر المسموحة
│   │   └── executor.py         # منفذ الأوامر
│   ├── api/
│   │   └── gemini_client.py    # عميل Gemini API
│   ├── interface/
│   │   ├── cli.py              # واجهة سطر الأوامر
│   │   └── web_server.py       # واجهة الويب
│   └── utils/
│       ├── logger.py           # نظام التسجيل
│       └── validators.py       # التحقق من المدخلات
├── config/
│   ├── settings.yaml           # إعدادات النظام
│   ├── whitelist.yaml          # الأوامر المسموحة
│   └── system_prompt.txt       # برومبت Gemini
├── logs/                       # سجلات النظام
├── tests/                      # الاختبارات
├── requirements.txt
└── main.py
```

## 🚀 التثبيت

```bash
# استنساخ المشروع
git clone https://github.com/your-repo/edgemind-agent.git
cd edgemind-agent

# إنشاء بيئة افتراضية
python3 -m venv venv
source venv/bin/activate

# تثبيت المتطلبات
pip install -r requirements.txt

# إعداد مفتاح API
export GEMINI_API_KEY="your-api-key"

# تشغيل النظام
python main.py
```

## 📊 تدفق العمل

```
User
 ↓
EdgeMind Interface (CLI / Web)
 ↓
Context Builder (Logs / Errors / State)
 ↓
Gemini API (Brain)
 ↓
Decision Output (JSON)
 ↓
Security Gateway
 ↓
Raspberry Pi OS
```

## 🔐 مبدأ الأمان

> **الذكاء لا ينفّذ — الذكاء يقرّر**

| Gemini API | Raspberry Pi OS |
|------------|-----------------|
| يفهم | لا يستقبل إلا أوامر مُصرّح بها |
| يحلل | عبر Whitelist فقط |
| يخطط | |
| يرفض الخطر | |

## 📋 أنواع المهام

- ✅ System diagnostics
- ✅ Network analysis
- ✅ Service health
- ✅ File inspection
- ✅ Automation planning
- ✅ Advisory DevOps

## 📝 الترخيص

MIT License
