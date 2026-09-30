// Every string the /agents page shows, in Arabic and English.
//
// The lab's i18n.mjs owns t(), applyTranslations() and STRINGS; this file only
// ADDS to STRINGS, once, at import, and refuses to overwrite anything. The lab
// page never imports this file, so /simulation's strings are exactly what they
// were. The same three rules as i18n.mjs apply (read its header): both
// languages carry the same keys, numbers go through {placeholders}, and the
// honesty captions are load-bearing text, not copy.
//
// Two rules of this page, pinned by agents-strings.test.mjs:
//  - The engine computer is always «حاسوب المحرك المنمذَج», the MODELLED one.
//  - No string says preview helps. This page shows one episode; the verdict
//    box quotes what the experiment found, word for word from results/.
//
// Arabic lines are from design sections 5 and 6
// (docs/superpowers/specs/2026-09-26-agent-replay-design.md), verbatim where the
// design gives them. \u200f is a right-to-left mark; \u2066...\u2069 would isolate
// a left-to-right run inside an Arabic line, which is how agent-picker.mjs
// (formatDiff) writes a pair's table number. The pair row subtracts with U+2212,
// written here as its escape; agents-strings.test.mjs pins every one of them.
//
// M3 adds the models panel's strings (agents.models.*; model-panel.mjs) and
// the pause panel's empty line (agents.pause.empty), from sections 7.5b, 7.7,
// 7.8 and 7.9 of docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md,
// verbatim where it gives them. The en dash in '70–500 ms' and the section
// sign in 'MCA §4.1' are ordinary characters. The two Arabic latency lines
// carry escapes: each Latin run that must keep its order ("{ms} ms",
// "{device}", "70–500 ms") is a left-to-right isolate, U+2066 ... U+2069,
// or the line draws "65 ms" as "ms 65" (the M3 final review, 29 Sep).
//
// The jev key field (Jad, 29 Sep, after M3) adds agents.models.jev.key.*,
// agents.models.jev.status.page, agents.models.jev.source.* (so the status
// line names a source in words) and the codes bad_key and bad_key_request,
// verbatim from its brief; agents-strings.test.mjs pins them.

import { STRINGS } from './i18n.mjs';

export const AGENT_STRINGS = {
  ar: {
    // --- document, intro and badge
    'agents.page.title': 'الوكلاء — GRAD',
    'agents.intro.heading': 'ماذا قرّر كل وكيل، ثانيةً بثانية',
    'agents.intro.note': 'حلقة اختبار واحدة تُحسب الآن من الشبكتين المدرَّبتين، على الطريق المحاكى نفسه للسيارتين.',
    'agents.badge': 'محاكاة: سيناريو إجهاد اصطناعي — تسلّق متواصل {grade}٪ عند {v} كم/س في {t} °م، أقسى من أي تسلّق مسجّل؛ لا يعني ذلك أنه أحرّ من كل لحظة في الرحلات المسجّلة',
    'agents.badge.short': 'محاكاة',

    // --- picker
    'agents.pick.experiment': 'التجربة',
    'agents.pick.pair': 'الزوج',
    'agents.pick.episode': 'الحلقة',
    'agents.pick.none': 'لم يُختر شيء بعد: اختر تجربة، ثم زوجاً، ثم حلقة، ثم اضغط احسب',
    'agents.pick.episode_option': 'حلقة {idx} · الصعود عند {start} ث · {grade}٪ · الأوزان: عزم {w0} / وقود {w1} / عمر المكوّنات {w2}',
    'agents.pick.budget': 'دُرِّب {budget} خطوة (من final.zip)',
    'agents.compute': 'احسب',
    'agents.compute_aria': 'احسب هذه الحلقة للوكيلين الآن',
    'agents.prompt': 'اختر تجربة وزوجاً وحلقة ثم اضغط احسب',

    // --- loading and errors
    'agents.load.networks': 'تحميل الشبكتين…',
    'agents.load.building': 'تُحسب الحلقة… {percent}٪',
    'agents.load.busy': 'تُحسب حلقة أخرى الآن ({runs} بذرة {seed} حلقة {ep}) — اضغط احسب لإيقافها وبدء هذه',
    'agents.load.error': 'تعذّر الحساب: {message}',
    'agents.load.server_down': 'الخادم غير متاح',
    'agents.load.retry': 'أعد المحاولة',
    'agents.load.refused': 'رُفض تشغيل هذا الزوج، ولم يُحمَّل أي نموذج:',
    'agents.load.not_found': 'لا توجد تجربة أو زوج أو حلقة بهذا الاسم',
    'agents.load.no_sb3': 'لا يمكن التشغيل: مكتبة stable-baselines3 غير مثبّتة',

    // --- timeline
    'agents.time.computed': 'حُسب حتى {done} · تنتهي الحلقة عند {end}',
    'agents.time.waiting': 'ينتظر الحساب…',
    'agents.dt.caption': 'تُعاد هنا بخطوة 1.0 ث، الخطوة التي قُيِّم بها الوكيلان؛ دُرِّبا بخطوة {train_dt} ث. مشكلة معروفة لم تُحلّ (AUDIT2.md H2\u20112)؛ لم يُقَس هل تؤثر في الوكيلين بالقدر نفسه',
    'agents.dt.same': 'تُعاد هنا بخطوة 1.0 ث، الخطوة التي قُيِّم بها الوكيلان ودُرِّبا بها',
    'agents.dt.not_recorded': 'تُعاد هنا بخطوة 1.0 ث، الخطوة التي قُيِّم بها الوكيلان؛ خطوة التدريب غير مسجّلة',

    // --- pause panel
    'agents.pause.heading': 'القرار المطبَّق من الثانية {k} إلى {k1}',
    'agents.pause.grade_now': 'ميل الطريق الآن {grade}٪',
    'agents.pause.weights': 'ما طُلب من الوكيلين في هذه الحلقة: عزم {w0} · وقود {w1} · عمر المكوّنات {w2}',
    'agents.action.spark': 'تعديل توقيت الشرارة',
    'agents.action.lambda': 'تعديل خليط الوقود (لامدا)',
    'agents.action.boost': 'إزاحة سقف ضغط الشحن',
    'agents.action.fan': 'مروحة التبريد',
    'agents.action.pump': 'مضخة سائل التبريد',
    'agents.action.tick_trim': 'بلا تعديل',
    'agents.action.tick_fan': 'قيمة صف "حاسوب المحرك الأساسي" في النتائج (1.0 ثابتة)؛ الحاسوب المنمذَج نفسه يجدول المروحة 0 أو 0.4 أو 1.0 حسب حرارة سائل التبريد',
    'agents.action.tick_pump': 'قيمة صف "حاسوب المحرك الأساسي" في النتائج (1.0 ثابتة)، وهي أيضاً ما يشغّل به الحاسوب المنمذَج المضخة طوال الوقت',
    'agents.action.held': 'أمر به {x}؛ قيّده حد سرعة التغيير',
    'agents.action.map': 'ضغط المشعب الآن {map} كيلوباسكال؛ السقف نفسه يُحسب داخل الحلقة ولا يُعرض',
    'agents.car.sighted': 'يرى الطريق أمامه',
    'agents.car.blind': 'لا يرى الطريق أمامه',
    'agents.seen.item': 'بعد {h} ث: {pct}٪',
    'agents.seen.blind': 'لا يرى الطريق أمامه: مداخل الاستباق عنده {zeros}',
    'agents.damage.caption': 'وحدات ضرر، في هذه الحلقة فقط حتى هذه اللحظة',
    'agents.turbine.label': 'حرارة غلاف التيربو مقابل عتبة الحماية',
    'agents.turbine.reading': '{turb} °م / {limit} °م',
    'agents.torque.label': 'العزم المُسلَّم {delivered} من {requested} نيوتن·م مطلوبة',
    'agents.device.line': 'التقييم المسجَّل حمّل الشبكة على الجهاز الافتراضي لـ SB3، وهو cuda على هذا الجهاز؛ ملفات النتائج لا تسجّل الجهاز. هذه الحلقة حُسبت على {device} \u200f(torch {torch}، SB3 {sb3})',
    'agents.device.warning': 'تنبيه: هذه الحلقة لم تُحسب على cuda، وحلقات المعالج تختلف عن حلقات cuda، فقد لا تطابق ما قُيِّم',
    'agents.fingerprint_taken': 'أُخذت بصمة المحاكي عند {time}؛ أعد تشغيل الخادم بعد تغيير أي ملف تدخل فيه البصمة',

    // --- scene and profile
    'agents.illustration': 'حلقة واحدة لزوج واحد مثال توضيحي، لا نتيجة. النتائج وسيطات عبر 20 حلقة، ولا يُحسب هنا أي فرق بين السيارتين',
    'agents.legend.same_place': 'السيارتان في المكان نفسه دائماً: السرعة يفرضها السيناريو، والوكيلان يختاران الحماية فقط',
    'agents.scene.slope': 'الميل غير مضخّم · السيارة ليست بمقياسها',
    'agents.scene.webgl_error': 'تعذّر عرض المشهد ثلاثي الأبعاد في هذا المتصفح. المقطع الجانبي ولوحة القرار يعملان.',
    'agents.profile.ve': 'المقياس الرأسي مضخّم ×{ve}',
    'agents.profile.rise': 'يرتفع الطريق {rise} م بينما يبقى الضغط {p} كيلوباسكال والحرارة {t} °م ثابتين طوال الحلقة',
    'agents.profile.climb': 'يبدأ الصعود عند {start} ث · {grade}٪',
    'agents.lane.stopped': 'توقفت محاكاة هذه السيارة عند الخطوة {k}',

    // --- verdict box
    'agents.verdict.heading': 'الحكم المسجَّل مسبقاً',
    'agents.verdict.source': 'results/{file}:{line}',
    'agents.verdict.scored_match': 'هذا هو الملف الذي قُيِّم: بصمة final.zip تطابق ما سجّلته النتائج',
    'agents.verdict.not_recorded': 'الملف المقيَّم غير مسجَّل في النتائج',
    'agents.verdict.no_result': 'لا ملف نتيجة لهذا الزوج',

    // --- footer (M3 attaches the hidden gesture here; nothing in M1)
    'agents.footer.index': '02 — AGENTS',

    // --- added by Task 9: the torque reading's label, the profile's km scale
    'agents.torque.heading': 'العزم المُسلَّم مقابل المطلوب',
    'agents.profile.km': '{km} كم',

    // --- added in M2: the working picker (agent-picker.mjs), Phase D's blind
    // car, the line shown while «احسب» stops another computation, and the
    // catalog's third 'scored' value (results/ records a different zip sha)
    'agents.pick.choose': 'اختر…',
    'agents.pick.pair_row': 'بذرة {seed} · الأعمى \u2212 المُبصر {diff}',
    'agents.pick.pair_no_row': 'بذرة {seed} · لا صف لهذه البذرة في جدول النتائج',
    'agents.pick.pair_refused': 'بذرة {seed} · لا يمكن تشغيله: {reason}',
    // {name} in the two refused labels is a first-strong isolate (U+2068 ...
    // U+2069): a made-up name ends in ')', which an Arabic line draws mirrored.
    'agents.pick.experiment_refused': '\u2068{name}\u2069 · لا يمكن تشغيل أي زوج: {reason}',
    'agents.pick.experiment_empty': '{name} · لا يوجد فيه أي زوج',
    'agents.pick.pair_qualifier': '(فرق وسيطَي 20 حلقة، لكلٍّ منها طريقها وأوزانها؛ ليست هذه الحلقة)',
    'agents.pick.pair_qualifier_same_road': '(فرق وسيطَي 20 حلقة على الطريق نفسه بأوزان مختلفة؛ ليست هذه الحلقة)',
    'agents.pick.episode_option_same_road': 'حلقة {idx} · الطريق نفسه · الأوزان: عزم {w0} / وقود {w1} / عمر المكوّنات {w2}',
    'agents.pick.same_road_note': 'الطريق نفسه ({start} ث · {grade}٪)؛ تختلف الحلقات في الأوزان فقط',
    'agents.pick.need_pair': 'اختر زوجاً',
    'agents.pick.need_episode': 'اختر حلقة',
    'agents.pick.catalog_loading': 'تحميل قائمة التجارب…',
    'agents.pick.catalog_error': 'تعذّر تحميل قائمة التجارب: {message}',
    'agents.pick.catalog_failed': 'لم تُحمَّل قائمة التجارب، فلا يمكن اختيار شيء بعد',
    'agents.pick.refused_summary': 'أزواج لا يمكن تشغيلها ({n})، ولماذا',
    'agents.pick.refused_pair': '\u2068{name}\u2069 · بذرة {seed}',
    'agents.car.blind_phase_d': 'لا يرى الطريق أمامه، لكنه قد يحفظه: الطريق نفسه في كل حلقة',
    'agents.seen.blind_phase_d': 'لا يرى الطريق أمامه: مداخل الاستباق عنده {zeros}؛ لكنه قد يحفظه: الطريق نفسه في كل حلقة ({cite})',
    'agents.load.stopping': 'يُوقَف حساب الحلقة السابقة ({runs} بذرة {seed} حلقة {ep})…',
    'agents.verdict.scored_mismatch': 'ليس هذا هو الملف الذي قُيِّم: بصمة final.zip تختلف عمّا سجّلته النتائج، فلا يمكن تشغيل هذا الزوج',

    // --- added in M3: the pause panel's empty line (design 7.8), and the models
    // panel behind the footer gesture (model-panel.mjs; design 7.5b, 7.7, 7.9).
    // The honesty lines are design 7.7 word for word; one error sentence per
    // model-panel.mjs ERROR_CODES entry, plus the page's own server_error.
    'agents.pause.empty': 'اضغط احسب، ثم أوقف العرض عند أي ثانية لترى ما قرّره كل وكيل',
    'agents.models.heading': 'اسأل نموذجاً لغوياً عن هذه الثانية',
    'agents.models.not_thesis': 'ليس جزءاً من الرسالة ولا من أي نتيجة. لا يقارن أي رقم هنا النموذجين بالوكيلين، ولا يُحسب أي فرق.',
    'agents.models.claim': 'الاحتمالات ادعاء النموذج نفسه، ولم تُختبر على هذه المهمة.',
    'agents.models.levels': 'كل نموذج يختار واحداً من خمسة مستويات لكل إجراء: للتعديلات الثلاثة الحدّان و"بلا تعديل" ونقطتان في المنتصف؛ وللمروحة والمضخة خمس قيم متساوية التباعد. المعروض هو اختيار النموذج نفسه، ولا يُحسب منه متوسط.',
    'agents.models.jev.name': 'typesafe.ai · {model}',
    'agents.models.jev.where': 'خدمة خارجية في الولايات المتحدة · كل ضغطة استدعاء مدفوع واحد',
    'agents.models.jev.text': 'خدمة خارجية تعمل في الولايات المتحدة. ليست جزءاً من الرسالة ولا من أي نتيجة، ولا يقارنها أي رقم بالوكلاء. هذه الصفحة لا تحفظ شيئاً؛ لكن اتفاقية المورّد تسمح له بالاحتفاظ بما يُرسل لاستخراج بيانات القياس بلا حدّ زمني (MCA §4.1). تُرسَل إليه حالة هذه الحلقة المحاكاة فقط، لا بيانات السيارة المسجّلة. كل ضغطة استدعاء واحد مدفوع. اتفاقية المورّد تمنع تدريب أي نموذج على تقليد إجاباته. شروط موقع المورّد موجّهة لزوّار الولايات المتحدة؛ هل الاستخدام من السعودية مسموح؟ غير معروف. ويقول المورّد إن النموذج ضعيف في الدقة العددية.',
    'agents.models.jev.status.configured': 'مفتاح مُعَدّ ({source})',
    'agents.models.jev.status.no_key': 'لا مفتاح؛ لن يُرسل شيء',
    'agents.models.jev.status.page': 'مفتاح من الصفحة، لهذه الجلسة فقط',
    'agents.models.jev.source.env': 'من متغيّر البيئة',
    'agents.models.jev.source.file': 'من ملف',
    'agents.models.jev.key.label': 'الصق مفتاح jev',
    'agents.models.jev.key.save': 'احفظ لهذه الجلسة',
    'agents.models.jev.key.clear': 'امسح',
    'agents.models.jev.key.note': 'يبقى في ذاكرة الخادم حتى يُغلق، ولا يُحفظ في أي ملف، ولا يعود إلى هذه الصفحة.',
    'agents.models.jev.ask': 'اسأل jev عن هذه الثانية (استدعاء مدفوع واحد)',
    'agents.models.jev.latency': '\u2066{ms} ms\u2069، مقيسة من هذا الجهاز (ادعاء المورّد \u206670–500 ms\u2069)',
    'agents.models.laya.name': 'Laya · {model} · laya {version}',
    'agents.models.laya.where': 'على هذا الجهاز ({device}) · مجاني، بلا مفتاح',
    'agents.models.laya.device_unknown': 'لم يُحمَّل بعد',
    'agents.models.laya.text': 'يعمل على هذا الجهاز ولا يُرسل شيئاً خارجه. تجربة تشغيل، لا تقييم. يقول ملف لايا نفسه إن نتيجة مثال لا تعني أنه مناسب للتحكم بالمحرك (README_AR.md:31). رخصة Apache 2.0.',
    'agents.models.laya.check': 'نسأل لايا مرتين، والخيارات بترتيبين متعاكسين. إذا تغيّر اختياره بتغيير الترتيب وحده، فذلك الاختيار لا يأتي من حالة المحرك.',
    'agents.models.laya.status.not_configured': 'غير مُعَدّ: LAYA_HOME',
    'agents.models.laya.status.not_found': 'لم يُعثر على لايا في LAYA_HOME، أو يقع داخل المستودع',
    'agents.models.laya.status.stopped': 'يُحمَّل عند أول سؤال',
    'agents.models.laya.status.starting': 'يُحمَّل على هذا الجهاز لأول مرة…',
    'agents.models.laya.status.ready': 'محمَّل على {device} حتى يُغلق الخادم',
    'agents.models.laya.status.failed': 'تعذّر التشغيل: {code}',
    'agents.models.laya.ask': 'اسأل لايا عن هذه الثانية (على هذا الجهاز)',
    'agents.models.laya.latency': '\u2066{ms} ms\u2069 على \u2066{device}\u2069',
    'agents.models.laya.first_load': 'التحميل الأول {s} ث',
    'agents.models.reason.pause': 'أوقف العرض أولاً',
    'agents.models.reason.not_done': 'انتظر حتى تكتمل الحلقة',
    'agents.models.reason.stopped': 'توقفت محاكاة المُبصر قبل هذه الثانية',
    'agents.models.reason.asking': 'يُسأل الآن…',
    'agents.models.ask_this': 'اسأل عن هذه الثانية',
    'agents.models.reference': 'طبّق الوكيلان في هذه الثانية:',
    'agents.models.choice': 'اختيار النموذج: {level} (الشبكة {net})',
    'agents.models.chosen_p': 'احتمال الخيار المختار {p}',
    'agents.models.reversed': 'بالترتيب المعكوس: {level}',
    'agents.models.held': 'ثبت',
    'agents.models.changed': 'تغيّر بتغيير الترتيب',
    'agents.models.footer': 'هدف لثانية واحدة: لم يُطبَّق ولم يُقيَّد بحد سرعة التغيير',
    'agents.models.sent': 'ما الذي أُرسل',
    'agents.models.no_answer': 'لا جواب — {code}: {sentence}',
    'agents.models.no_answer_plain': 'لا جواب — {sentence}',
    'agents.models.error.no_key': 'لا مفتاح، فلم يُرسل شيء.',
    'agents.models.error.network': 'تعذّر الوصول إلى الخدمة من هذا الجهاز.',
    'agents.models.error.timeout': 'انتهت المهلة دون جواب.',
    'agents.models.error.key_rejected': 'رفضت الخدمة المفتاح.',
    'agents.models.error.vendor_refused': 'رفضت الخدمة الطلب؛ قد لا يُسمح بالوصول من هذا الموقع.',
    'agents.models.error.request_rejected': 'رفضت الخدمة شكل الطلب: خلل في هذه الصفحة.',
    'agents.models.error.rate_limited': 'طلبات كثيرة؛ اسأل مرة أخرى بعد لحظة.',
    'agents.models.error.overloaded': 'الخدمة مشغولة؛ اسأل مرة أخرى بعد لحظة.',
    'agents.models.error.vendor_status': 'رفضت الخدمة الطلب (HTTP {status}). قد يعني ذلك أن الحساب بلا رصيد.',
    'agents.models.error.not_configured': 'لم يُعَدّ LAYA_HOME، فلم يُشغَّل شيء.',
    'agents.models.error.not_found': 'لم يُعثر على بايثون لايا أو مجلد نموذجه، أو يقعان داخل المستودع.',
    'agents.models.error.start_failed': 'خرج عامل لايا قبل أن يجهز.',
    'agents.models.error.start_timeout': 'لم يجهز عامل لايا خلال 90 ث، فأُوقف.',
    'agents.models.error.worker_error': 'أبلغ عامل لايا عن خطأ ({kind}).',
    'agents.models.error.worker_died': 'توقف عامل لايا في منتصف الطلب.',
    'agents.models.error.network_attempt': 'سجّل الحارس محاولة اتصال بالشبكة، فأُسقط الجواب وأُوقف العامل.',
    'agents.models.error.bad_answer': 'جاء جواب لا يمكن تحويله إلى إجراء، فلم يُعرض شيء.',
    'agents.models.error.foreign_origin': 'رُفض الطلب لأنه لم يأتِ من هذه الصفحة.',
    'agents.models.error.no_trace': 'هذه الحلقة لم تعد محفوظة في الخادم؛ اضغط احسب ثم اسأل.',
    'agents.models.error.step_not_computed': 'هذه الثانية لم تُحسب للمُبصر.',
    'agents.models.error.busy': 'سؤال آخر لهذا النموذج جارٍ الآن.',
    'agents.models.error.bad_key': 'تعذّر استعمال هذا المفتاح؛ لم يُحفظ شيء.',
    'agents.models.error.bad_key_request': 'طلب غير صالح؛ لم يُحفظ شيء.',
    'agents.models.error.server_error': 'خطأ في الخادم (HTTP {status})',

    // --- added 30 Sep 2026: an agent whose certificate was RECONSTRUCTED
    // (reconstruct_meta.py, read by app/agent_catalog.py), and the device its
    // committed scores were reproduced on. Each Latin run (a date, a file, a
    // list of episodes, a device) is a left-to-right isolate, as above.
    'agents.verdict.reconstructed': 'شهادة أُعيد بناؤها في \u2066{date}\u2069، ولم تُكتب عند بدء التدريب. أُعيد تشغيل حلقات مجمَّدة فساوت النتائج المحفوظة في \u2066{file}\u2069، وهي: \u2066{episodes}\u2069',
    'agents.device.line_reproduced': 'أُعيد إنتاج النتائج المحفوظة على \u2066{reproduced}\u2069 عند إعادة بناء الشهادة. هذه الحلقة حُسبت على {device} \u200f(torch {torch}، SB3 {sb3})',
    'agents.device.warning_reproduced': 'تنبيه: هذه الحلقة لم تُحسب على \u2066{reproduced}\u2069، فقد لا تطابق ما قُيِّم',
  },

  en: {
    // --- document, intro and badge
    'agents.page.title': 'Agents — GRAD',
    'agents.intro.heading': 'What each agent decided, second by second',
    'agents.intro.note': 'One test episode, computed now from the two trained networks, on the same simulated road for both cars.',
    'agents.badge': 'Simulation: a synthetic stress scenario, a sustained {grade} % climb at {v} km/h in {t} °C, harsher than any recorded climb; this does not mean it is hotter than every moment of the recorded drives',
    'agents.badge.short': 'Simulation',

    // --- picker
    'agents.pick.experiment': 'Experiment',
    'agents.pick.pair': 'Pair',
    'agents.pick.episode': 'Episode',
    'agents.pick.none': 'Nothing is selected yet: choose an experiment, then a pair, then an episode, then press Compute',
    'agents.pick.episode_option': 'Episode {idx} · climb at {start} s · {grade} % · weights: torque {w0} / fuel {w1} / component life {w2}',
    'agents.pick.budget': 'trained {budget} steps (from final.zip)',
    'agents.compute': 'Compute',
    'agents.compute_aria': 'Compute this episode for both agents now',
    'agents.prompt': 'Choose an experiment, a pair and an episode, then press Compute',

    // --- loading and errors
    'agents.load.networks': 'Loading the two networks…',
    'agents.load.building': 'Computing the episode… {percent} %',
    'agents.load.busy': 'Another episode is being computed now ({runs} seed {seed} episode {ep}) — press Compute to stop it and start this one',
    'agents.load.error': 'The computation failed: {message}',
    'agents.load.server_down': 'Server not reachable',
    'agents.load.retry': 'Retry',
    'agents.load.refused': 'This pair was refused and no model was loaded:',
    'agents.load.not_found': 'No experiment, pair or episode by that name',
    'agents.load.no_sb3': 'Cannot run: stable-baselines3 is not installed',

    // --- timeline
    'agents.time.computed': 'Computed up to {done} · the episode ends at {end}',
    'agents.time.waiting': 'Waiting for the computation…',
    'agents.dt.caption': 'Replayed here at a 1.0 s step, the step the agents were scored at; they were trained at {train_dt} s. A known, unresolved problem (AUDIT2.md H2\u20112); whether it affects both agents equally has not been measured',
    'agents.dt.same': 'Replayed here at a 1.0 s step, the step the agents were scored and trained at',
    'agents.dt.not_recorded': 'Replayed here at a 1.0 s step, the step the agents were scored at; the training step is not recorded',

    // --- pause panel
    'agents.pause.heading': 'The decision applied from second {k} to {k1}',
    'agents.pause.grade_now': 'Grade now {grade} %',
    'agents.pause.weights': 'What the agents were asked to weigh in this episode: torque {w0} · fuel {w1} · component life {w2}',
    'agents.action.spark': 'Spark timing trim',
    'agents.action.lambda': 'Fuel mixture trim (lambda)',
    'agents.action.boost': 'Boost-pressure ceiling offset',
    'agents.action.fan': 'Cooling fan',
    'agents.action.pump': 'Coolant pump',
    'agents.action.tick_trim': 'No change',
    'agents.action.tick_fan': "The value used by the results' 'baseline ECU' row (a constant 1.0); the modelled computer itself schedules the fan at 0, 0.4 or 1.0 by coolant temperature",
    'agents.action.tick_pump': "The value used by the results' 'baseline ECU' row (a constant 1.0), which is also what the modelled computer runs the pump at throughout",
    'agents.action.held': 'Commanded {x}; held back by the rate limit',
    'agents.action.map': 'Manifold pressure now {map} kPa; the ceiling itself is computed inside the loop and is not shown',
    'agents.car.sighted': 'Sees the road ahead',
    'agents.car.blind': 'Does not see the road ahead',
    'agents.seen.item': 'In {h} s: {pct} %',
    'agents.seen.blind': 'Does not see the road ahead: its preview inputs were {zeros}',
    'agents.damage.caption': 'Damage units, in this episode only, up to this moment',
    'agents.turbine.label': 'Turbine housing temperature against the protection limit',
    'agents.turbine.reading': '{turb} °C / {limit} °C',
    'agents.torque.label': 'Torque delivered {delivered} of {requested} N·m requested',
    'agents.device.line': "The recorded evaluation loaded the network on SB3's default device, which is cuda on this machine; the result files do not record the device. This episode was computed on {device} (torch {torch}, SB3 {sb3})",
    'agents.device.warning': 'Warning: this episode was not computed on cuda, and CPU episodes differ from CUDA ones, so it may not match what was scored',
    'agents.fingerprint_taken': 'Plant fingerprint taken at {time}; restart the server after changing a hashed file',

    // --- scene and profile
    'agents.illustration': 'One episode of one pair is an illustration, not a result. The results are medians over 20 episodes, and no difference between the cars is computed here',
    'agents.legend.same_place': 'Both cars are always at the same place: the scenario sets the speed, and the agents choose only the protection',
    'agents.scene.slope': 'Slope not exaggerated · car not to scale',
    'agents.scene.webgl_error': 'The 3D view could not be shown in this browser. The side profile and the decision panel still work.',
    'agents.profile.ve': 'Vertical scale exaggerated ×{ve}',
    'agents.profile.rise': 'The road rises {rise} m while pressure stays at {p} kPa and temperature at {t} °C throughout the episode',
    'agents.profile.climb': 'Climb starts at {start} s · {grade} %',
    'agents.lane.stopped': "This car's simulation stopped at step {k}",

    // --- verdict box
    'agents.verdict.heading': 'The preregistered verdict',
    'agents.verdict.source': 'results/{file}:{line}',
    'agents.verdict.scored_match': 'This is the scored artefact: the final.zip sha matches the one the results recorded',
    'agents.verdict.not_recorded': 'Scored artefact not recorded in results',
    'agents.verdict.no_result': 'No result file for this pair',

    // --- footer (M3 attaches the hidden gesture here; nothing in M1)
    'agents.footer.index': '02 — AGENTS',

    // --- added by Task 9: the torque reading's label, the profile's km scale
    'agents.torque.heading': 'Torque delivered against requested',
    'agents.profile.km': '{km} km',

    // --- added in M2: the working picker (agent-picker.mjs), Phase D's blind
    // car, the line shown while Compute stops another computation, and the
    // catalog's third 'scored' value (results/ records a different zip sha)
    'agents.pick.choose': 'Choose…',
    'agents.pick.pair_row': 'Seed {seed} · blind \u2212 sighted {diff}',
    'agents.pick.pair_no_row': 'Seed {seed} · no row for this seed in the results table',
    'agents.pick.pair_refused': 'Seed {seed} · cannot run: {reason}',
    'agents.pick.experiment_refused': '{name} · no pair can run: {reason}',
    'agents.pick.experiment_empty': '{name} · holds no pair',
    'agents.pick.pair_qualifier': '(difference of the medians of 20 episodes, each with its own road and weights; not this episode)',
    'agents.pick.pair_qualifier_same_road': '(difference of the medians of 20 episodes on the same road with different weights; not this episode)',
    'agents.pick.episode_option_same_road': 'Episode {idx} · the same road · weights: torque {w0} / fuel {w1} / component life {w2}',
    'agents.pick.same_road_note': 'The same road ({start} s · {grade} %); the episodes differ only in their weights',
    'agents.pick.need_pair': 'Choose a pair',
    'agents.pick.need_episode': 'Choose an episode',
    'agents.pick.catalog_loading': 'Loading the list of experiments…',
    'agents.pick.catalog_error': 'The list of experiments could not be loaded: {message}',
    'agents.pick.catalog_failed': 'The list of experiments did not load, so nothing can be chosen yet',
    'agents.pick.refused_summary': 'Pairs that cannot run ({n}), and why',
    'agents.pick.refused_pair': '{name} · seed {seed}',
    'agents.car.blind_phase_d': 'Does not see the road ahead, but may have memorised it: the same road in every episode',
    'agents.seen.blind_phase_d': 'Does not see the road ahead: its preview inputs were {zeros}; but it may have memorised it: the same road in every episode ({cite})',
    'agents.load.stopping': 'Stopping the previous computation ({runs} seed {seed} episode {ep})…',
    'agents.verdict.scored_mismatch': 'Not the scored artefact: the final.zip sha differs from the one the results recorded, so this pair cannot run',

    // --- added in M3: the pause panel's empty line (design 7.8), and the models
    // panel behind the footer gesture (model-panel.mjs; design 7.5b, 7.7, 7.9).
    // The honesty lines are design 7.7 word for word; one error sentence per
    // model-panel.mjs ERROR_CODES entry, plus the page's own server_error.
    'agents.pause.empty': 'Press Compute, then pause at any second to see what each agent decided',
    'agents.models.heading': 'Ask a language model about this second',
    'agents.models.not_thesis': 'Not part of the thesis or of any result. No figure here compares the models with the agents, and no difference is computed.',
    'agents.models.claim': "The probabilities are the model's own claim, untested on this task.",
    'agents.models.levels': 'Each model picks one of five levels per action: for the three trims, both limits, "no change" and two midpoints; for the fan and the pump, five evenly spaced duties. What is shown is the model\'s own choice; no average is computed from it.',
    'agents.models.jev.name': 'typesafe.ai · {model}',
    'agents.models.jev.where': 'External service in the USA · each press is one paid call',
    'agents.models.jev.text': "An external service in the USA. It is not part of the thesis or of any result, and no figure compares it with the agents. This page saves nothing, but the vendor's agreement lets it keep what is sent, in perpetuity, to derive telemetry (MCA §4.1). It receives only this simulated episode's state, never the recorded car data. Each press is one paid call. The vendor's agreement forbids training any model to imitate its answers. The vendor's site terms are aimed at US visitors; whether use from Saudi Arabia is permitted is unknown. The vendor says the model is weak at numeric precision.",
    'agents.models.jev.status.configured': 'Key configured ({source})',
    'agents.models.jev.status.no_key': 'No key; nothing will be sent',
    'agents.models.jev.status.page': 'Key from this page, for this session only',
    'agents.models.jev.source.env': 'from the environment variable',
    'agents.models.jev.source.file': 'from a file',
    'agents.models.jev.key.label': 'Paste the jev key',
    'agents.models.jev.key.save': 'Keep for this session',
    'agents.models.jev.key.clear': 'Clear',
    'agents.models.jev.key.note': "Kept in the server's memory until it stops; saved in no file; it never comes back to this page.",
    'agents.models.jev.ask': 'Ask jev about this second (one paid call)',
    'agents.models.jev.latency': '{ms} ms, measured from this machine (vendor claim 70–500 ms)',
    'agents.models.laya.name': 'Laya · {model} · laya {version}',
    'agents.models.laya.where': 'On this machine ({device}) · free, no key',
    'agents.models.laya.device_unknown': 'not loaded yet',
    'agents.models.laya.text': "Runs on this machine and sends nothing out of it. A trial run, not an evaluation. Laya's own file says an example result does not mean it suits engine control (README_AR.md:31). Apache 2.0 licence.",
    'agents.models.laya.check': 'We ask Laya twice, with the options in opposite orders. If its choice changes when only the order changes, that choice does not come from the engine state.',
    'agents.models.laya.status.not_configured': 'Not configured: LAYA_HOME',
    'agents.models.laya.status.not_found': 'Laya was not found at LAYA_HOME, or it lies inside the repository',
    'agents.models.laya.status.stopped': 'Loads on the first question',
    'agents.models.laya.status.starting': 'Loading on this machine for the first time…',
    'agents.models.laya.status.ready': 'Loaded on {device} until the server stops',
    'agents.models.laya.status.failed': 'Could not start: {code}',
    'agents.models.laya.ask': 'Ask Laya about this second (on this machine)',
    'agents.models.laya.latency': '{ms} ms on {device}',
    'agents.models.laya.first_load': 'first load {s} s',
    'agents.models.reason.pause': 'Pause first',
    'agents.models.reason.not_done': 'Wait for the episode to finish',
    'agents.models.reason.stopped': "The sighted car's simulation stopped before this second",
    'agents.models.reason.asking': 'Asking now…',
    'agents.models.ask_this': 'Ask about this second',
    'agents.models.reference': 'The agents applied in this second:',
    'agents.models.choice': "The model's choice: {level} (network {net})",
    'agents.models.chosen_p': 'Probability of the chosen option {p}',
    'agents.models.reversed': 'With the options reversed: {level}',
    'agents.models.held': 'held',
    'agents.models.changed': 'changed with the order',
    'agents.models.footer': 'A one-second target: not applied, not rate-limited',
    'agents.models.sent': 'What was sent',
    'agents.models.no_answer': 'No answer — {code}: {sentence}',
    'agents.models.no_answer_plain': 'No answer — {sentence}',
    'agents.models.error.no_key': 'No key, so nothing was sent.',
    'agents.models.error.network': 'The service could not be reached from this machine.',
    'agents.models.error.timeout': 'The time limit passed with no answer.',
    'agents.models.error.key_rejected': 'The service rejected the key.',
    'agents.models.error.vendor_refused': 'The service refused the request; access from this location may not be permitted.',
    'agents.models.error.request_rejected': "The service rejected the request's shape: a bug on this page.",
    'agents.models.error.rate_limited': 'Too many requests; ask again in a moment.',
    'agents.models.error.overloaded': 'The service is overloaded; ask again in a moment.',
    'agents.models.error.vendor_status': 'The service refused the request (HTTP {status}). This may mean the account has no credit.',
    'agents.models.error.not_configured': 'LAYA_HOME is not set, so nothing was started.',
    'agents.models.error.not_found': "Laya's python or its model folder was not found, or lies inside the repository.",
    'agents.models.error.start_failed': "Laya's worker exited before it was ready.",
    'agents.models.error.start_timeout': "Laya's worker was not ready within 90 s and was stopped.",
    'agents.models.error.worker_error': "Laya's worker reported an error ({kind}).",
    'agents.models.error.worker_died': "Laya's worker stopped in the middle of the request.",
    'agents.models.error.network_attempt': 'The guard counted a network attempt, so the answer was dropped and the worker stopped.',
    'agents.models.error.bad_answer': 'An answer came back that cannot become an action, so nothing is shown.',
    'agents.models.error.foreign_origin': 'The request was refused because it did not come from this page.',
    'agents.models.error.no_trace': 'This episode is no longer held by the server; press Compute, then ask.',
    'agents.models.error.step_not_computed': 'This second was not computed for the sighted car.',
    'agents.models.error.busy': 'Another question to this model is running now.',
    'agents.models.error.bad_key': 'This key could not be used; nothing was kept.',
    'agents.models.error.bad_key_request': 'Invalid request; nothing was kept.',
    'agents.models.error.server_error': 'Server error (HTTP {status})',

    // --- added 30 Sep 2026: an agent whose certificate was RECONSTRUCTED
    // (reconstruct_meta.py, read by app/agent_catalog.py), and the device its
    // committed scores were reproduced on
    'agents.verdict.reconstructed': 'Certificate reconstructed on {date}, not written when training started. Frozen episodes were re-run and equal the committed scores in {file}: {episodes}',
    'agents.device.line_reproduced': 'The committed scores were reproduced on {reproduced} when the certificate was reconstructed. This episode was computed on {device} (torch {torch}, SB3 {sb3})',
    'agents.device.warning_reproduced': 'Warning: this episode was not computed on {reproduced}, so it may not match what was scored',
  },
};

/**
 * Add `extra` ({lang: {key: text}}) into `target` (i18n's STRINGS) and return
 * how many keys each language gained. Everything is checked BEFORE anything is
 * written, so a refused merge leaves `target` exactly as it was. It throws on:
 *  - a language `target` does not have;
 *  - a key present in one language of `extra` and missing from another (or a
 *    language of `target` that `extra` leaves out);
 *  - a key `target` already has: this page may add strings, never change the
 *    lab's.
 */
export function mergeStrings(target, extra) {
  const langs = Object.keys(target);
  for (const lang of Object.keys(extra)) {
    if (!langs.includes(lang)) throw new Error(`agents strings: unknown language "${lang}"`);
  }
  const keys = new Set(Object.values(extra).flatMap(table => Object.keys(table)));
  for (const lang of langs) {
    const table = extra[lang] ?? {};
    for (const key of keys) {
      if (!Object.prototype.hasOwnProperty.call(table, key)) {
        const has = Object.keys(extra).filter(l => Object.prototype.hasOwnProperty.call(extra[l], key));
        throw new Error(`agents strings: "${key}" is missing from ${lang} (present in ${has.join(', ')})`);
      }
      if (Object.prototype.hasOwnProperty.call(target[lang], key)) {
        throw new Error(`agents strings: "${key}" collides with an existing ${lang} string`);
      }
    }
  }
  for (const lang of langs) Object.assign(target[lang], extra[lang]);
  return keys.size;
}

mergeStrings(STRINGS, AGENT_STRINGS);
