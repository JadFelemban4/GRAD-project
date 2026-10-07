# مختبر السوبرا — النسخة العربية

**ابدأ:** افتح `start.cmd`؛ يبدأ المختبر بعرض «السيارة ومسار الهواء». اضغط «التيربو» على السيارة لتكبيره. ثم اختر «رؤية الطريق والقرار» واضغط «شاهد مثالًا قبل الصعود».

الواجهة عربية من اليمين إلى اليسار، وتعرض درسًا وتجربة واحدة في كل خطوة. تظهر الدروس القريبة فقط، ويمكن فتح خارطة الدروس والتفاصيل التقنية عند الحاجة. استُخدم نموذج السوبرا الجاهز من `GRAD-project/app/static/sim/scene.mjs`، مع إصلاح خطوط الكبوت العائمة وتجهيز مقطع داخلي. المحرك المكبّر له عرض مستقل لشرح الأشواط؛ والأنابيب داخل حدود السيارة وتحت الكبوت.

المختبر الجديد يتيح عزل الأجزاء، المقطع الداخلي، الشفافية، التفكيك التدريجي وإعادة التجميع، زوايا الكاميرا والعرض الموسّع. مدخلات RPM والضغط والشرارة ولامدا تستدعي محاكي المشروع الفعلي. حركة الآلية وأبعاد التفكيك تعليمية وليست ملف CAD أو قياسات ضغط داخل الأسطوانة. الدوران والتكبير وإعادة المنظور متاحة داخل النموذج. حسابات الفيزياء والمصادر والنتائج البحثية هي حسابات المشروع الأصلية. الشيفرة والأرقام والوحدات تحتفظ باتجاهها الطبيعي من اليسار إلى اليمين.

تفاصيل الفحص الجديد: `docs/ARABIC_MODEL_VALIDATION.md`. الصور: `qa/arabic-exterior.png` و`qa/arabic-cutaway.png` و`qa/arabic-engine.png` و`qa/arabic-mobile.png`.

المختبر الداكن والتفكيك التفاعلي: `docs/STUDIO_VALIDATION.md`. معاينته: `qa/studio-engine.png` و`qa/studio-desktop.png` و`qa/studio-mobile.png`.

**الجديد من المراجع:** اختر «التيربو مكبّر» لفحص التيربو واتباع المسارين بخمس خطوات. اضغط «ثبّت المرجع» قبل تغيير مدخل واحد؛ «ارجع للمرجع» يعيد المدخلات ويحسب النتيجة من جديد. المرجع مؤقت أثناء فتح المشهد. حركة التيربو تعليمية؛ ليست قياسًا لسرعته الفعلية. تقييم المراجع الـ17: `docs/REFERENCE_REVIEW_2026-10-04.md`، وصورة النتيجة: `qa/studio-turbo.png`.

**السيارة وفكرة المشروع:** النموذج المكبّر نفسه مركّب داخل السيارة. الأسهم الزرقاء تتبع الهواء من الخارج عبر الفلتر والضاغط والمبرد إلى المحرك؛ البرتقالية تتبع العادم عبر التوربين إلى الخلف. صفحة الرؤية تربط معاينة الطريق بالحالة الحالية ثم أوامر ECU المطبّقة. المثال يفتح الطريق المقفل عند 170 ثانية بسياسة يدوية استباقية؛ يمكنك اختيار SAC بصورة منفصلة. الرؤية هنا بيانات مسار التجربة، وليست كاميرا. الفحص: `docs/VEHICLE_PROJECT_VALIDATION.md`؛ نجح البناء و51 اختبارًا.

## حدود مختبر الشرح

`Explanatory Simulation` بيئة تعليمية داخل `GRAD-project` لفهم المشروع: دخول الهواء وخروج العادم → الاحتراق والعزم → التيربو → الذاكرة الحرارية → الرؤية وقرار المشرف. خارطة الشرح تفتح المشاهد الموجودة وتوضح في كل جزء ما يدخل ويخرج وصلته بهدف المشروع، مع سؤال قصير لاختبار الفهم.

تقرير تحقق الخارطة والعربية/الإنجليزية والمظهرين على الكمبيوتر والجوال: `docs/LEARNING_PURPOSE_VALIDATION.md`.

تجارب التحكم القصيرة داخل المختبر تشرح أثر المدخلات وحلقة القرار باستخدام شيفرة المشروع الأصلية. متابعة تشغيل الوكلاء الكامل وإدارة تجاربهم لها بيئة مستقلة في `GRAD-project/app`؛ تبقى خارج نطاق تطوير مختبر الشرح الحالي. يمكن ربط البيئتين لاحقًا بمدخل مشترك وروابط للدروس المناسبة.

### Learning scope

`Explanatory Simulation` is a learning environment inside `GRAD-project`: air and exhaust paths → combustion and torque → turbo → thermal memory → road preview and supervisor decisions. The learning map opens existing scenes, explains each part's inputs, outputs and role in the project, and offers a short understanding check. Short control experiments explain the decision loop using the original project code. Full agent episode monitoring belongs to the separate `GRAD-project/app` environment. A shared entry point and links to relevant lessons can connect them later.

---

# Supra Lab

An interactive learning environment for the **local** GRAD project: nine guided lessons, a live physics sandbox, searchable source inspector, and fourteen viva questions. All learning code lives in this folder. The parent `GRAD-project` working tree supplies physics, derived parameters, recordings and current results. Historical reports call this folder `ex`; it was renamed and moved inside the project on 7 October 2026.

## Launch

Double-click **start.cmd**. It opens http://127.0.0.1:8765. Keep the server terminal open; Ctrl+C stops a server owned by the launcher. The frontend is already built in `dist` in this workspace.

PowerShell alternative:

```powershell
cd 'C:\Users\admin\Documents\graduation project\GRAD-project\Explanatory Simulation'
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

The launcher uses `..\.venv\Scripts\python.exe`. If that environment is missing, create an environment **inside Explanatory Simulation**, install the parent project's Python requirements plus `backend/requirements.txt`, and run its Python interpreter with `launch.py`. Do not overwrite an existing core environment.

## Start learning

1. In the first lesson, step once on flat road. Enable the road override, move grade to 12%, and advance 30 seconds. Watch torque demand rise.
2. Open Engine 101. Move RPM, manifold pressure, spark and lambda. Actual Python cycle calculations update after a short debounce; inspect all four strokes or animate the slowed cycle.
3. Heat the thermal lab, then scrub through cooling. Exhaust conditions drop while metal retains heat.
4. Load paired sighted/blind actors. Advance toward the climb at 180 s; see future slots diverge while both controllers still know current grade.
5. Trace a part to its real numbered source excerpt. Use viva practice to explain it aloud before revealing the answer.

## Development and verification

Node.js and the project's Python environment are required. Frontend dependencies are locked in package-lock.json; fonts are bundled locally.

```powershell
npm ci
npm run build
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
..\.venv\Scripts\python.exe launch.py --check
```

For development, use separate terminals:

```powershell
..\.venv\Scripts\python.exe -m backend.server
npm run dev
```

Vite uses port 5173 and proxies `/api` to loopback port 8765. The built frontend and API share port 8765. If an older API process is running, stop its own terminal and restart after backend changes.

## Evidence and limits

Live values are model outputs, not additional car measurements. Geometry and motion are conceptual. Direct engine points need not be vehicle-feasible. The damage proxy is not measured component lifetime. Scored dt=1 episodes retain the source thermal integration limitation; the separate thermal teaching lab uses 0.1 s substeps. Exported actor reruns are **unverified reenactments**, separate from recorded results. The current paired preview effect is **inconclusive**.

See docs/PROJECT_MAP.md, SOURCE_MAP.md, VARIABLES.md, ARCHITECTURE.md, LEARNING_FLOW.md, VALIDATION.md, LIMITATIONS.md, DECISIONS.md and TASKS.md for continuation details.

