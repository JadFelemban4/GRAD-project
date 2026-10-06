// Every string the results tab (/results) shows, in Arabic and English.
//
// The lab's i18n.mjs owns t(), applyTranslations() and STRINGS; this file only
// ADDS to STRINGS, once, at import, and refuses to overwrite anything. Its
// merge, mergeInto, keeps the rules of agents-strings.mjs mergeStrings but is
// its own copy: importing agents-strings.mjs would add every /agents string to
// this page. The same three rules as i18n.mjs apply (read its header): both
// languages carry the same keys, numbers go through {placeholders}, and the
// honesty notes are load-bearing text, not copy.
//
// The English lines are the R1a contract's (section 5), word for word; the
// Arabic lines say the same. Rules of this page, pinned by
// results-strings.test.mjs:
//  - no line says that preview helps or that it does not; where a line ever
//    names preview in Arabic, it is «الاستباق», the app's word for it;
//  - the engine computer is always «حاسوب المحرك المنمذَج», the MODELLED one;
//  - "current-grade" stays Latin in Arabic, inside a left-to-right isolate;
//  - none of the words current, stale, outdated, fresh or up to date, nor their
//    Arabic forms, is used: a file's facts are dated, never called recent;
//  - the knock is written with its vowel marks, so it cannot be read as roads;
//  - in an Arabic line every Latin word and every digit is a left-to-right
//    isolate, U+2066 ... U+2069, and so is a {placeholder} that always holds
//    ONE number, hash, commit, date, path, module or protocol. A placeholder
//    that may hold Arabic words or a list ({name}, {other}, {have}, {list},
//    {seeds}) stays bare: the caller isolates each Latin item in it;
//  - thousands take U+202F and a subtraction U+2212.
// The invisible characters are escapes, never the characters: the Write tool
// on this machine decodes a typed escape, so this file is written by a Python
// script and byte-checked.
import { STRINGS } from './i18n.mjs';

export const RESULTS_STRINGS = {
  ar: {
    // --- page, intro, footer and loading
    'results.page.title': 'النتائج — GRAD',
    'results.intro.heading': 'تجارب التقييم، كما تسجّلها ملفاتها',
    'results.intro.note': 'يُقرأ كل ما هنا من \u2066results/\u2069 في كل مرة تُفتح فيها هذه الصفحة. الرقم الوحيد المحسوب هنا هو الأعمى \u2212 المُبصر لكل بذرة، كما تطبعه سكربتات التحليل.',
    'results.intro.agent_sets': 'مجموعات الوكلاء (\u2066results/agents/\u2069، ومنها وكلاء غسان العشرون) ليست في هذه الصفحة بعد؛ تأتي مع المرحلة \u2066R1b\u2069.',
    'results.footer.index': '03 — RESULTS',
    'results.loading': 'جارٍ قراءة ملفات النتائج…',
    'results.error.fetch': 'تعذّرت قراءة النتائج (\u2066{status}\u2069).',

    // --- the build line and the tab-level warnings
    'results.built.line': 'المستودع عند \u2066commit {head}\u2069 · \u2066Python {python}\u2069 · المحاكي \u2066{plant}\u2069',
    'results.built.git_unavailable': 'لا يتوفر \u2066git\u2069 هنا، فلا تُعرض معلومات الـ \u2066commits\u2069.',
    'results.built.restart': 'تغيّرت ملفات المحاكي بعد أن بدأ الخادم: أعد تشغيل الخادم.',
    'results.built.derived_restart': 'تغيّرت الثوابت المشتقة بعد أن بدأ الخادم: أعد تشغيل الخادم.',
    'results.import_failure': 'تعذّر تحميل \u2066{module}\u2069 (\u2066{type}\u2069). كل قسم يحتاج إليه يذكر ذلك.',

    // --- the summary
    'results.summary.heading': 'الملخّص',
    'results.summary.note': 'كل صف تجربة مستقلة، لها محاكيها وطريقها؛ ولا تُدمج الصفوف في نتيجة واحدة.',
    'results.summary.col.experiment': 'التجربة',
    'results.summary.col.plant': 'المحاكي',
    'results.summary.col.verdict': 'الحكم',
    'results.summary.no_verdict': 'لا حكم مسجَّل لهذه التجربة',
    'results.summary.continues': 'تُكمل وكلاء {other}، على الحلقات نفسها',

    // --- a section's head, and a section that cannot be built
    'results.section.no_name': '\u2066{prefix}\u2069 (لا اسم مسجَّل)',
    'results.section.meta': '\u2066{episodes}\u2069 حلقة مجمّدة · جُمّدت في \u2066{frozen}\u2069 · البروتوكول \u2066{protocol}\u2069',
    'results.section.unavailable.missing': 'غير متاح: الملف \u2066{file}\u2069 غير موجود. الأمر الذي ينشئه: \u2066{command}\u2069',
    'results.section.unavailable.read': 'تعذّرت قراءة \u2066{file}\u2069: \u2066{type}\u2069',
    'results.section.unavailable.module': 'يحتاج إلى \u2066{module}\u2069، وتعذّر تحميله.',
    'results.section.unavailable.build': 'تعذّر بناء هذا القسم: \u2066{type}\u2069',

    // --- where the numbers came from (spec 5.2)
    'results.plant.label': 'المحاكي',
    'results.plant.forced': 'قُيِّم الوكلاء رغم اختلاف المحاكي، بتجاوزٍ قسري',
    'results.plant.not_recorded': 'المحاكي غير مسجَّل في هذا الملف',
    'results.plant.another': 'أُجريت على محاكٍ آخر',
    'results.plant.cannot_compare': 'لا يمكن المقارنة',
    'results.plant.same_code': 'شيفرة المحاكي نفسها التي في هذه النسخة؛ الثوابت المشتقة غير مسجَّلة',
    'results.plant.same': 'المحاكي نفسه الذي في هذه النسخة',
    'results.plant.mixed': 'ملفات هذه التجربة لا تتفق؛ التفصيل لكل بذرة أدناه',
    'results.plant.hashes': 'المسجَّل \u2066{recorded}\u2069 · هذه النسخة \u2066{live}\u2069',
    'results.plant.tag': 'محاكي \u2066{tag}\u2069',
    'results.plant.route_git': 'قورن عبر \u2066git\u2069: سُجِّل تحت إصدار آخر من \u2066Python\u2069',
    'results.plant.reason.python': 'سُجِّل تحت \u2066Python {recorded}\u2069؛ وهذا الخادم يعمل بالإصدار \u2066{live}\u2069، ولا يصل \u2066git\u2069 إلى الـ \u2066commit\u2069 المسجَّل',
    'results.plant.reason.no_git_route': 'ملفات المحاكي في الـ \u2066commit\u2069 المسجَّل ليست هي التي حُسبت بصمتها',
    'results.plant.reason.dirty': 'كانت في ملفات المحاكي تغييرات خارج أي \u2066commit\u2069 حين شُغّل التقييم',
    'results.plant.reason.one_sided': 'حقل من البصمة موجود في جهة واحدة فقط',
    'results.plant.reason.restart': 'تغيّرت ملفات المحاكي بعد أن بدأ الخادم؛ أعد تشغيل الخادم',
    'results.plant.reason.protocol': 'بروتوكول هذا الملف غير معروف هنا',
    'results.plant.reason.import': 'تعذّر حساب بصمة هذه النسخة',
    'results.plant.reason.derived_differs': 'الثوابت المشتقة مختلفة',
    'results.plant.reason.derived_restart': 'تغيّرت الثوابت المشتقة بعد أن بدأ الخادم؛ أعد تشغيل الخادم',
    'results.plant.commits': 'شُغّلت من الـ \u2066commits\u2069 {list}',
    'results.plant.committed': 'آخر \u2066commit {commit}\u2069 (\u2066{date}\u2069)',
    'results.plant.changed': 'تغيّر منذ آخر \u2066commit\u2069 له (\u2066{date}\u2069)',
    'results.plant.forced_lines': 'أسطر الملف نفسه:',

    // --- the cross-check of spec 4.4
    'results.check.parse_equals_analysis.pass': 'الوسيطات المقروءة هنا تساوي ما يقرؤه \u2066analyse_phase_d.parse\u2069.',
    'results.check.parse_equals_analysis.fail': 'الوسيطات المقروءة هنا تختلف عمّا يقرؤه \u2066analyse_phase_d.parse\u2069: \u2066{detail}\u2069',
    'results.check.parse_equals_analysis.not_compared': 'لم تُقارَن بما يقرؤه \u2066analyse_phase_d.parse\u2069.',

    // --- the verdict block
    'results.verdict.heading': 'الحكم المسجَّل مسبقاً',
    'results.verdict.none': 'لا حكم مسجَّل لهذه التجربة',
    'results.verdict.unavailable': 'تعذّرت قراءة الحكم هنا.',
    'results.verdict.lines': 'النص كما كُتب، مع ملفه وسطره',

    // --- the required notes (spec 5.4)
    'results.notes.heading': 'لا تُقرأ النتيجة دون ما يلي',
    'results.note.blind_not_blind': 'لم يكن الوكيل الأعمى أعمى تماماً: جاء الصعود في الثانية نفسها في كل حلقة، فأمكن أن تعمل حالته الحرارية كساعة (\u2066results/PREREGISTRATION.md\u2069، القيد \u20667\u2069، وُجد في \u206622\u2069 سبتمبر).',
    'results.note.budget_c1': 'دُرِّب الوكلاء \u206650\u202f000\u2069 خطوة، وهي ميزانية \u2066C1\u2069، كما يسجّلها التسجيل المسبق في \u2066results/PREREGISTRATION.md\u2069 (\u206621\u2069 سبتمبر) وفي \u2066results/PREREGISTRATION_D2.md\u2069 (\u206622\u2069 سبتمبر)؛ ولا تذكرها هذه الملفات.',
    'results.note.budget_from_file': 'دُرِّب الوكلاء \u2066{steps}\u2069 خطوة، كما تسجّله أسطر النموذج في هذه الملفات.',
    'results.note.c4_not_converged': 'لم يستقر تدريب الوكلاء بحسب قاعدة \u2066C4\u2069 نفسها، التي وُضعت في \u206623\u2069 سبتمبر قبل أن يُدرَّب أي وكيل من \u2066C4\u2069 (\u2066results/PREREGISTRATION_C4.md\u2069، \u20665b\u2069؛ \u2066results/C4_RESULT.txt\u2069).',
    'results.note.spark_bound_jad': 'كل وكيل يدفع تعديل توقيت الشرارة إلى الحدّ الأعلى للإجراء، \u2066+4°\u2069 (هذا مقيس). والهامش فوق \u2066current-grade\u2069 مع منع تبكير الشرارة قِيس لـ \u2066C4\u2069 على حلقة واحدة، ولم يُقَس لـ \u2066Phase D\u2069 ولا لـ \u2066D2\u2069 (\u2066SESSION_REPORT_2026-09-30_merge.md\u2069).',
    'results.note.spike_unmeasured': 'في كل حلقة قفزة طَرْق مدّتها خطوة واحدة عند تغيّر الميل المفاجئ؛ ولم يُقَس قطّ هل حرّكت نتيجة هذه التجربة (\u2066conflict.md\u2069، القسم \u20663b\u2069، \u206630\u2069 سبتمبر).',
    'results.note.dt_mismatch': 'دُرِّب الوكلاء بخطوة زمنية \u2066{train_dt}\u2069 ث وقُيِّموا بخطوة \u2066{eval_dt}\u2069 ث، كما تسجّل أسطر الملاحظات في هذه الملفات.',
    'results.note.no_thermal_only': 'لم تسجّل هذه الملفات الضرر دون ضرر الطَّرْق، فلا يُعرف كم من كل فرق يعود إلى ضرر الطَّرْق.',
    'results.note.knock_model': 'الهامش فوق \u2066current-grade\u2069 قائم على نموذج الطَّرْق، الذي لم يُختبر على السيارة (الرحلة \u2066C\u2069؛ \u2066conflict.md\u2069، القسم \u20663a\u2069، \u206630\u2069 سبتمبر).',
    'results.note.turbine_modelled': 'درجات حرارة التيربو منمذَجة لا مقيسة: لا حساس في هذه السيارة يقرؤها، والسعة الحرارية لغلاف التيربو، \u2066c_turb\u2069، مفترَضة؛ وهي التي تحدّد \u2066τ\u2069 (\u2066CLAUDE.md\u2069، \u2066Limits the live app adds\u2069).',
    'results.note.no_other_notes': 'لا ملاحظات أخرى مسجَّلة لهذه التجربة.',

    // --- the figures
    'results.chart.pairs.title': 'الأزواج، بذرةً بذرةً',
    'results.chart.pairs.what': 'لكل بذرة علامتان، الوكيل المُبصر والوكيل الأعمى، يصل بينهما خط. الخط المتقطّع هو وسيط \u2066current-grade\u2069.',
    'results.chart.pairs_thermal.title': 'الأزواج، دون ضرر الطَّرْق',
    'results.chart.thermal_none': 'الضرر دون ضرر الطَّرْق: غير مسجَّل في هذه الملفات.',
    'results.chart.thermal_some': 'دون ضرر الطَّرْق للبذور {seeds} فقط؛ البذور الأخرى لم تسجّله.',
    'results.chart.hand.title': 'مقابل السياسات المكتوبة يدوياً',
    'results.chart.hand.what': 'وسيط ضرر كل وكيل بجانب السياسات الثلاث المكتوبة يدوياً، من الملف نفسه.',
    'results.chart.axis.seed': 'البذرة',
    'results.chart.axis.damage': 'وسيط الضرر عبر الحلقات المجمّدة (وحدات ضرر)',
    'results.chart.axis.damage_thermal': 'وسيط الضرر دون ضرر الطَّرْق (وحدات ضرر)',
    'results.chart.mei': 'القوس المرسوم هو الحد الأدنى المهم للأثر، \u2066{mei}\u2069 وحدة ضرر.',
    'results.chart.mei_after': 'حُدِّد في \u206622\u2069 سبتمبر، بعد هذه النتيجة.',
    'results.chart.unavailable': 'تعذّر رسم هذا الشكل.',
    'results.chart.aria.pairs': 'أزواج {name}',
    'results.chart.aria.hand': '{name} مقابل السياسات المكتوبة يدوياً',

    // --- legend, tooltip and table
    'results.legend.sighted': 'الوكيل المُبصر',
    'results.legend.blind': 'الوكيل الأعمى',
    'results.legend.baseline': 'حاسوب المحرك المنمذَج',
    'results.legend.reactive': 'السياسة التفاعلية',
    'results.legend.current_grade': 'سياسة \u2066current-grade\u2069',
    'results.tip.seed': 'بذرة \u2066{seed}\u2069',
    'results.tip.median': 'الوسيط',
    'results.tip.worst': 'أسوأ حلقة',
    'results.tip.fuel': 'وسيط الوقود (غرام)',
    'results.tip.peak': 'أعلى حرارة للتيربو (°م، منمذَجة)',
    'results.tip.diff': 'الأعمى \u2212 المُبصر',
    'results.table.toggle': 'الأرقام',
    'results.table.seed': 'البذرة',
    'results.table.sighted': 'وسيط المُبصر',
    'results.table.blind': 'وسيط الأعمى',
    'results.table.diff': 'الأعمى \u2212 المُبصر',
    'results.table.sighted_worst': 'أسوأ حلقة للمُبصر',
    'results.table.blind_worst': 'أسوأ حلقة للأعمى',
    'results.table.current_grade': 'وسيط \u2066current-grade\u2069',
    'results.table.baseline': 'وسيط حاسوب المحرك المنمذَج',
    'results.table.reactive': 'وسيط السياسة التفاعلية',
    'results.unpaired': 'البذرة \u2066{seed}\u2069 بلا زوج: في ملفها {have} فقط؛ لم تُرسم.',

    // --- files not read, and the summary's marker
    'results.not_read.heading': 'ملفات لم تُقرأ',
    'results.not_read.reason.name': 'الاسم ليس على صيغة \u2066<prefix>_seed<N>.txt\u2069',
    'results.not_read.reason.header': 'السطر الأول ليس ترويسة من \u2066evaluate.py\u2069',
    'results.not_read.reason.no_fingerprint': 'لا كتلة لبصمة المحاكي',
    'results.not_read.reason.no_table': 'لا جدول للسياسات',
    'results.not_read.reason.duplicate_role': 'أكثر من وكيل واحد للذراع الواحدة',
    'results.not_read.reason.duplicate_seed': 'ملف آخر يحمل البذرة نفسها',
    'results.not_read.reason.unreadable': 'تعذّرت قراءته (\u2066{type}\u2069)',
    'results.markers.continues': 'تكملة',
  },

  en: {
    // --- page, intro, footer and loading
    'results.page.title': 'Results — GRAD',
    'results.intro.heading': 'The evaluation experiments, as their files record them',
    'results.intro.note': 'Read from results/ every time this page opens. The only figure computed here is blind minus sighted per seed, as the analysis scripts print it.',
    'results.intro.agent_sets': "Agent sets (results/agents/, Ghassan's twenty agents among them) are not on this tab yet; they come with milestone R1b.",
    'results.footer.index': '03 — RESULTS',
    'results.loading': 'Reading the result files…',
    'results.error.fetch': 'Could not read the results ({status}).',

    // --- the build line and the tab-level warnings
    'results.built.line': 'Repository at commit {head} · Python {python} · plant {plant}',
    'results.built.git_unavailable': 'git is not available here, so the commit facts are left out.',
    'results.built.restart': 'The plant files changed after the server started: restart the server.',
    'results.built.derived_restart': 'The derived constants changed after the server started: restart the server.',
    'results.import_failure': 'Could not load {module} ({type}). Every section that needs it says so.',

    // --- the summary
    'results.summary.heading': 'Summary',
    'results.summary.note': 'Each row is a separate experiment, on its own plant and road; the rows are not to be counted together.',
    'results.summary.col.experiment': 'Experiment',
    'results.summary.col.plant': 'Plant',
    'results.summary.col.verdict': 'Verdict',
    'results.summary.no_verdict': 'No verdict recorded for this experiment',
    'results.summary.continues': "Continues {other}'s agents, on the same episodes",

    // --- a section's head, and a section that cannot be built
    'results.section.no_name': '{prefix} (no name recorded)',
    'results.section.meta': '{episodes} frozen episodes · frozen {frozen} · protocol {protocol}',
    'results.section.unavailable.missing': 'Not available: {file} is missing. The command that makes it: {command}',
    'results.section.unavailable.read': 'Could not read {file}: {type}',
    'results.section.unavailable.module': 'Needs {module}, which could not be loaded.',
    'results.section.unavailable.build': 'Could not build this section: {type}',

    // --- where the numbers came from (spec 5.2)
    'results.plant.label': 'Plant',
    'results.plant.forced': 'Agents scored with a plant mismatch forced',
    'results.plant.not_recorded': 'Plant not recorded in this file',
    'results.plant.another': 'Made on another plant',
    'results.plant.cannot_compare': 'Cannot compare',
    'results.plant.same_code': 'Same plant code as this tree; derived constants not recorded',
    'results.plant.same': 'Same plant as this tree',
    'results.plant.mixed': 'The files of this experiment do not agree; per seed below',
    'results.plant.hashes': 'recorded {recorded} · this tree {live}',
    'results.plant.tag': 'the plant of {tag}',
    'results.plant.route_git': 'compared through git: recorded under another Python',
    'results.plant.reason.python': 'recorded under Python {recorded}; this server runs {live}, and git cannot reach the recorded commit',
    'results.plant.reason.no_git_route': "the recorded commit's plant files are not the ones that were hashed",
    'results.plant.reason.dirty': 'the plant files had uncommitted changes when it ran',
    'results.plant.reason.one_sided': 'a fingerprint field exists on one side only',
    'results.plant.reason.restart': 'the plant files changed after the server started; restart the server',
    'results.plant.reason.protocol': 'the protocol of this file is not known here',
    'results.plant.reason.import': 'the live fingerprint could not be built',
    'results.plant.reason.derived_differs': 'the derived constants differ',
    'results.plant.reason.derived_restart': 'the derived constants changed after the server started; restart the server',
    'results.plant.commits': 'run from commits {list}',
    'results.plant.committed': 'last commit {commit} ({date})',
    'results.plant.changed': 'changed since its last commit ({date})',
    'results.plant.forced_lines': "The file's own lines:",

    // --- the cross-check of spec 4.4
    'results.check.parse_equals_analysis.pass': "The medians read here equal analyse_phase_d.parse's.",
    'results.check.parse_equals_analysis.fail': "The medians read here differ from analyse_phase_d.parse's: {detail}",
    'results.check.parse_equals_analysis.not_compared': 'Not compared with analyse_phase_d.parse.',

    // --- the verdict block
    'results.verdict.heading': 'The preregistered verdict',
    'results.verdict.none': 'No verdict recorded for this experiment',
    'results.verdict.unavailable': 'The verdict could not be read here.',
    'results.verdict.lines': 'The text as written, with its file and line',

    // --- the required notes (spec 5.4)
    'results.notes.heading': 'Not to be read without',
    'results.note.blind_not_blind': 'The blind agent was not fully blind: the climb came at the same second in every episode, so its thermal state could serve as a clock (results/PREREGISTRATION.md, limit 7, found on 22 September).',
    'results.note.budget_c1': 'Trained for 50 000 steps, the C1 budget, as the preregistrations record it: results/PREREGISTRATION.md (21 September) and results/PREREGISTRATION_D2.md (22 September); these files do not.',
    'results.note.budget_from_file': "Trained for {steps} steps, as these files' model lines record.",
    'results.note.c4_not_converged': "The agents had not converged by C4's own rule, set on 23 September before any C4 agent trained (results/PREREGISTRATION_C4.md, 5b; results/C4_RESULT.txt).",
    'results.note.spark_bound_jad': 'Every agent pushes its spark trim to the +4° action bound (measured). The margin over current-grade with spark advance forbidden was measured for C4 on one episode, and not for Phase D or D2 (SESSION_REPORT_2026-09-30_merge.md).',
    'results.note.spike_unmeasured': "Every episode holds a one-step knock spike at the grade step; whether it moved this experiment's result was never measured (conflict.md, section 3b, 30 September).",
    'results.note.dt_mismatch': "Trained at a {train_dt} s step and scored at {eval_dt} s, as these files' note lines record.",
    'results.note.no_thermal_only': 'Damage without the knock term was not recorded in these files, so how much of each difference is the knock term is unknown.',
    'results.note.knock_model': 'The margin over current-grade rests on the knock model, which has not been tested on the car (drive C; conflict.md, section 3a, 30 September).',
    'results.note.turbine_modelled': "Turbine temperatures are modelled, not measured: no sensor on this car reads them, and the housing's heat capacity, c_turb, is assumed; it sets τ (CLAUDE.md, 'Limits the live app adds').",
    'results.note.no_other_notes': 'No other notes recorded for this experiment.',

    // --- the figures
    'results.chart.pairs.title': 'The pairs, seed by seed',
    'results.chart.pairs.what': "Each seed has two marks, the sighted agent and the blind one, joined by a line. The dashed line is current-grade's median.",
    'results.chart.pairs_thermal.title': 'The pairs, without the knock term',
    'results.chart.thermal_none': 'Damage without the knock term: not recorded in these files.',
    'results.chart.thermal_some': 'Without the knock term only for seeds {seeds}; the others did not record it.',
    'results.chart.hand.title': 'Against the hand-written policies',
    'results.chart.hand.what': "Each agent's median damage beside the three hand-written policies, from the same file.",
    'results.chart.axis.seed': 'Seed',
    'results.chart.axis.damage': 'Median damage over the frozen episodes (damage units)',
    'results.chart.axis.damage_thermal': 'Median damage without the knock term (damage units)',
    'results.chart.mei': 'The bracket is the minimum effect of interest, {mei} damage units.',
    'results.chart.mei_after': 'It was set on 22 September, after this result.',
    'results.chart.unavailable': 'This figure could not be drawn.',
    'results.chart.aria.pairs': 'The pairs of {name}',
    'results.chart.aria.hand': '{name} against the hand-written policies',

    // --- legend, tooltip and table
    'results.legend.sighted': 'Sighted agent',
    'results.legend.blind': 'Blind agent',
    'results.legend.baseline': 'Engine computer (modelled)',
    'results.legend.reactive': 'Reactive',
    'results.legend.current_grade': 'Current-grade',
    'results.tip.seed': 'Seed {seed}',
    'results.tip.median': 'median',
    'results.tip.worst': 'worst episode',
    'results.tip.fuel': 'median fuel (g)',
    'results.tip.peak': 'hottest turbine (°C, modelled)',
    'results.tip.diff': 'blind \u2212 sighted',
    'results.table.toggle': 'The numbers',
    'results.table.seed': 'Seed',
    'results.table.sighted': 'Sighted median',
    'results.table.blind': 'Blind median',
    'results.table.diff': 'Blind \u2212 sighted',
    'results.table.sighted_worst': 'Sighted worst',
    'results.table.blind_worst': 'Blind worst',
    'results.table.current_grade': 'Current-grade median',
    'results.table.baseline': 'Engine computer median',
    'results.table.reactive': 'Reactive median',
    'results.unpaired': 'Seed {seed} has no pair: its file holds only {have}; it is not drawn.',

    // --- files not read, and the summary's marker
    'results.not_read.heading': 'Files not read',
    'results.not_read.reason.name': 'the name is not <prefix>_seed<N>.txt',
    'results.not_read.reason.header': 'the first line is not an evaluate.py header',
    'results.not_read.reason.no_fingerprint': 'no plant fingerprint block',
    'results.not_read.reason.no_table': 'no policy table',
    'results.not_read.reason.duplicate_role': 'more than one agent per arm',
    'results.not_read.reason.duplicate_seed': 'another file names the same seed',
    'results.not_read.reason.unreadable': 'could not be read ({type})',
    'results.markers.continues': 'continues',
  },
};

/**
 * Add `extra` ({lang: {key: text}}) into `target` (i18n's STRINGS) and return
 * how many keys each language gained. Everything is checked BEFORE anything is
 * written, so a refused merge leaves `target` exactly as it was. It throws on:
 *  - a language `target` does not have;
 *  - a key present in one language of `extra` and missing from another (or a
 *    language of `target` that `extra` leaves out);
 *  - a key `target` already has: this tab may add strings, never change the
 *    lab's or another page's. A second copy of this module (an import with
 *    another ?v= query) therefore fails loudly instead of merging twice.
 */
export function mergeInto(target, extra) {
  const langs = Object.keys(target);
  for (const lang of Object.keys(extra)) {
    if (!langs.includes(lang)) throw new Error(`results strings: unknown language "${lang}"`);
  }
  const keys = new Set(Object.values(extra).flatMap(table => Object.keys(table)));
  for (const lang of langs) {
    const table = extra[lang] ?? {};
    for (const key of keys) {
      if (!Object.prototype.hasOwnProperty.call(table, key)) {
        const has = Object.keys(extra).filter(l => Object.prototype.hasOwnProperty.call(extra[l], key));
        throw new Error(`results strings: "${key}" is missing from ${lang} (present in ${has.join(', ')})`);
      }
      if (Object.prototype.hasOwnProperty.call(target[lang], key)) {
        throw new Error(`results strings: "${key}" collides with an existing ${lang} string`);
      }
    }
  }
  for (const lang of langs) Object.assign(target[lang], extra[lang]);
  return keys.size;
}

mergeInto(STRINGS, RESULTS_STRINGS);
