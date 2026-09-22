// The Arabic / English string layer for the 3D replay lab (/simulation).
//
// No DOM work happens at import time and no physics happens here at all. This
// file owns WHAT the page is allowed to say in each language; main.mjs owns
// WHEN it says it. Keeping the two apart is the same split panel.mjs already
// makes, and it is why this file can be unit tested without a browser.
//
// THREE RULES, and they are not stylistic.
//
// 1. Both languages carry the SAME keys. `missingKeys()` exists so a test can
//    assert that rather than a reader having to notice.
// 2. Anything that interpolates a number or a name uses a {placeholder}, never
//    concatenation at the call site. Arabic and English order the parts
//    differently, and a sentence glued together in main.mjs can only be
//    correct in one of them.
// 3. THE HONESTY CAVEATS ARE LOAD-BEARING TEXT, NOT COPY. The preview ribbon
//    is not a predictive controller, the turbine temperature is a model output
//    whose heat capacity is ASSUMED, the road is decoration that feeds nothing,
//    a gear may be recorded / estimated / unresolved and the page says which
//    and why, and H/tau is a live reading of one recording rather than an
//    experimental result. Every one of those survives in both languages below.
//    Translating one of them away would make the page claim something the
//    project has not measured. Do not soften them to make a line fit.
//
// Keys are FLAT strings. The dots inside them are namespacing for a human
// reader; `t()` does a single property lookup and never walks a path, so
// STRINGS.ar['preview.caption.complete'] is the whole address.

export const LANGS = ['ar', 'en'];
export const DEFAULT_LANG = 'ar';

/** Writing direction per language. The page is Arabic-first, hence rtl first. */
export const DIR = { ar: 'rtl', en: 'ltr' };

export const STRINGS = {
  // ------------------------------------------------------------------ ARABIC
  ar: {
    // --- turbine threshold highlight -------------------------------------
    'limit.badge_near': 'يقترب من العتبة',
    'limit.badge_over': 'عند العتبة أو فوقها',
    'limit.caption': 'العتبة {value} °C — اختارها المشروع، والحرارة تقدير من النموذج لا قراءة حساس.',
    'limit.near_note': 'ضمن {margin} K من العتبة.',
    'limit.heading_note': 'نقطة التشغيل الحالية تستقر عند {steady} °C، أي فوق العتبة لو استمرت.',
    'limit.over_note': 'تجاوز العتبة بـ {over} K.',
    'limit.time_above': 'فوق العتبة {seconds} ث من {total} ث ({percent}٪ من الرحلة).',
    'limit.never': 'لم تبلغ الحرارة المقدّرة العتبة في هذه الرحلة.',
    'limit.legend': 'عتبة التيربو',

    // --- document & chrome
    'page.title': 'مختبر الرحلة — GRAD',
    'brand.aria': 'مختبر GRAD',
    'brand.tagline': 'مختبر الأنظمة الهندسية',
    'nav.aria': 'التنقل الرئيسي',
    'nav.simulation': 'مختبر الرحلة',
    'nav.monitor': 'المراقبة',
    'nav.review': 'مراجعة التنبيهات',
    'readonly.badge': 'قراءة فقط من السيارة',
    'noscript': 'يحتاج المختبر إلى JavaScript لعرض بيانات الرحلة والمشهد ثلاثي الأبعاد.',
    'footer.brand': 'GRAD / ENGINEERING REPLAY LAB',
    'footer.note': 'مشروع تخرّج · محرك B58 · عرض علمي استكشافي',
    'footer.index': '01 — REPLAY',

    // --- page intro and drive picker
    'intro.eyebrow': 'المحرك · الطريق · الزمن',
    'intro.heading': 'كل رحلة، من الداخل',
    'intro.note': 'استكشف حركة السيارة وحالتها الحرارية، لحظة بلحظة.',
    'trip.label': 'الرحلة المسجّلة',
    'trip.loading_option': 'جارٍ قراءة الرحلات…',
    'trip.meta_default': 'بيانات محلية · دون اتصال بالسيارة',
    'trip.option': '{id} — {minutes} دقيقة',
    'trip.meta_separator': ' · ',
    'trip.samples': '{count} عيّنة',
    'trip.build_minutes': 'حساب أولي ~{minutes} دقيقة',
    'trip.build_seconds': 'حساب أولي ~{seconds} ث',
    'trip.gear_channel': 'قناة غيار متاحة',
    'trip.no_gear_channel': 'بلا قناة غيار — تقدير كامل',
    'trip.no_speed_channel': 'بلا قناة سرعة',
    'trip.no_motion': 'السرعة مسجّلة صفرًا طوال التسجيل — السيارة لا تتحرك',
    'trip.oil_estimated': 'حرارة الزيت مقدّرة',

    // --- the world scene
    'layout.aria': 'عرض الرحلة والمؤشرات',
    'scene.mode_badge': 'إعادة تشغيل',
    'scene.terrain_label': 'طريق توضيحي · ليس مسار GPS',
    'scene.world_aria': 'مجسم ثلاثي الأبعاد لسيارة سوبرا على طريق توضيحي، اسحب لتدوير المشهد',
    'scene.label.world': 'المشهد',
    'scene.label.engine': 'مقطع المحرك',
    'scene.webgl_error': 'تعذّر تشغيل {label} ثلاثي الأبعاد في هذا المتصفح. تبقى القراءات والرسوم البيانية أدناه صحيحة.',

    // --- camera tools
    'camera.aria': 'الكاميرا',
    'camera.follow': 'تتبع السيارة',
    'camera.zoom_in': 'تقريب',
    'camera.zoom_out': 'إبعاد',
    'camera.reset': 'إعادة ضبط الكاميرا',

    // --- the decorative road
    'road.level': 'مستوي',
    'road.uphill': '↗ صعود',
    'road.downhill': '↘ نزول',
    'road.decorative': 'شكل توضيحي لا يدخل في الحسابات',
    'road.lap_note': 'الدورة {lap} على حلقة طولها {km} كم',

    // --- preview horizon H and the H/tau card
    'preview.label': 'مدى الاستباق البصري',
    'preview.horizon_aria': 'أفق الاستباق H بالثواني',
    'preview.horizon_option': 'H = {seconds} s',
    'preview.no_controller': 'لا يعني تشغيل متحكم استباقي',
    'preview.caption.no_distance': 'لا مسافة استباق: القناة منقطعة أو السرعة غير مسجّلة.',
    'preview.caption.complete': 'مدى بصري من التسجيل — لا يعني تشغيل متحكم استباقي',
    'preview.caption.partial': 'يغطي {seconds} ث فقط حتى نهاية البيانات — لا يعني تشغيل متحكم استباقي',
    'ratio.tau_label': 'τ التيربو',
    'ratio.h_tau_label': 'H/τ',
    'ratio.caveat': 'τ من النموذج، وسعته الحرارية c_turb مفترَضة لا مقيسة',

    // --- loading card
    'load.title': 'تجهيز مختبر الرحلة',
    'load.detail_boot': 'تحميل محرك العرض…',
    'load.detail_budget_minutes': 'حساب الحالة الحرارية بتوقيت التسجيل الأصلي — يستغرق ~{minutes} دقيقة…',
    'load.detail_budget_seconds': 'حساب الحالة الحرارية بتوقيت التسجيل الأصلي — يستغرق ~{seconds} ثانية…',
    'load.detail_progress': 'حساب الحالة الحرارية… {percent}٪',
    'load.title_busy': 'رحلة أخرى قيد الحساب',
    'load.detail_busy': 'يجري إنهاء الحساب الجاري قبل بدء هذه الرحلة…',
    'load.title_failed': 'تعذّر التحميل',
    'load.detail_no_server': 'الخادم لا يستجيب لطلب قائمة الرحلات.',
    'load.title_failed_compute': 'تعذّر الحساب',
    'load.detail_server_error': 'الخادم ردّ بـ {message}. اختر الرحلة مرة أخرى لإعادة المحاولة.',

    // --- errors
    'error.retry_button': 'إعادة المحاولة',
    'error.catalog': 'تعذّر قراءة قائمة الرحلات: {message}',
    'error.no_recordings': 'لا توجد تسجيلات في logs/raw.',
    'error.trip_prepare': 'تعذّر تحضير الرحلة: {message}',
    'error.unknown_reason': 'سبب غير معروف.',
    'error.unknown_reason_inline': 'سبب غير معروف',
    'error.unexpected': 'خطأ غير متوقع في تشغيل المختبر: {message}',

    // --- telemetry panel
    'telemetry.heading': 'حالة السيارة',
    'sample.waiting': 'بانتظار البيانات',
    'sample.gap': 'فجوة في التسجيل — لا عيّنة',
    'sample.index': 'عيّنة {index} من {total}',
    'metric.speed': 'السرعة',
    'metric.rpm': 'دورات المحرك',

    // --- gearbox
    'gear.header': 'ناقل الحركة',
    'gear.strip_aria': 'الغيارات الأمامية الثمانية',
    'gear.note_default': 'الغيارات المسجّلة أو المقدّرة فقط؛ دون تحكم يدوي.',
    'gear.note.waiting': 'بانتظار عيّنة صالحة.',
    'gear.note.insufficient_data': 'لا توجد سرعة أو دورات كافية لتحديد الغيار.',
    'gear.note.low_speed_or_slip': 'سرعة دون 15 km/h؛ انزلاق المحوّل يمنع الاستدلال من النسبة.',
    'gear.note.low_speed_recording': 'سرعة منخفضة؛ القراءة المسجّلة معروضة دون تحقق من النسبة.',
    'gear.note.ratio_mismatch_or_slip': 'نسبة الدورات إلى السرعة لا تطابق أي غيار ضمن التفاوت؛ غير محسوم.',
    'gear.note.recorded_ratio_checked': 'قراءة قناة الغيار، مطابِقة للنسبة المحسوبة.',
    'gear.note.clipped_channel': 'قناة الغيار متشبّعة عند 6؛ الغيار مقدّر من نسبة الدورات إلى السرعة.',
    'gear.note.rpm_speed_ratio': 'غيار مقدّر من نسبة الدورات إلى السرعة ونسب ZF المنشورة.',
    // {note} is one of the seven above; the ratio error is appended INSIDE the
    // string so each language can put the two parts in its own order.
    'gear.note_with_ratio_error': '{note} فرق النسبة {pct}٪.',
    'shift.marker_title': '{time} · {from} → {to}',

    // --- source labels and dots
    'source.recorded': 'مسجّل',
    'source.estimated': 'مقدّر',
    'source.unavailable': 'غير متاح',
    'dot.recorded_title': 'مسجّلة',
    'dot.estimated_title': 'مقدّرة من النموذج',
    'dot.unavailable_title': 'غير متاحة',
    'legend.recorded': 'مسجّلة',
    'legend.estimated': 'مقدّرة',
    'legend.unavailable': 'غير متاحة',
    'value.unavailable': 'غير متاح',

    // --- engine cut-away and thermal readings
    'engine.heading': 'داخل المحرك',
    'engine.subheading': 'رسم مبسّط',
    'engine.aria': 'رسم ثلاثي الأبعاد مبسط لمحرك بست أسطوانات وتيربو ونظام تبريد',
    'key.block': 'المحرك',
    'key.turbine': 'التيربو',
    'key.coolant': 'التبريد',
    'thermal.turbine': 'غلاف التيربو',
    'thermal.coolant': 'سائل التبريد',
    'thermal.oil': 'الزيت',
    'seed.model_output': 'حرارة التيربو تقدير من النموذج، وليست قراءة حساس.',
    'seed.warming': 'بداية غير محسومة: الحالة الحرارية الابتدائية غير معروفة، وعرض النطاق {band} K. التنبيهات الحرارية موقوفة حتى يضيق.',

    // --- transport
    'transport.aria': 'التحكم في إعادة التشغيل',
    'transport.play': 'تشغيل',
    'transport.play_aria': 'تشغيل الرحلة',
    'transport.pause': 'إيقاف مؤقت',
    'transport.pause_aria': 'إيقاف مؤقت',
    'transport.restart_aria': 'إعادة الرحلة من البداية',
    'transport.seek_aria': 'موضع إعادة تشغيل الرحلة',
    'time.context': 'ساعة العرض مستقلة عن حساب المحاكاة',
    'rate.label': 'سرعة العرض',
    'rate.aria': 'سرعة العرض',

    // --- charts
    'chart.drive.heading': 'إيقاع الرحلة',
    'chart.drive.aria': 'رسم السرعة ودورات المحرك عبر زمن الرحلة',
    'chart.drive.footer': 'نفس العينة، نفس اللحظة',
    'chart.thermal.heading': 'الأثر الحراري',
    'chart.thermal.aria': 'رسم درجات حرارة التيربو والزيت عبر زمن الرحلة',
    'chart.thermal.footer': 'القراءات والتقديرات موضّحة بالمصدر',
    'chart.legend.speed': 'السرعة',
    'chart.legend.rpm': 'RPM',
    'chart.legend.turbine': 'التيربو',
    'chart.legend.oil': 'الزيت',
    'chart.unavailable': 'القناة غير متاحة في هذه الرحلة.',

    // --- operating data
    'operation.heading': 'بيانات التشغيل',
    'operation.grade': 'ميل الطريق الفعلي',
    'operation.fuel': 'تدفق الوقود',
    'operation.torque': 'العزم المقدّر',
    'operation.map': 'ضغط مجمّع السحب',
    'operation.distance': 'المسافة المحسوبة',

    // --- provenance bar
    'provenance.no_comparison': 'لا توجد مقارنة متحكمات معتمدة في هذا العرض.',
    'details.toggle': 'مصادر البيانات وحدود النموذج',

    // --- methodology section
    'method.reading.heading': 'كيف تُقرأ هذه الواجهة؟',
    'method.reading.p1': 'تأتي السرعة وRPM من سجل السيارة. قنوات OBD تُحدَّث في أوقات مختلفة، لذا لا يمثّل كل صف قياسات حساسات متزامنة تمامًا. علامات التبديل تحدد تغيّر الغيار بين عينتين، ولا تدّعي توقيت التعشيق الميكانيكي الدقيق.',
    'method.reading.p2': 'عند صلاحية قناة الغيار نستخدم القراءة. إذا تشبّعت عند السادس نستدل على الغيار من نسبة RPM إلى السرعة ونسب ZF الحالية. عند الانزلاق أو عدم وضوح المطابقة يظهر «غير محسوم». افتراض المحوّل المقفل يخص التقدير، لا يثبت حالة محوّل السيارة.',
    'method.gear_ratios': 'نسب {name}: {ratios}، والتخفيض النهائي {final_drive}. يُقبل الغيار عندما تقع النسبة المقيسة ضمن {tolerance}٪ من نسبة منشورة، وفوق {min_kmh} km/h فقط.',
    'method.scene.heading': 'المشهد والحرارة',
    'method.scene.p1': 'الطريق حلقة توضيحية بمقياس عرض، بلا إحداثيات جغرافية. صعوده ونزوله لا يغيّران الحمل المسجّل ولا درجات الحرارة. مدى الاستباق هو المسافة المحسوبة من السرعات القادمة في التسجيل، ويُقصَر عند نهاية البيانات أو انقطاعها.',
    'method.scene.p2': 'H هو أفق الاستباق المختار، وτ ثابت الزمن الحراري لغلاف التيربو كما يحسبه النموذج عند نقطة التشغيل الحالية. τ ليس رقمًا ثابتًا: مقامه يتضمن تدفق العادم، فيقصر تحت الحمل ويطول عند الثبات. النسبة H/τ معروضة كقراءة لحظية من هذه الرحلة، وليست نتيجة تجربة ولا دليلًا على قيمة الاستباق.',
    'method.scene.p3': 'ألوان التيربو والمحرّك تتبع عقد النموذج الحراري. لون المشعّ والأنابيب يمثل سائل التبريد؛ ليست لهما درجات حرارة معدنية مستقلة. نطاق البداية يبين أثر عدم معرفة الحالة الحرارية الأولية، وليس هامش دقة شاملًا للنموذج.',
    'method.scene.p4': 'الفيزياء تُحسب في Python بتوقيت التسجيل الأصلي. التقديم والتأخير وتسريع العرض تختار من النتائج نفسها. لا اتصال بالسيارة في وضع المختبر ولا حفظ لبيانات الرحلة على القرص.',
    'method.fingerprint.heading': 'بصمة البيانات والحساب',
    'fingerprint.waiting': 'بانتظار حساب الرحلة.',
    'fingerprint.none': 'لا توجد بصمة.',

    // --- appearance and language controls (new with the toggles; nothing in
    //     the shipped page carried these yet)
    'theme.aria': 'مظهر الصفحة',
    'theme.light': 'فاتح',
    'theme.dark': 'داكن',
    'theme.to_dark': 'التبديل إلى الوضع الداكن',
    'theme.to_light': 'التبديل إلى الوضع الفاتح',
    'lang.aria': 'لغة الواجهة',
    'lang.arabic': 'العربية',
    'lang.english': 'English',
    'lang.switch_to_english': 'Switch to English',
    'lang.switch_to_arabic': 'التبديل إلى العربية',
  },

  // ----------------------------------------------------------------- ENGLISH
  en: {
    // --- turbine threshold highlight -------------------------------------
    'limit.badge_near': 'Approaching the threshold',
    'limit.badge_over': 'At or above the threshold',
    'limit.caption': 'Threshold {value} °C — chosen by this project, and the temperature is a model estimate, not a sensor reading.',
    'limit.near_note': 'Within {margin} K of the threshold.',
    'limit.heading_note': 'The current operating point settles at {steady} °C, above the threshold if it is held.',
    'limit.over_note': 'Above the threshold by {over} K.',
    'limit.time_above': 'Above the threshold for {seconds} s of {total} s ({percent}% of the drive).',
    'limit.never': 'The estimated temperature never reached the threshold in this drive.',
    'limit.legend': 'Turbine threshold',

    // --- document & chrome
    'page.title': 'Replay Lab — GRAD',
    'brand.aria': 'GRAD lab',
    'brand.tagline': 'Engineering systems lab',
    'nav.aria': 'Main navigation',
    'nav.simulation': 'Replay lab',
    'nav.monitor': 'Supervisor',
    'nav.review': 'Alert review',
    'readonly.badge': 'Read-only from the vehicle',
    'noscript': 'The lab needs JavaScript to show the drive data and the 3D scene.',
    'footer.brand': 'GRAD / ENGINEERING REPLAY LAB',
    'footer.note': 'Graduation project · B58 engine · exploratory scientific view',
    'footer.index': '01 — REPLAY',

    // --- page intro and drive picker
    'intro.eyebrow': 'Engine · Road · Time',
    'intro.heading': 'Every drive, from the inside',
    'intro.note': "Explore the car's motion and its thermal state, moment by moment.",
    'trip.label': 'Recorded drive',
    'trip.loading_option': 'Reading the drives…',
    'trip.meta_default': 'Local data · no connection to the vehicle',
    'trip.option': '{id} — {minutes} min',
    'trip.meta_separator': ' · ',
    'trip.samples': '{count} samples',
    'trip.build_minutes': 'first computation ~{minutes} min',
    'trip.build_seconds': 'first computation ~{seconds} s',
    'trip.gear_channel': 'gear channel available',
    'trip.no_gear_channel': 'no gear channel — fully inferred',
    'trip.no_speed_channel': 'no road-speed channel',
    'trip.no_motion': 'road speed is recorded as zero throughout — the car does not move',
    'trip.oil_estimated': 'oil temperature estimated',

    // --- the world scene
    'layout.aria': 'Drive view and readings',
    'scene.mode_badge': 'Replay',
    'scene.terrain_label': 'Illustrative road · not a GPS route',
    'scene.world_aria': 'Three-dimensional model of a Supra on an illustrative road; drag to rotate the scene',
    'scene.label.world': 'scene',
    'scene.label.engine': 'engine cut-away',
    'scene.webgl_error': 'The 3D {label} could not run in this browser. The readings and the charts below remain correct.',

    // --- camera tools
    'camera.aria': 'Camera',
    'camera.follow': 'Follow the car',
    'camera.zoom_in': 'Zoom in',
    'camera.zoom_out': 'Zoom out',
    'camera.reset': 'Reset the camera',

    // --- the decorative road
    'road.level': 'Level',
    'road.uphill': '↗ Uphill',
    'road.downhill': '↘ Downhill',
    'road.decorative': 'An illustrative shape; it enters no calculation',
    'road.lap_note': 'Lap {lap} of a loop {km} km long',

    // --- preview horizon H and the H/tau card
    'preview.label': 'Visual preview reach',
    'preview.horizon_aria': 'Preview horizon H, in seconds',
    'preview.horizon_option': 'H = {seconds} s',
    'preview.no_controller': 'does not mean a predictive controller is running',
    'preview.caption.no_distance': 'No preview distance: the channel is broken or road speed was not recorded.',
    'preview.caption.complete': 'A visual reach taken from the recording — does not mean a predictive controller is running',
    'preview.caption.partial': 'Covers only {seconds} s before the data ends — does not mean a predictive controller is running',
    'ratio.tau_label': 'Turbine τ',
    'ratio.h_tau_label': 'H/τ',
    'ratio.caveat': 'τ comes from the model, and its heat capacity c_turb is assumed, not measured',

    // --- loading card
    'load.title': 'Preparing the replay lab',
    'load.detail_boot': 'Loading the render engine…',
    'load.detail_budget_minutes': "Computing the thermal state at the recording's own timestamps — takes ~{minutes} min…",
    'load.detail_budget_seconds': "Computing the thermal state at the recording's own timestamps — takes ~{seconds} s…",
    'load.detail_progress': 'Computing the thermal state… {percent}%',
    'load.title_busy': 'Another drive is being computed',
    'load.detail_busy': 'Finishing the computation already running before starting this drive…',
    'load.title_failed': 'Load failed',
    'load.detail_no_server': 'The server is not answering the request for the list of drives.',
    'load.title_failed_compute': 'Computation failed',
    'load.detail_server_error': 'The server replied {message}. Pick the drive again to retry.',

    // --- errors
    'error.retry_button': 'Try again',
    'error.catalog': 'Could not read the list of drives: {message}',
    'error.no_recordings': 'No recordings in logs/raw.',
    'error.trip_prepare': 'Could not prepare the drive: {message}',
    'error.unknown_reason': 'Unknown reason.',
    'error.unknown_reason_inline': 'unknown reason',
    'error.unexpected': 'Unexpected error starting the lab: {message}',

    // --- telemetry panel
    'telemetry.heading': 'Vehicle state',
    'sample.waiting': 'Waiting for data',
    'sample.gap': 'Gap in the recording — no sample',
    'sample.index': 'Sample {index} of {total}',
    'metric.speed': 'Road speed',
    'metric.rpm': 'Engine speed',

    // --- gearbox
    'gear.header': 'Transmission',
    'gear.strip_aria': 'The eight forward gears',
    'gear.note_default': 'Recorded or inferred gears only; no manual control.',
    'gear.note.waiting': 'Waiting for a valid sample.',
    'gear.note.insufficient_data': 'No sufficient road speed or engine speed to determine the gear.',
    'gear.note.low_speed_or_slip': 'Below 15 km/h; converter slip rules out inference from the ratio.',
    'gear.note.low_speed_recording': 'Low speed; the recorded reading is shown without a ratio check.',
    'gear.note.ratio_mismatch_or_slip': 'The engine-speed to road-speed ratio matches no gear within tolerance; unresolved.',
    'gear.note.recorded_ratio_checked': 'Read from the gear channel, and it agrees with the computed ratio.',
    'gear.note.clipped_channel': 'The gear channel saturates at 6; the gear is inferred from the engine-speed to road-speed ratio.',
    'gear.note.rpm_speed_ratio': 'Gear inferred from the engine-speed to road-speed ratio against the published ZF ratios.',
    'gear.note_with_ratio_error': '{note} Ratio error {pct}%.',
    'shift.marker_title': '{time} · {from} → {to}',

    // --- source labels and dots
    'source.recorded': 'Recorded',
    'source.estimated': 'Estimated',
    'source.unavailable': 'Unavailable',
    'dot.recorded_title': 'Recorded',
    'dot.estimated_title': 'Estimated by the model',
    'dot.unavailable_title': 'Unavailable',
    'legend.recorded': 'Recorded',
    'legend.estimated': 'Estimated',
    'legend.unavailable': 'Unavailable',
    'value.unavailable': 'Unavailable',

    // --- engine cut-away and thermal readings
    'engine.heading': 'Inside the engine',
    'engine.subheading': 'Simplified drawing',
    'engine.aria': 'Simplified three-dimensional drawing of a six-cylinder engine, its turbocharger and its cooling system',
    'key.block': 'Engine',
    'key.turbine': 'Turbo',
    'key.coolant': 'Coolant',
    'thermal.turbine': 'Turbine housing',
    'thermal.coolant': 'Coolant',
    'thermal.oil': 'Oil',
    'seed.model_output': 'The turbine temperature is an estimate from the model, not a sensor reading.',
    'seed.warming': 'Unresolved start: the initial thermal state is not known, and the band is {band} K wide. Thermal alerts stay suppressed until it narrows.',

    // --- transport
    'transport.aria': 'Replay controls',
    'transport.play': 'Play',
    'transport.play_aria': 'Play the drive',
    'transport.pause': 'Pause',
    'transport.pause_aria': 'Pause',
    'transport.restart_aria': 'Restart the drive from the beginning',
    'transport.seek_aria': 'Replay position within the drive',
    'time.context': "The display clock is independent of the simulation's computation",
    'rate.label': 'Playback speed',
    'rate.aria': 'Playback speed',

    // --- charts
    'chart.drive.heading': 'Pace of the drive',
    'chart.drive.aria': 'Plot of road speed and engine speed across the drive',
    'chart.drive.footer': 'Same sample, same instant',
    'chart.thermal.heading': 'Thermal trace',
    'chart.thermal.aria': 'Plot of turbine and oil temperatures across the drive',
    'chart.thermal.footer': 'Readings and estimates are marked with their source',
    'chart.legend.speed': 'Speed',
    'chart.legend.rpm': 'RPM',
    'chart.legend.turbine': 'Turbo',
    'chart.legend.oil': 'Oil',
    'chart.unavailable': 'This channel is not available in this drive.',

    // --- operating data
    'operation.heading': 'Operating data',
    'operation.grade': 'Actual road grade',
    'operation.fuel': 'Fuel flow',
    'operation.torque': 'Estimated torque',
    'operation.map': 'Intake manifold pressure',
    'operation.distance': 'Computed distance',

    // --- provenance bar
    'provenance.no_comparison': 'No validated controller comparison exists in this view.',
    'details.toggle': 'Data sources and model limits',

    // --- methodology section
    'method.reading.heading': 'How is this interface read?',
    'method.reading.p1': "Road speed and RPM come from the car's own log. OBD channels refresh at different times, so a row is not a set of exactly simultaneous sensor readings. The shift marks locate a gear change between two samples; they do not claim the precise instant of mechanical engagement.",
    'method.reading.p2': 'Where the gear channel is valid, its reading is used. Where it saturates at sixth, the gear is inferred from the ratio of RPM to road speed against the ZF ratios in use. Under converter slip, or when the match is not clear, it reads "unresolved". The locked-converter assumption belongs to the inference; it does not establish the state of the car’s own converter.',
    'method.gear_ratios': '{name} ratios: {ratios}, with a {final_drive} final drive. A gear is accepted when the measured ratio falls within {tolerance}% of a published ratio, and only above {min_kmh} km/h.',
    'method.scene.heading': 'The scene and the heat',
    'method.scene.p1': 'The road is an illustrative loop at a display scale, with no geographic coordinates. Its climbs and descents change neither the recorded load nor any temperature. The preview reach is the distance computed from the road speeds that follow in the recording, and it is shortened at the end of the data or at a break in it.',
    'method.scene.p2': 'H is the chosen preview horizon, and τ is the thermal time constant of the turbine housing as the model computes it at the current operating point. τ is not a fixed number: its denominator contains the exhaust flow, so it is short under load and long at steady state. The ratio H/τ is displayed as a live reading of this recording. It is not an experimental result and not evidence that preview is worth anything.',
    'method.scene.p3': "The turbine and engine colours follow the thermal model's nodes. The colour of the radiator and the pipes stands for the coolant; neither has a metal temperature of its own. The start-up band shows the effect of not knowing the initial thermal state; it is not an overall accuracy margin for the model.",
    'method.scene.p4': "The physics is computed in Python at the recording's own timestamps. Seeking and changing the playback speed only select from those same results. In lab mode there is no connection to the vehicle and no drive data is written to disk.",
    'method.fingerprint.heading': 'Data and computation fingerprint',
    'fingerprint.waiting': 'Waiting for the drive to be computed.',
    'fingerprint.none': 'No fingerprint.',

    // --- appearance and language controls
    'theme.aria': 'Page appearance',
    'theme.light': 'Light',
    'theme.dark': 'Dark',
    'theme.to_dark': 'Switch to dark mode',
    'theme.to_light': 'Switch to light mode',
    'lang.aria': 'Interface language',
    'lang.arabic': 'العربية',
    'lang.english': 'English',
    'lang.switch_to_english': 'Switch to English',
    'lang.switch_to_arabic': 'التبديل إلى العربية',
  },
};

const PLACEHOLDER = /\{(\w+)\}/g;

/** The language actually used for a lookup: a known code, or the default. */
export function resolveLang(lang) {
  return Object.prototype.hasOwnProperty.call(STRINGS, lang) ? lang : DEFAULT_LANG;
}

/**
 * One string, with {placeholder} slots filled from `vars`.
 *
 * A key missing from the requested language falls back to the other language
 * rather than to an empty node, because a blank caption on this page reads as
 * "no caveat" and that is the one failure mode worth avoiding. A key missing
 * from BOTH returns the key itself, so the gap is visible on screen instead of
 * silently shipping.
 *
 * A placeholder with no matching var is left as written for the same reason.
 */
export function t(lang, key, vars) {
  const code = resolveLang(lang);
  const table = STRINGS[code];
  const other = STRINGS[code === 'ar' ? 'en' : 'ar'];
  let text = Object.prototype.hasOwnProperty.call(table, key) ? table[key] : undefined;
  if (text === undefined && Object.prototype.hasOwnProperty.call(other, key)) text = other[key];
  if (text === undefined) return key;
  if (!vars) return text;
  return text.replace(PLACEHOLDER, (whole, name) =>
    (Object.prototype.hasOwnProperty.call(vars, name) && vars[name] !== null
      && vars[name] !== undefined ? String(vars[name]) : whole));
}

/** Keys present in one language and missing from the other. A test asserts []. */
export function missingKeys() {
  const out = [];
  for (const [code, table] of Object.entries(STRINGS)) {
    const otherCode = code === 'ar' ? 'en' : 'ar';
    for (const key of Object.keys(table)) {
      if (!Object.prototype.hasOwnProperty.call(STRINGS[otherCode], key)) {
        out.push(`${key} missing from ${otherCode} (present in ${code})`);
      }
    }
  }
  return out.sort();
}

/**
 * Fill every marked element under `root` and set lang/dir on <html>.
 *
 *   data-i18n        -> textContent
 *   data-i18n-aria   -> aria-label
 *   data-i18n-title  -> title
 *   data-i18n-vars   -> optional JSON object of {placeholder} values, applied
 *                       to all three of the above on the same element
 *
 * IMPORTANT for markup: setting textContent REPLACES an element's children, so
 * a label that wraps a source dot, a legend swatch or the horizon <select>
 * must carry data-i18n on an inner text-only <span>, never on the element that
 * holds the icon. Losing a .source-dot to a translation would erase the
 * measured-versus-estimated distinction, which is the one thing this page is
 * not allowed to blur.
 *
 * Returns the number of nodes it touched, which is what a smoke test asserts.
 */
export function applyTranslations(root, lang) {
  const scope = root && typeof root.querySelectorAll === 'function'
    ? root
    : (typeof document === 'undefined' ? null : document);
  if (!scope) return 0;
  const code = resolveLang(lang);

  const doc = scope.ownerDocument || (scope.documentElement ? scope : null);
  const html = doc && doc.documentElement;
  if (html) {
    html.setAttribute('lang', code);
    html.setAttribute('dir', DIR[code] || 'ltr');
  }

  const readVars = el => {
    const raw = el.getAttribute('data-i18n-vars');
    if (!raw) return undefined;
    // Private mode is not the risk here; a hand-edited attribute is. A bad
    // JSON blob must not stop the rest of the page translating.
    try { return JSON.parse(raw); } catch { return undefined; }
  };

  const FIELDS = [
    ['data-i18n', (el, text) => { if (el.textContent !== text) el.textContent = text; }],
    ['data-i18n-aria', (el, text) => el.setAttribute('aria-label', text)],
    ['data-i18n-title', (el, text) => el.setAttribute('title', text)],
  ];

  let touched = 0;
  for (const [attr, apply] of FIELDS) {
    const nodes = [...scope.querySelectorAll(`[${attr}]`)];
    // querySelectorAll skips the root itself, and the root is a legitimate
    // place to put a marker when a caller translates one panel.
    if (typeof scope.hasAttribute === 'function' && scope.hasAttribute(attr)) nodes.unshift(scope);
    for (const el of nodes) {
      const key = el.getAttribute(attr);
      if (!key) continue;
      apply(el, t(code, key, readVars(el)));
      touched += 1;
    }
  }
  return touched;
}
