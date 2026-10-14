# الجلسة الجديدة — ربط التطبيق بالتدريب وتطوير عرض الوكلاء

هذه خطة مكتوبة بعد قراءة ملفات التطبيق ومسار التدريب في 7 أكتوبر 2026. لم يُعدّل كود التطبيق أو التدريب في جلسة التخطيط.

## الهدف

عندما يصل تدريب جديد أو ملف نتائج جديد إلى المشروع، يلتقطه التطبيق وهو مفتوح ويعرض ما أصبح جاهزًا تلقائيًا. بعد تثبيت الربط نطوّر عرض قرارات الوكيل والمحرك بنفس مستوى الوضوح الذي وصلنا إليه في مختبر الشرح.

مختبر الشرح موجود داخل `GRAD-project/Explanatory Simulation` ويبقى مستقلًا. العمل القادم داخل `GRAD-project/app`.

## ما وجدته

1. الواجهة تقرأ النتائج عند فتح الصفحة؛ لا تتابع الملفات الجديدة تلقائيًا أثناء بقائها مفتوحة.
2. قارئ الوكلاء يدعم المجلدات المباشرة، ويحتاج دعم تنظيم التدريب المتداخل الذي يستخدمه `train_all.py`.
3. اكتمال حفظ النموذج يسبق اكتمال بقية ملفات التدريب. نحتاج حالة واضحة: يتدرّب، ينهي الحفظ، اكتمل، ينتظر التقييم.
4. ملخصات المجموعتين موجودة؛ تسجيلات خطوات التدريب والتقييم غير موجودة في هذه النسخة. نعرض الملخص المتاح ونفعّل التسجيل عند وصوله.
5. صفحة النتائج الحالية أنجزت R1a. نكمل R1b من تصميمها الموجود، مع الحفاظ على بصمة المحاكي وصحة المقارنة.

## ترتيب العمل

| الدفعة | الناتج |
|---|---|
| A1–A3، أول جلسة تنفيذ | اكتشاف الملفات، فحص جاهزيتها، تحديث الصفحات تلقائيًا، منع إعادة استخدام عرض وكيل قديم، وضبط التشغيل المحلي |
| B1 | إظهار مجموعات الوكلاء ونتائجها ورسومها، استكمالًا لعمل R1b |
| B2 | استعراض القرار خطوة بخطوة من التسجيلات المتاحة |
| B3 | تحسين النموذج والهواء والتبريد والكاميرات وعرض المقارنة، والتحقق على الكمبيوتر ومقاس الجوال |
| C1 / R2 | استكمال رسوم المحاكي مقابل السيارة وبقية الرسومات المرجعية، مع مصادرها وحالة صلاحية بياناتها |

**تلقائي هنا يعني قراءة وعرض ما أنتجه التدريب.** اكتمال التدريب لا ينتج التقييم بنفسه في المسار الحالي. إذا لم تصل ملفات التقييم، يظهر ذلك بوضوح؛ فتح التطبيق لا يشغّل تدريبًا أو تقييمًا جديدًا من تلقاء نفسه.

## الرسومات المطلوبة

المرجع الذي اختاره المستخدم: [B58 Preview Study](https://claude.ai/artifact/16mUxgXuHMzLppvT9Df4rM). تمت مشاهدة الصفحة وتفاعل تبديل المشغّلات في المتصفح.

أُضيفت قائمة **25 لوحة تحليل** مرتبطة بمصادرها: منحنيات الحرارة والضرر، نتائج كل وكيل وتوزيعها، مقارنة أزواج الوكلاء، الضرر مقابل الوقود، منحنيات التدريب، أوامر المشغّلات الخمسة، خرائط السرعة والميل، ومقارنة المحاكي بقياسات السيارة. معها رسوم زمنية مترابطة للملاحظة والأمر المطلوب وما طُبّق والمكافأة ونتيجة القرار.

المطلوب رسوم تفاعلية: تبديل القنوات والوكلاء، تكبير وإعادة ضبط، تحديد لحظة واحدة في الرسومات والنموذج، إظهار القيم باللمس ولوحة المفاتيح، وجدول أرقام لكل رسم. تبقى الرسومات مقسّمة إلى مجموعات واضحة على الجوال.

التفاصيل ومصادر كل رسم: [مواصفات الرسومات](docs/superpowers/specs/2026-10-07-training-linked-app-visuals.md). نأخذ طريقة العرض من المرجع؛ القيم والاستنتاجات تأتي من ملفات المشروع مع تاريخها وبصمتها. الرسم الذي تنقص بياناته يوضح الملف المطلوب بدل عرض أرقام افتراضية.

## توزيع العمل المعتمد

أكّد المستخدم هذا التوزيع في 7 أكتوبر 2026؛ يُطبّق عند بدء جلسة التنفيذ:

| النموذج | الدور | جهد التفكير |
|---|---|---|
| GPT 6.1 Sol — `gpt-6.1-sol` | المخطّط والمنسّق: يقسّم المهام، يثبت الواجهات بين الملفات، يراجع التنفيذ ويدمج التغييرات ويتحقق من النتيجة | `high` |
| GPT 6 Luna — `gpt-6-luna` | وكلاء فرعيون ينفّذون مهام محددة ويشغّلون اختباراتهم | `high` |
| GPT 6 Astra — `gpt-6-astra` | تصعيد فقط لمشكلة محددة لم يحسمها Sol بعد فحصها؛ يعود القرار بعدها إلى Sol | `high` |

يشغّل Sol حتى عاملين Luna بالتوازي عندما تكون الملفات مستقلة، ويمنع تعديل الملف نفسه من عاملين في الوقت نفسه. يراجع النتائج بنفسه؛ لا يستدعي Astra تلقائيًا لكل دفعة. إعداد `high` يُمرَّر صراحة إلى الوكلاء الفرعيين.

هذه أدوار نماذج التطوير في الجلسة، وليست إعدادات وكلاء التدريب داخل التطبيق. تدوينها هنا لا يغيّر نموذج المحادثة أو إعداداته تلقائيًا.

## النص الجاهز للجلسة الجديدة

انسخ هذا النص:

```text
أنا جاد. نبدأ الآن تطوير تطبيق التدريب والوكلاء، بعد الانتهاء من Explanatory Simulation.

Repository: C:\Users\admin\Documents\graduation project\GRAD-project
Work target: app/
Keep Explanatory Simulation/ separate and unchanged.

Development workflow — explicitly authorized:
- GPT 6.1 Sol (gpt-6.1-sol), high: orchestrator/planner, integration and verification.
- GPT 6 Luna (gpt-6-luna), high: worker sub-agents for bounded implementation tasks.
- GPT 6 Astra (gpt-6-astra), high: escalation only for a specific issue Sol cannot
  resolve from the evidence; not a routine worker or mandatory reviewer.
Use at most two Luna workers concurrently, with disjoint file ownership and agreed
interfaces. Pass the model and reasoning effort explicitly when spawning workers.
Sol reviews their work and owns final acceptance. Reuse this authorization; do not
ask again merely to delegate a task within the plan. Follow the plan's escalation rules.
These development roles do not change the trained policies or in-app model settings.

Read:
1. NEXT_SESSION_2026-10-07_training-linked-app.md
2. docs/superpowers/specs/2026-10-07-training-linked-app-design.md
3. docs/superpowers/plans/2026-10-07-training-linked-app.md
4. CLAUDE.md and the applicable repository instructions.
5. docs/superpowers/specs/2026-10-07-training-linked-app-visuals.md

Graphics reference: https://claude.ai/artifact/16mUxgXuHMzLppvT9Df4rM
The graphics addendum is required: 25 reference panels G01–G25 plus linked decision
timelines, with interactive values, channel/policy selection, zoom/reset and exact-value
tables. B1/B2/B3/C1 deliver this coverage; A1–A3 remain the first execution batch.
Use the reference's presentation patterns with the project's own source-aware data.
Do not copy its historical numbers, conclusions or unsupported validation labels.

Implement A1–A3 from the new plan, then verify on desktop and a mobile-sized viewport.
The app must discover supported local training and result artifacts while already open,
including nested runs, and show their readiness without a manual reload or server restart.
Preserve the selected experiment and playback when unrelated artifacts arrive. Invalidate
old replay frames and answers when a selected model is replaced at the same path.

Use the existing app and scientific guards. Do not change physics, rewards, protocols or
training code; do not start training/evaluation, overwrite runs/results, call external AI
services automatically, change network exposure, commit or push. Preserve unrelated edits.
Use temporary artifacts for arrival/partial-write/replacement tests.

The app is FastAPI + native JS modules + Three.js. It already has /agents, /results and
/simulation. The first session delivers the automatic-link foundation; B1 then extends
agent-set results, B2 recorded decisions, B3 the visual/mechanical experience, and C1
the remaining reference graphics / R2 simulator-versus-car figures.

Report what was actually verified, including skipped checks and missing recordings.
Keep updates to me concise and in Arabic. Do not restart the design discussion from zero.
```

## تفاصيل التنفيذ

- التصميم: [training-linked-app-design](docs/superpowers/specs/2026-10-07-training-linked-app-design.md)
- المهام والاختبارات: [training-linked-app plan](docs/superpowers/plans/2026-10-07-training-linked-app.md)
- الرسومات: [visual requirements](docs/superpowers/specs/2026-10-07-training-linked-app-visuals.md)
- تصميم النتائج السابق: [results-tab-design](docs/superpowers/specs/2026-09-30-results-tab-design.md)

قبل التنفيذ افحص حالة Git وبيئة Python مجددًا؛ قد تتغير الملفات بسبب عمل جلسة أخرى. نتائج اختبارات مختبر الشرح السابقة ليست دليلًا على اختبارات هذا التطبيق.
