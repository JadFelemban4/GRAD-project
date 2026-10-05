// RETIRED-OK: file -- a dated meeting deck (1 October 2026). It quotes the 20 September figures on purpose, beside the current ones.
//
// build_deck.js -- "تحديث المشروع — 1 أكتوبر": what was done since the 20 September deck.
//
//     npm install pptxgenjs@3      (once, in any folder; then run from there)
//     node build_deck.js [output.pptx]
//
// Same design as the 20 September deck (pptxgenjs, 16:9, IBM Plex Sans Arabic, the same
// palette and card/table/stat layouts), with one change, and it is the reason this file is
// longer than a deck needs to be: ARABIC AND NUMBERS GO IN SEPARATE TEXT RUNS.
//
// The 20 September deck wrote every run as lang="en-US" in a left-to-right paragraph, and
// PowerPoint then moved spaces, colons and quote marks around every number ("20سبتمبر",
// "رحلة :B"). Measured on this machine, 1 Oct 2026, through PowerPoint itself:
//   - rtl paragraph + one en-US run     the same glitches;
//   - rtl paragraph + one ar-SA run     the Arabic is right, but every DIGIT is drawn as
//                                       garbage when IBM Plex Sans Arabic is not installed,
//                                       and "ZF 8HP51" splits into "51HP8ZF";
//   - rtl paragraph + split runs        right: Arabic in ar-SA runs, Latin and digits in
//                                       en-US runs (bidi() below). This is what PowerPoint
//                                       itself writes for mixed text.
// After writing, fixDeck() repairs three things pptxgenjs 3.12 writes when a paragraph is
// an ARRAY of runs: it drops rtl="1" (so the paragraph is laid out left-to-right and the
// Arabic words come out in reverse order), and it repeats <a:pPr> before every run, which
// the schema allows once. It also drops the East-Asian font slot and the Chinese charsets
// pptxgenjs puts on the complex-script slot: with them, PowerPoint drew a full stop and
// parentheses beside Arabic as stray Latin glyphs. Keep numbers away from parentheses in
// the text below: a bracket between an Arabic run and a number run has no safe direction.
//
// Every figure is copied from the repository at commit a7ce729: validate.py (run 1 Oct),
// results/premise.json, CLAUDE.md's first box, SESSION_REPORT_2026-09-30_merge.md and
// _merge_review/reports/. Training is deliberately not part of this deck (Jad, 1 Oct).

const fs = require('fs');
const pptxgen = require('pptxgenjs');
const JSZip = require('jszip');                     // ships with pptxgenjs

const OUT = process.argv[2] || 'تحديث المشروع — 1 أكتوبر.pptx';
const F = 'IBM Plex Sans Arabic';

const C = {
  ink: '16202B', bg: 'F2F4F6', white: 'FFFFFF', border: 'D4DCE3', slate: '5D6E7D',
  muted: '8A9AA8', red: 'BD3F2C', blue: '2F6FA8', amber: 'C8841F', amberDk: 'B5741A',
  calloutBg: 'EAF1F7', calloutLn: 'C3D6E6', tableTxt: '3D4C5A', tableLn: 'CCCED0',
  dkCard: '22303F', dkCardLn: '3A4C5C', dkCard2: '1C2A36', dkRed: '2E1F1C', dkRedLn: '6B3A30',
  onDk: 'F2F4F6', onDk2: 'B8C6D4', onDk3: '8FA3B5', blueOnDk: '7FB2DC', salmon: 'E08A78',
};

const X0 = 0.89, CW = 11.55, XR = X0 + CW;          // card grid, as in the 20 Sep deck

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';                        // 13.333 x 7.5 in = 960 x 540 pt
pres.title = 'تحديث المشروع — 1 أكتوبر';
pres.author = 'فريق مشروع التخرج';

// ---------------------------------------------------------------- bidi runs
// Arabic letters (and «») are 'A'; Latin letters, Greek and digits are 'L'; the rest is
// neutral. A neutral stretch between two L characters stays L ("1.05", "103–111",
// "883 °C", "H/τ", "ZF 8HP51"); any other neutral stretch goes to the Arabic run, except
// % and ° touching a number, which stay with it ("43.4%").
const AR = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF«»]/;
const LT = /[A-Za-z0-9\u00C0-\u024F\u0370-\u03FF]/;
const ATTACH = new Set(['%', '°']);
function classify(str) {
  const ch = Array.from(str), n = ch.length;
  const cls = ch.map(c => (AR.test(c) ? 'A' : LT.test(c) ? 'L' : 'N'));
  for (let i = 0; i < n;) {
    if (cls[i] !== 'N') { i++; continue; }
    let j = i;
    while (j + 1 < n && cls[j + 1] === 'N') j++;
    const left = i > 0 ? cls[i - 1] : 'A', right = j < n - 1 ? cls[j + 1] : 'A';
    const both = left === 'L' && right === 'L';
    for (let k = i; k <= j; k++) cls[k] = both ? 'L' : 'A';
    if (!both && left === 'L') for (let k = i; k <= j && ATTACH.has(ch[k]); k++) cls[k] = 'L';
    if (!both && right === 'L') for (let k = j; k >= i && ATTACH.has(ch[k]); k--) cls[k] = 'L';
    i = j + 1;
  }
  const runs = [];
  ch.forEach((c, k) => {
    const last = runs[runs.length - 1];
    if (last && last.c === cls[k]) last.t += c; else runs.push({ c: cls[k], t: c });
  });
  return runs;
}
// Each Latin/number run is also wrapped in LEFT-TO-RIGHT MARKs (U+200E, invisible).
// PowerPoint runs the Unicode bidi algorithm across runs, whatever their `lang`: after an
// Arabic word, "97.0 °C" became an Arabic number followed by a neutral and a Latin C, and
// was drawn "C° 97.0" (seen on slide 5, 1 Oct 2026). The mark makes the nearest strong
// character before the digits Latin, so the run stays one left-to-right unit.
const LRM = '‎';
function bidi(input) {
  const parts = typeof input === 'string' ? [{ text: input, options: {} }] : input;
  const out = [];
  parts.forEach(p => classify(p.text).forEach(r => out.push({
    text: r.c === 'L' ? LRM + r.t + LRM : r.t,
    options: Object.assign({}, p.options || {}, { lang: r.c === 'L' ? 'en-US' : 'ar-SA' }),
  })));
  return out;
}

// ---------------------------------------------------------------- helpers
function T(slide, text, o) {
  slide.addText(bidi(text), Object.assign({
    fontFace: F, rtlMode: true, align: 'right', valign: 'top', margin: 0,
    isTextBox: true, color: C.ink, fontSize: 15, lineSpacingMultiple: 1.2,
  }, o));
}
function kicker(slide, text, color, y = 0.78) {
  T(slide, text, { x: 0.54, y, w: 11.9, h: 0.3, fontSize: 13, bold: true, color });
}
function title(slide, text, color = C.ink, y = 1.10, size = 30) {
  T(slide, text, { x: 0.54, y, w: 11.9, h: 0.62, fontSize: size, bold: true, color, lineSpacingMultiple: 1.0 });
}
function card(slide, x, y, w, h, fill = C.white, line = C.border) {
  const o = { x, y, w, h, fill: { color: fill }, rectRadius: 0.08 };
  o.line = line ? { color: line, width: 0.75 } : { type: 'none' };
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, o);
}
// A table written right-to-left: the first column given is drawn at the RIGHT.
function rtlTable(slide, header, rows, o) {
  const colW = o.colW.slice().reverse();
  const hdr = header.slice().reverse().map(t => ({
    text: bidi(t), options: { bold: true, color: C.white, fill: { color: C.ink }, fontSize: o.hdrSize || 13 } }));
  const body = rows.map((r, i) => r.slice().reverse().map((cell, j) => {
    const c = typeof cell === 'string' ? { text: cell } : cell;
    return { text: bidi(c.text), options: Object.assign({
      fill: { color: i % 2 ? C.bg : C.white }, color: C.tableTxt, fontSize: o.size || 13,
    }, c.o || {}) };
  }));
  slide.addTable([hdr].concat(body), {
    x: o.x, y: o.y, w: colW.reduce((a, b) => a + b, 0), colW,
    fontFace: F, rtlMode: true, align: 'right', valign: 'middle',
    border: { type: 'solid', pt: 0.75, color: C.tableLn }, margin: [0.06, 0.1, 0.06, 0.1],
    rowH: o.rowH, autoPage: false,
  });
}

// ===================================================================== 1. title
{
  const s = pres.addSlide(); s.background = { color: C.ink };
  T(s, 'مشروع التخرّج · جامعة جدة', { x: 0.54, y: 0.89, w: 11.9, h: 0.3, fontSize: 14, color: C.blueOnDk });
  T(s, 'تحديث المشروع', { x: 0.54, y: 3.0, w: 11.9, h: 0.9, fontSize: 52, bold: true, color: C.onDk, lineSpacingMultiple: 1.0 });
  T(s, 'ما حدث منذ عرض 20 سبتمبر', { x: 0.54, y: 4.07, w: 11.9, h: 0.5, fontSize: 22, color: C.onDk2 });
  T(s, '1 أكتوبر 2026', { x: 9.5, y: 6.36, w: 2.95, h: 0.3, fontSize: 13, color: C.muted });
  T(s, 'كل رقم في هذا العرض مكتوب في المستودع، مع السكربت أو التقرير الذي أخرجه', {
    x: 0.89, y: 6.36, w: 6.4, h: 0.3, fontSize: 13, color: C.muted, align: 'left' });
  s.addNotes('افتح بهذي الجملة: «من آخر عرض اشتغلنا على شيئين: خلّينا المحاكاة تأخذ أرقامها من سيارتنا نفسها، ' +
    'ودمجنا شغل الفريق في نسخة واحدة. وخلال الدمج لقينا عيبين في المحاكاة، ونعرف علاج كل واحد.» ' +
    'العرض الماضي كان عن تصحيح المحاكاة؛ هذا العرض عن جعلها تأخذ أرقامها من السيارة نفسها.');
}

// ===================================================================== 2. summary
{
  const s = pres.addSlide(); s.background = { color: C.bg };
  title(s, 'الخلاصة في ثلاثة أسطر', C.ink, 0.89, 34);
  const items = [
    ['صارت ثوابت المحاكاة تُحسب من سجلّات سيارتنا', 'الحرارة، وسقف ضغط الشاحن، والشرارة، والإغناء، ونزول الغيار — يُعاد حسابها كلها مع كل رحلة جديدة'],
    ['سجّلنا رحلة جديدة، ودمجنا عمل الفريق في نسخة واحدة', 'رحلة B: واحد وأربعون تسارعاً كاملاً بغيار ثابت · الدمج: 15 ملفاً متعارضاً، ولا ملف محذوف'],
    ['ووجدنا عيبين في المحاكاة، ونعرف علاج كل واحد', 'حساب حرارة الماء يتذبذب، وثانية «طَرق» مصطنعة عند بداية كل طلعة'],
  ];
  items.forEach(([h, sub], i) => {
    const y = 1.82 + i * 1.46;
    card(s, X0, y, CW, 1.26);
    T(s, h, { x: X0 + 0.3, y: y + 0.27, w: CW - 0.6, h: 0.36, fontSize: 19, bold: true });
    T(s, sub, { x: X0 + 0.3, y: y + 0.68, w: CW - 0.6, h: 0.36, fontSize: 15, color: C.slate });
  });
  s.addNotes('هذي الشريحة هي العرض كله. لو الوقت ضيق تكفي. ' +
    'النقطة الثالثة ليست خبراً سيئاً: نحن من وجد العيبين أثناء مراجعة الدمج، وعلاج كل واحد مكتوب ومتّفق عليه بين جاد وغسان.');
}

// ===================================================================== 3. drive B
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, 'البيانات', C.blue);
  title(s, 'رحلة جديدة: تسارعات كاملة بغيار ثابت');
  T(s, 'لماذا: في رحلاتنا السابقة لم يُطلب من الشاحن ضغطٌ عالٍ على دوران منخفض، فلم تكن المحاكاة تعرف كم يستطيع هناك.', {
    x: X0, y: 1.78, w: CW, h: 0.36, fontSize: 15, color: C.slate });
  const stats = [
    ['41', 'تسارعاً كاملاً', 'بالغيار السادس والسابع والثامن، مثبّتاً يدوياً، في 26.7 دقيقة', C.blue],
    ['1.05 ث', 'لكل قراءة', 'سجّلنا 7 قنوات فقط، فكل قناة تُقرأ مرة كل 1.05 ثانية', C.ink],
    ['321.7', 'دقيقة مسجّلة الآن', 'في 11 رحلة، ثمانٍ منها تحمل عيّنات صالحة — كانت 295.0 دقيقة في 10 رحلات', C.ink],
  ];
  // RTL order: first card on the right
  stats.forEach(([big, h, sub, col], i) => {
    const w = 3.73, gap = (CW - 3 * w) / 2, x = XR - w - i * (w + gap), y = 2.35;
    card(s, x, y, w, 2.2, C.white, C.border);
    T(s, big, { x: x + 0.2, y: y + 0.22, w: w - 0.4, h: 0.6, fontSize: 30, bold: true, color: col, lineSpacingMultiple: 1.0 });
    T(s, h, { x: x + 0.2, y: y + 0.88, w: w - 0.4, h: 0.32, fontSize: 15.5, bold: true });
    T(s, sub, { x: x + 0.2, y: y + 1.24, w: w - 0.4, h: 0.85, fontSize: 13, color: C.slate });
  });
  card(s, X0, 4.85, CW, 1.25, C.calloutBg, C.calloutLn);
  T(s, 'درس دفعنا ثمنه: نسينا قناة حرارة الجو', { x: X0 + 0.3, y: 5.03, w: CW - 0.6, h: 0.34, fontSize: 16, bold: true, color: C.amberDk });
  T(s, 'وكل حساب حرارة في النموذج يحتاجها. عوّضناها بـ 42 °C من رحلاتنا العصرية ووسمنا كل صفّ بأنه مُفترَض — وصارت القناة في كل قائمة رحلة قادمة.', {
    x: X0 + 0.3, y: 5.4, w: CW - 0.6, h: 0.6, fontSize: 14.5 });
  s.addNotes('التسارع الكامل بغيار ثابت: نثبّت الغيار يدوياً (وضع M) وندعس للآخر لثوانٍ ثم نرفع. ' +
    'الهدف نعرف كم ضغط يعطيه الشاحن (التيربو) والمحرك وهو يدور ببطء. ' +
    'القراءة كل 1.05 ثانية أسرع سبع مرات من رحلة 7475b5d7 اللي سجّلت 26 قناة. ' +
    'ولو سأل عن حرارة الجو: الخطأ مسجّل عندنا كدرس رقم 21، والتعويض موسوم في البيانات حتى لا يختلط بالمقيس.');
}

// ===================================================================== 4. derived constants
{
  const s = pres.addSlide(); s.background = { color: C.bg };
  kicker(s, 'من السيارة نفسها', C.blue);
  title(s, 'ثوابت المحاكاة صارت تُشتق من السجلات، لا تُكتب باليد');
  rtlTable(s, ['الثابت', 'قبل', 'الآن'], [
    [{ text: 'حرارة الكتلة والزيت', o: { bold: true, color: C.ink } }, 'أرقام مُفترَضة', 'مُقدَّرة من 7 رحلات تحمل الزيت والماء وحرارة الجو'],
    [{ text: 'سقف ضغط الشاحن', o: { bold: true, color: C.ink } }, 'معادلة مُلاءَمة مرة واحدة في 8 سبتمبر', 'الغلاف المقيس نفسه: أعلى ما وصلته السيارة عند كل تدفّق هواء'],
    [{ text: 'إزاحة الشرارة', o: { bold: true, color: C.ink } }, '26.18 — والخط لم يكن يُستعمل أصلاً', '13.42 — يحدّد الشرارة في 25 من 26 نقطة، بانحياز صفر'],
    [{ text: 'توقيت الإغناء', o: { bold: true, color: C.ink } }, '2 و 9 ثوانٍ، على محور زمن خاطئ', '1.5 و 3.0 ثانية من الطوابع الزمنية · 8 من 9 خلايا ضمن 0.02 من السيارة'],
    [{ text: 'جدول نزول الغيار', o: { bold: true, color: C.ink } }, 'مكتوب باليد', 'يُقاس من المحاكاة نفسها بعد كل تغيير'],
  ], { x: X0, y: 1.85, colW: [2.6, 3.65, 5.3], rowH: [0.46, 0.6, 0.6, 0.6, 0.6, 0.6], size: 13.5 });
  T(s, 'سكربت واحد يعيد حسابها كلها مع كل رحلة جديدة. وما لا يمكن اشتقاقه من هذه السيارة مكتوب مع سببه: حرارة غلاف التوربين، وضغط العادم، وتقسيم المُشعّ.', {
    x: X0, y: 5.45, w: CW, h: 0.6, fontSize: 13.5, color: C.slate });
  s.addNotes('المعنى البسيط: بدل ما نكتب الرقم بيدنا مرة ويبقى، البرنامج يحسبه من بيانات السيارة كل ما جت رحلة جديدة. ' +
    'خط الشرارة كان مكتوب بس المحاكاة ما كانت تستعمله، لأنه كان فوق حدّ الطَّرق في كل النقاط، فكانت الشرارة كلها تجي من نموذج الطَّرق. ' +
    'لو سأل عن سيارات ثانية: نفس الطريقة يمكن تجربتها على أي سيارة نسجّل لها نفس القنوات — لكن ما جرّبناها بعد، فلا نعد بنتيجة.');
}

// ===================================================================== 5. oil node
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, 'الزيت', C.blue);
  title(s, 'خطأ نموذج الزيت كان في شكل المعادلة، لا في أرقامها');
  // right column: what the car showed
  const xr = 6.9, wr = XR - xr;
  card(s, xr, 1.85, wr, 1.15);
  T(s, '11–15 درجة فوق حرارة الماء', { x: xr + 0.25, y: 2.0, w: wr - 0.5, h: 0.36, fontSize: 18, bold: true, color: C.red });
  T(s, 'على دوران 3700–4800 وسرعة 70–100 كم/س — رحلة الطائف', { x: xr + 0.25, y: 2.42, w: wr - 0.5, h: 0.4, fontSize: 13.5, color: C.slate });
  card(s, xr, 3.15, wr, 1.15);
  T(s, '2–3 درجات تحت حرارة الماء', { x: xr + 0.25, y: 3.3, w: wr - 0.5, h: 0.36, fontSize: 18, bold: true, color: C.blue });
  T(s, 'على دوران 2600 وسرعة 130–140 كم/س — سير سريع على طريق مستوٍ', { x: xr + 0.25, y: 3.72, w: wr - 0.5, h: 0.4, fontSize: 13.5, color: C.slate });
  T(s, 'حرارة الزيت تتبع سرعة المحرك، والهواء تحت السيارة يبرّده كلما زادت السرعة. النموذج القديم كان يسخّنه بنسبة ثابتة من الوقود.', {
    x: xr, y: 4.45, w: wr, h: 0.8, fontSize: 14, bold: true });
  // left column: native chart, before/after on the Taif drive
  T(s, 'خطأ النموذج على رحلة الطائف، بالدرجات', { x: X0, y: 1.85, w: 5.7, h: 0.32, fontSize: 14, bold: true });
  s.addChart(pres.charts.BAR, [
    { name: 'قبل', labels: ['الزيت', 'ماء التبريد'], values: [7.55, 5.51] },
    { name: 'بعد', labels: ['الزيت', 'ماء التبريد'], values: [3.57, 2.28] },
  ], {
    x: X0, y: 2.2, w: 5.7, h: 3.0, barDir: 'col', barGrouping: 'clustered', barGapWidthPct: 60,
    chartColors: [C.muted, C.blue], showValue: true, dataLabelPosition: 'outEnd',
    dataLabelFontFace: F, dataLabelFontSize: 13, dataLabelColor: C.ink, dataLabelFormatCode: '0.00',
    catAxisLabelFontFace: F, catAxisLabelFontSize: 13, catAxisLabelColor: C.ink, catAxisOrientation: 'maxMin',
    valAxisHidden: true, valGridLine: { style: 'none' }, catGridLine: { style: 'none' },
    valAxisMinVal: 0, valAxisMaxVal: 9,
    showLegend: true, legendPos: 'b', legendFontFace: F, legendFontSize: 12, legendColor: C.slate,
  });
  card(s, X0, 5.45, CW, 0.95, C.calloutBg, C.calloutLn);
  T(s, 'وما زال ناقصاً: تحت حمل مستمر يقرأ 97.0 °C والسيارة بين 103 و 111، وتبيّن في المراجعة أن الوقود أيضاً يسخّن الزيت. رحلة A هي البيانات التي تحسمه.', {
    x: X0 + 0.3, y: 5.6, w: CW - 0.6, h: 0.65, fontSize: 14 });
  s.addNotes('لو سأل: ليش ما ضبطتوا الأرقام لين يطابق؟ جرّبنا، وكل ضبط كان يحسّن رحلة ويخرّب ثانية. ' +
    'لما يصير كذا، المشكلة في شكل المعادلة مو في أرقامها — وهذا الدرس رقم 20 في سجل أخطائنا. ' +
    'الأرقام: خطأ الزيت نزل من 7.55 إلى 3.57 درجة، ولو حسبنا الثوابت بدون رحلة الطائف يصير 3.90. ' +
    'وثابت زمن الزيت صار 57 ثانية بدل 14 حسب المعادلة، و60 ثانية لما نقيسه بنفس طريقة قياس السيارة (شريحة التحقّق). والمراجعة لقت إن جملة «الوقود ما يسخّن الزيت» غلط: الفرق يزيد 1.5 إلى 2.8 درجة لكل غرام وقود في الثانية، وصحّحناها.');
}

// ===================================================================== 6. physics corrections
{
  const s = pres.addSlide(); s.background = { color: C.bg };
  kicker(s, 'ثلاثة تصحيحات فيزيائية', C.red);
  title(s, 'ثلاثة أخطاء في المعادلات، واثنان منها يلغي أحدهما الآخر');
  rtlTable(s, ['ما هو', 'كان', 'صار', 'أثره على أعلى حرارة'], [
    [{ text: 'تدفّق العادم إلى التوربين', o: { bold: true, color: C.ink } }, 'الوقود × 15', 'الهواء + الوقود (حفظ الكتلة)', { text: 'يرفعها 5.5 درجة', o: { color: C.red, bold: true } }],
    [{ text: 'كثافة الهواء في مقاومة الهواء', o: { bold: true, color: C.ink } }, 'رقم ثابت: 1.2', 'من حرارة الجو: 1.12 عند 42 °C', { text: 'يخفضها 6.2 درجة', o: { color: C.blue, bold: true } }],
    [{ text: 'حرارة مدخل الشاحن عند حساب السقف', o: { bold: true, color: C.ink } }, 'حرارة الشحنة بعد الشاحن', 'حرارة الجو، كما يقول تعريف السقف نفسه', '—'],
  ], { x: X0, y: 1.85, colW: [3.4, 2.45, 3.45, 2.25], rowH: [0.46, 0.62, 0.62, 0.62], size: 14 });
  card(s, X0, 4.45, CW, 1.45, C.calloutBg, C.calloutLn);
  T(s, [
    { text: 'لهذا بقيت أعلى حرارة على صعود الاختبار تقريباً كما هي: 884 ثم 883 °C. ', options: { bold: true } },
    { text: 'ليس لأن شيئاً لم يتغيّر، بل لأن تصحيحين متعاكسين بنفس الحجم تقريباً. أمّا الضرر المحسوب فتغيّر بين 12 و 13%.' },
  ], { x: X0 + 0.3, y: 4.68, w: CW - 0.6, h: 1.0, fontSize: 15.5 });
  s.addNotes('حفظ الكتلة يعني: اللي يطلع من العادم = الهواء الداخل + الوقود. الصيغة القديمة (الوقود × 15) كانت أقل بـ 4.5% في السير العادي، ' +
    'وأكثر بـ 11% لما المحرك يُغنى بالوقود، فكانت تخفي جزءاً من التبريد اللي يعطيه الإغناء. ' +
    'لو لاحظ إن الحرارة القصوى ما تغيّرت — هذي بالضبط النقطة: التشابه صدفة، وقسنا كل تصحيح لحاله.');
}

// ===================================================================== 7. gearbox + spark line
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, 'ناقل الحركة ووحدة التحكّم', C.blue);
  title(s, 'عيبان كانا يغيّران سلوك السيارة في المحاكاة');
  const w = 5.66, y = 1.85, h = 3.25;
  // right card
  const xA = XR - w;
  card(s, xA, y, w, h, C.white, C.border);
  T(s, 'ناقل الحركة لم يكن ينزّل الغيار', { x: xA + 0.28, y: y + 0.25, w: w - 0.56, h: 0.38, fontSize: 18, bold: true });
  T(s, 'بالغيار الثامن عند 130 كم/س يعطي المحرك في المحاكاة 333 نيوتن·متر، والناقل لا ينزّل غياراً إلا فوق 375. فعلى ميل قرابة 9% لم تكن السيارة تستطيع حفظ سرعتها.', {
    x: xA + 0.28, y: y + 0.72, w: w - 0.56, h: 1.2, fontSize: 14, color: C.slate });
  T(s, 'الآن ينزّل غياراً حين لا يكفي المحرك، كما يفعل الأوتوماتيك الحقيقي.', { x: xA + 0.28, y: y + 1.9, w: w - 0.56, h: 0.5, fontSize: 14, bold: true, color: C.blue });
  T(s, 'الثمن، ونكتبه: في هذا المدى يدور المحرك أسرع من السيارة الحقيقية بنحو 600 دورة.', { x: xA + 0.28, y: y + 2.62, w: w - 0.56, h: 0.55, fontSize: 13, color: C.amberDk });
  // left card
  const xB = X0;
  card(s, xB, y, w, h, C.white, C.border);
  T(s, 'خط الشرارة المُلاءَم لم يكن يُستعمل', { x: xB + 0.28, y: y + 0.25, w: w - 0.56, h: 0.38, fontSize: 18, bold: true });
  T(s, 'كان فوق حدّ الطَّرق بـ 9.6 درجة في كل النقاط الـ 26، فكانت الشرارة كلها تأتي من نموذج الطَّرق غير المُتحقَّق منه.', {
    x: xB + 0.28, y: y + 0.72, w: w - 0.56, h: 1.2, fontSize: 14, color: C.slate });
  T(s, 'إزاحة جديدة تُحسب من شرارة السيارة نفسها: الخط يحدّد الشرارة الآن في 25 من 26 نقطة.', { x: xB + 0.28, y: y + 1.9, w: w - 0.56, h: 0.65, fontSize: 14, bold: true, color: C.blue });
  T(s, 'الانحياز صفر، ومتوسط الخطأ 2.5 درجة.', { x: xB + 0.28, y: y + 2.62, w: w - 0.56, h: 0.6, fontSize: 13, color: C.slate });
  card(s, X0, 5.3, CW, 0.85, C.calloutBg, C.calloutLn);
  T(s, [
    { text: 'فحص جديد: 40 طريقاً متنوعاً. ', options: { bold: true } },
    { text: 'وحدة التحكّم الأصلية تقود كلها دون عجز في العزم، و14 منها تتجاوز حدّ الحماية 850 °C.' },
  ], { x: X0 + 0.3, y: 5.5, w: CW - 0.6, h: 0.5, fontSize: 14.5 });
  s.addNotes('نزول الغيار: زي لما تدعس في طلعة والسيارة تنزّل غيار لحالها. المحاكاة ما كانت تسويها، فكانت تطلب من المحرك عزماً ما يقدر عليه. ' +
    'حدّ الطَّرق: أعلى تقديم للشرارة قبل ما يصير الاحتراق غير منتظم. ' +
    'الـ 26 نقطة هي نقاط تشغيل ثابتة من رحلاتنا، بين 30 و 75 كيلوباسكال.');
}

// ===================================================================== 8. validation vs our car
{
  const s = pres.addSlide(); s.background = { color: C.bg };
  kicker(s, 'التحقّق', C.blue);
  title(s, 'قارنّا الزيت والماء بسيارتنا نفسها، لا بنطاقات من الكتب');
  // dark stat card on the right
  const ws = 3.6, xs = XR - ws;
  card(s, xs, 1.85, ws, 2.75, C.ink, null);
  T(s, '8 من 11', { x: xs + 0.25, y: 2.3, w: ws - 0.5, h: 0.8, fontSize: 44, bold: true, color: C.onDk, lineSpacingMultiple: 1.0 });
  T(s, 'كمية داخل نطاقها', { x: xs + 0.25, y: 3.1, w: ws - 0.5, h: 0.35, fontSize: 15, bold: true, color: C.blueOnDk });
  T(s, '6 من 7 ضد المراجع، و 2 من 4 ضد سيارتنا', { x: xs + 0.25, y: 3.5, w: ws - 0.5, h: 0.8, fontSize: 13.5, color: C.onDk3 });
  rtlTable(s, ['الكمية', 'النموذج', 'نطاق سيارتنا', 'الحالة'], [
    ['زيت تحت حمل مستمر (أسخن 10 دقائق في رحلة الطائف)', '97.0 °C', '103–111', { text: 'خارج', o: { color: C.red, bold: true } }],
    ['ثابت زمن الزيت', '60 ث', '70–100 ث', { text: 'خارج', o: { color: C.red, bold: true } }],
    ['ماء التبريد على صعود الاختبار', '93.0 °C', '83.6–95.5', { text: 'داخل', o: { color: C.blue, bold: true } }],
    ['ماء التبريد طوال رحلة الطائف', '92.2 °C', '91.8–94', { text: 'داخل', o: { color: C.blue, bold: true } }],
  ], { x: X0, y: 1.85, colW: [3.95, 1.15, 1.4, 0.95], rowH: [0.45, 0.62, 0.5, 0.5, 0.5], size: 13 });
  card(s, X0, 4.82, CW, 1.5, C.white, C.border);
  T(s, 'ثلاثة من النطاقات الأربعة كانت بلا مصدر؛ الآن تُحسب من رحلاتنا بقاعدة ثابتة قبل المقارنة. الصفّان الخارجان كلاهما الزيت، ورحلة A هي البيانات التي تنقصهما.', {
    x: X0 + 0.3, y: 5.0, w: CW - 0.6, h: 0.75, fontSize: 14.5, bold: true });
  T(s, 'وفحصنا مواصفات الخليج: لا مصدر يثبت تبريداً أقوى، وحتى مشعّ ومروحة أقوى بـ 50% يغيّران حرارة التوربين نصف درجة. والوقود 95 أوكتان، كما يفترض النموذج.', {
    x: X0 + 0.3, y: 5.8, w: CW - 0.6, h: 0.4, fontSize: 13, color: C.slate });
  s.addNotes('8 من 11 هو نفس العدد اللي قلناه قبل، لكن الآن 4 صفوف مقارنة مع سيارتنا الحقيقية — اختبار أصعب وأصدق. ' +
    'ثابت الزمن: كم ثانية يحتاج الزيت عشان يلحق تغيّر الحرارة. ' +
    'والصف السابع (ثابت زمن غلاف التوربين 48 ثانية) ما زال ضد المراجع، لأن السيارة ما فيها حسّاس هناك.');
}

// ===================================================================== 9. knock: untested
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, 'نموذج الطَّرق', C.amberDk);
  title(s, 'نموذج الطَّرق لم يُختبَر بعد — لا أنه فشل');
  T(s, 'قلنا في العرض السابق: لا علاقة بين نموذج الطَّرق وتأخير الشرارة في السيارة. لكن الرحلة التي قارنّا بها سُجّلت بـ 26 قناة، والطَّرق يستمر ثانية أو ثانيتين فقط.', {
    x: X0, y: 1.8, w: CW, h: 0.7, fontSize: 15, color: C.slate });
  const st = [
    ['404 و 410', 'قراءة لزاويتي الشرارة', 'في 55 دقيقة — قراءة كل 8 ثوانٍ تقريباً'],
    ['الثلث', 'من أزواج القراءات', 'قُرئ طرفاه بفارق أكثر من ثانية'],
    ['3–8 درجات', 'أقلّ تقديماً في السيارة', 'شرارة السيارة تحت الضغط العالي أقلّ من نموذجنا — 31 قراءة فقط، لا تكفي للمعايرة'],
  ];
  st.forEach(([big, h, sub], i) => {
    const w = 3.73, gap = (CW - 3 * w) / 2, x = XR - w - i * (w + gap), y = 2.65;
    card(s, x, y, w, 1.95);
    T(s, big, { x: x + 0.2, y: y + 0.2, w: w - 0.4, h: 0.55, fontSize: 26, bold: true, color: i === 2 ? C.red : C.ink, lineSpacingMultiple: 1.0 });
    T(s, h, { x: x + 0.2, y: y + 0.8, w: w - 0.4, h: 0.32, fontSize: 15, bold: true });
    T(s, sub, { x: x + 0.2, y: y + 1.15, w: w - 0.4, h: 0.7, fontSize: 13, color: C.slate });
  });
  card(s, X0, 4.85, CW, 1.3, C.ink, null);
  T(s, 'العلاج: رحلة C', { x: X0 + 0.3, y: 5.02, w: CW - 0.6, h: 0.34, fontSize: 16, bold: true, color: C.blueOnDk });
  T(s, '6 قنوات فقط، فتُقرأ الزاويتان كل 1.25 ثانية تقريباً · غيار ثابت على 2000–3500 دورة · في حرّ العصر · وقاعدة الحكم تُكتب قبل الرحلة.', {
    x: X0 + 0.3, y: 5.42, w: CW - 0.6, h: 0.6, fontSize: 14.5, color: C.onDk });
  s.addNotes('هذا نفس الفخ اللي وقعنا فيه مع حسّاس حرارة الهواء: كان الارتباط 0.35 لما كانت القراءات بطيئة، وصار 0.95 لما سجّلنا 7 قنوات فقط. ' +
    'يعني «ما لقينا علاقة» ما يعني «ما فيه علاقة» — القياس كان أبطأ من الشيء اللي يقيسه. ' +
    'رحلة C ما تكتب شيء في السيارة؛ تسجيل قراءة فقط، والراكب يمسك الجوال والسائق يسوق.');
}

// ===================================================================== 10. two defects (dark)
{
  const s = pres.addSlide(); s.background = { color: C.ink };
  kicker(s, 'تراجُع مُعلَن', C.salmon);
  title(s, 'عيبان في المحاكاة وجدناهما أثناء مراجعة الدمج', C.onDk);
  const w = 5.66, y = 1.9, h = 2.85;
  const xA = XR - w, xB = X0;
  card(s, xA, y, w, h, C.dkCard2, C.blue);
  T(s, 'العيب الأول: حساب حرارة الماء يتذبذب', { x: xA + 0.28, y: y + 0.24, w: w - 0.56, h: 0.36, fontSize: 17, bold: true, color: C.onDk });
  T(s, 'المحاكاة تحسب الحرارة مرة كل ثانية، ومنظّم حرارة الماء في النموذج أسرع من خطوة الحساب. فتقفز الحرارة نحو درجتين في كل خطوة، وعند خطوة ثانيتين تتأرجح بين 85 و 95 °C ولا تستقر.', {
    x: xA + 0.28, y: y + 0.68, w: w - 0.56, h: 1.4, fontSize: 13.5, color: C.onDk2 });
  T(s, 'العلاج: نقسم كل ثانية إلى 10 خطوات صغيرة.', { x: xA + 0.28, y: y + 2.2, w: w - 0.56, h: 0.4, fontSize: 14.5, bold: true, color: C.blueOnDk });
  card(s, xB, y, w, h, C.dkRed, C.dkRedLn);
  T(s, 'العيب الثاني: ثانية «طَرق» مصطنعة عند بداية كل طلعة', { x: xB + 0.28, y: y + 0.24, w: w - 0.56, h: 0.36, fontSize: 17, bold: true, color: C.onDk });
  T(s, 'عند بداية الطلعة المفاجئة تختار وحدة التحكّم الشرارة على ضغط الثانية السابقة، والحمل يقفز في نفس الثانية. ثانية واحدة فيها 58.6 من أصل 60.6 وحدة ضرر طَرق في الرحلة كلها.', {
    x: xB + 0.28, y: y + 0.68, w: w - 0.56, h: 1.4, fontSize: 13.5, color: C.onDk2 });
  T(s, 'العلاج: طلعة تتدرّج خلال 8 ثوانٍ تخفضه إلى 2.4.', { x: xB + 0.28, y: y + 2.2, w: w - 0.56, h: 0.4, fontSize: 14.5, bold: true, color: C.salmon });
  card(s, X0, 5.0, CW, 1.2, C.dkCard, C.dkCardLn);
  T(s, 'ما بطَل معه', { x: X0 + 0.3, y: 5.15, w: CW - 0.6, h: 0.3, fontSize: 13.5, color: C.salmon });
  T(s, '«الاستشراف اليدوي يخسر 0.3 نقطة» — الفرق كله هذه الثانية؛ على ضرر التوربين والزيت وحده السياستان متعادلتان. ولا نقتبس منحنى H/τ حتى نصلح العيب الأول.', {
    x: X0 + 0.3, y: 5.48, w: CW - 0.6, h: 0.65, fontSize: 14.5, color: C.onDk });
  s.addNotes('قلها بثقة لا باعتذار: نحن من وجد العيبين في مراجعة الدمج. ' +
    'مثال الأول: سواق يطالع الطريق مرة كل ثانيتين — يعدّل يمين زيادة ويسار زيادة ويتمايل. لو يطالع كل عُشر ثانية يمشي مستقيم. ' +
    'والثاني ما يصير في السيارة الحقيقية: وحدة التحكّم الحقيقية تختار الشرارة كل دورة محرك، والطريق الحقيقي ما يقفز من مستوٍ إلى 12% في لحظة. ' +
    'الاتفاق بين جاد وغسان: نعالج الاثنين قبل أي قياس جديد.');
}

// ===================================================================== 11. what changed since 20 Sep
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, 'أرقام تغيّرت منذ 20 سبتمبر', C.blue);
  title(s, 'ما قلناه في العرض السابق، وما صار عليه');
  rtlTable(s, ['الرقم', 'في 20 سبتمبر', 'الآن', 'لماذا'], [
    [{ text: 'البيانات المسجّلة', o: { bold: true, color: C.ink } }, '295.0 دقيقة · 10 رحلات', '321.7 دقيقة · 11 رحلة', 'رحلة B'],
    [{ text: 'أعلى حرارة على صعود الاختبار', o: { bold: true, color: C.ink } }, '884 °C', '883 °C', 'تصحيحان متعاكسان'],
    [{ text: 'ما تخفضه الحماية من الضرر', o: { bold: true, color: C.ink } }, '34.0%', '43.4%', 'تدفّق العادم صُحّح'],
    [{ text: 'أعلى حرارة مقدّرة في رحلة 7475b5d7', o: { bold: true, color: C.ink } }, '890.6 °C', '873.1 °C', 'تدفّق العادم صُحّح'],
    [{ text: 'الاستشراف اليدوي مقابل «الميل الحالي»', o: { bold: true, color: C.ink } }, 'ناقص 0.4 نقطة', 'ناقص 0.3 نقطة', 'وكلّه ثانية الطَّرق'],
    [{ text: 'التحقّق', o: { bold: true, color: C.ink } }, '8 من 11', '8 من 11', 'لكن 4 صفوف الآن ضد سيارتنا'],
  ], { x: X0, y: 1.85, colW: [3.75, 2.45, 2.45, 2.9], rowH: [0.45, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5], size: 13.5 });
  T(s, 'نسبة 0.206% — أي 36 ثانية فوق الحدّ — لم نُعِد قياسها بعد على الفيزياء المصحّحة. وكل رقم هنا سيتحرّك مرة أخرى بعد علاج العيبين.', {
    x: X0, y: 5.6, w: CW, h: 0.6, fontSize: 13.5, color: C.slate });
  s.addNotes('قل هذا قبل ما يسأل: الأرقام تغيّرت لأن المحاكاة صارت أدق، وكل تغيير له سبب مكتوب. ' +
    'الدكتور شاف 34% في العرض الماضي، فلازم يعرف ليش صارت 43.4%: الصيغة القديمة للعادم كانت تقلّل ضرر السيارة الأصلية، فكانت النسبة أقل من حقيقتها. ' +
    '«الميل الحالي» سياسة مكتوبة يدوياً تحمي حسب الميل اللي السيارة عليه الآن، بلا نظر للأمام.');
}

// ===================================================================== 12. tools
{
  const s = pres.addSlide(); s.background = { color: C.bg };
  kicker(s, 'أدوات بنيناها', C.blue);
  title(s, 'أدوات تجعل الخطأ يظهر بدل أن يختبئ');
  const cards = [
    ['معمل إعادة الرحلات ثلاثي الأبعاد', 'يعيد رحلاتنا المسجّلة في المتصفح: الغيارات الثمانية، ومنحنيات الحرارة، وقيمة H/τ لحظة بلحظة.',
      'وأثناء بنائه وجدنا خامس قناة في هذه السيارة لا يطابق اسمها ما تقيسه: قناة «الغيار الداخلي» ثابتة على 8، فظهر الغيار الثامن «مقيساً» في 62% من إحدى الرحلات.'],
    ['حارس المستندات', 'سكربت يعيد حساب كل رقم منشور ويقارنه بما في المستندات، ويفشل باسم الملف والسطر.',
      'نظّفنا 187 إشارة قديمة إلى صفر. الآن 73 فحصاً و 837 إشارة رقمية تمرّ كلها، واختباره الذاتي يكشف 16 من 16 خطأً مزروعاً.'],
    ['دمج عمل الفريق', 'فرعا غسان وجاد صارا نسخة واحدة على الفرع الرئيسي.',
      '15 ملفاً متعارضاً و 91 موضعاً، كل قرار مكتوب، ولا ملف محذوف: 454 من 454. القاعدة: فيزياء غسان، وطريقة جاد في التحقّق.'],
  ];
  cards.forEach(([h, a, b], i) => {
    const w = 3.73, gap = (CW - 3 * w) / 2, x = XR - w - i * (w + gap), y = 1.85;
    card(s, x, y, w, 3.35);
    T(s, h, { x: x + 0.22, y: y + 0.24, w: w - 0.44, h: 0.62, fontSize: 16.5, bold: true });
    T(s, a, { x: x + 0.22, y: y + 0.9, w: w - 0.44, h: 1.05, fontSize: 13.5 });
    T(s, b, { x: x + 0.22, y: y + 2.0, w: w - 0.44, h: 1.25, fontSize: 13, color: C.slate });
  });
  T(s, 'والتطبيق الحيّ ومعمل الإعادة جاهزان للعرض لو بقي وقت.', { x: X0, y: 5.5, w: CW, h: 0.35, fontSize: 14, color: C.slate });
  s.addNotes('المعمل جاهز للعرض لو بقي وقت: يعيد رحلة حقيقية بالأبعاد الثلاثة مع الحرارة المقدّرة لحظة بلحظة. ' +
    'وحارس المستندات هو السبب إن كل رقم في هذا العرض له مصدر: لو تغيّر رقم في المحاكاة ونسينا نحدّثه في مستند، يفشل الفحص.');
}

// ===================================================================== 13. next steps
{
  const s = pres.addSlide(); s.background = { color: C.bg };
  kicker(s, 'الخطوة التالية', C.blue);
  title(s, 'نصلح العيبين، ثم نقيس كل شيء من جديد');
  const steps = [
    ['1', 'تقسيم حساب الحرارة', 'عشر خطوات صغيرة داخل كل ثانية، ثم نعيد حساب الثوابت بنفس الطريقة ونعيد كل الفحوصات.'],
    ['2', 'طلعات متدرّجة', 'كل تغيّر في الميل يتدرّج خلال ثوانٍ، كما في الطريق الحقيقي.'],
    ['3', 'رحلة C ثم رحلة A', 'رحلة C للطَّرق: ست قنوات وغيار ثابت. ورحلة A: صعود طويل في الحرّ، ثم خمس دقائق دوران على الوقوف في الأعلى.'],
    ['4', 'تحديث الأرقام والمستندات', 'بعد العلاج نعيد كل الأرقام، ونحدّث المستندات والصفحات مرة واحدة.'],
  ];
  steps.forEach(([n, h, sub], i) => {
    const w = (CW - 0.3) / 2, col = i % 2, row = Math.floor(i / 2);
    const x = XR - w - col * (w + 0.3), y = 1.85 + row * 1.42;
    card(s, x, y, w, 1.25);
    T(s, n, { x: x + w - 0.75, y: y + 0.22, w: 0.5, h: 0.6, fontSize: 30, bold: true, color: C.blue, lineSpacingMultiple: 1.0 });
    T(s, h, { x: x + 0.25, y: y + 0.2, w: w - 1.1, h: 0.36, fontSize: 16.5, bold: true });
    T(s, sub, { x: x + 0.25, y: y + 0.58, w: w - 1.1, h: 0.62, fontSize: 13, color: C.slate });
  });
  card(s, X0, 4.8, CW, 1.45, C.white, C.border);
  T(s, 'وحدود نكتبها في الرسالة بدل أن نخفيها', { x: X0 + 0.3, y: 4.95, w: CW - 0.6, h: 0.32, fontSize: 14.5, bold: true, color: C.amberDk });
  const lim = [
    'الارتفاع غير مُمثَّل: صعود الاختبار يرتفع 2340 م والمحرك يتنفّس هواء مستوى البحر',
    'سعة حرارة غلاف التوربين مُفترَضة لا مقيسة',
    'تقسيم تبريد المُشعّ بين الهواء والمروحة لا يُميَّز من بيانات هذه السيارة',
  ];
  lim.forEach((t, i) => {
    const w = (CW - 0.6 - 0.4) / 3, x = XR - 0.3 - w - i * (w + 0.2);
    T(s, t, { x, y: 5.35, w, h: 0.8, fontSize: 12.5, bold: true, color: C.tableTxt });
  });
  s.addNotes('اختم بهذي: نعرف بالضبط وش العيبين، وعلاجهما مكتوب ومتّفق عليه، وبعدها نعيد القياس كله مرة وحدة. ' +
    'رحلة C قبل A لأن C تحسم سؤال الطَّرق، وA تحسم الزيت. ' +
    'لو سأل عن السيارات الجديدة: طريقة اشتقاق الثوابت من السجلات تقدر تشتغل على أي سيارة نسجّل لها نفس القنوات — لكن لازم نجرّبها قبل ما نعد بنتيجة.');
}

// ---------------------------------------------------------------- after writing
const unesc = t => t.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
  .replace(/&apos;/g, "'").replace(/&amp;/g, '&');
const esc = t => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

async function fixDeck(buf) {
  const zip = await JSZip.loadAsync(buf);
  for (const name of Object.keys(zip.files)) {
    if (!/^ppt\/(slides|charts|notesSlides)\/[^/]+\.xml$/.test(name)) continue;
    let x = await zip.file(name).async('string');
    x = x.replace(/<a:ea typeface="[^"]*" pitchFamily="34" charset="-122"\/>/g, '')
         .replace(/<a:cs typeface="([^"]*)" pitchFamily="34" charset="-120"\/>/g, '<a:cs typeface="$1"/>');
    // one <a:pPr> per paragraph, and rtl="1" on every paragraph that carries Arabic
    x = x.replace(/<a:p>([\s\S]*?)<\/a:p>/g, (m, inner) => {
      let first = true;
      inner = inner.replace(/<a:pPr\b[^>]*?(?:\/>|>[\s\S]*?<\/a:pPr>)/g, pp => {
        if (first) { first = false; return pp; }
        return '';
      });
      if (AR.test(inner)) {
        if (first) inner = '<a:pPr algn="r" rtl="1"/>' + inner;
        else inner = inner.replace(/<a:pPr\b([^>]*?)(\/?>)/, (pp, attrs, close) =>
          '<a:pPr' + (/\brtl="/.test(attrs) ? attrs.replace(/\brtl="\d"/, 'rtl="1"') : attrs + ' rtl="1"') + close);
      }
      return '<a:p>' + inner + '</a:p>';
    });
    if (name.startsWith('ppt/notesSlides/')) {
      // speaker notes: right-to-left, split into runs like the slides
      x = x.replace(/<a:p><a:r><a:rPr lang="en-US" dirty="0"\/><a:t>([^<]*)<\/a:t><\/a:r>/g, (m, t) => {
        if (!AR.test(unesc(t))) return m;
        const runs = classify(unesc(t)).map(r =>
          `<a:r><a:rPr lang="${r.c === 'L' ? 'en-US' : 'ar-SA'}" dirty="0"/><a:t>${esc(r.c === 'L' ? LRM + r.t + LRM : r.t)}</a:t></a:r>`).join('');
        return `<a:p><a:pPr algn="r" rtl="1"/>${runs}`;
      });
    }
    zip.file(name, x);
  }
  return zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' });
}

pres.write({ outputType: 'nodebuffer' })
  .then(fixDeck)
  .then(buf => { fs.writeFileSync(OUT, buf); console.log('wrote', OUT); });
