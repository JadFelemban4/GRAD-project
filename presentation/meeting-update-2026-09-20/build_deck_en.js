// RETIRED-OK: file -- a dated meeting deck (20 September 2026, English edition made 1 October). Its figures are those of 20 September, on purpose.
//
// build_deck_en.js -- "Project Update — 20 September", the English edition, dark design.
//
//     npm install pptxgenjs@3      (once, in any folder; then run from there)
//     node build_deck_en.js [output.pptx]
//
// A translation of the Arabic deck of 20 September 2026 ("تحديث المشروع — 20 سبتمبر"),
// slide for slide and note for note. Jad asked on 1 October for an English edition in
// darker colours: every slide is on the dark background, and the light cards, tables and
// callouts of the Arabic deck became dark ones.
//
// THE FIGURES ARE THE 20 SEPTEMBER ONES AND ARE NOT UPDATED HERE. Several have moved since
// (the 1 October update, slide 11, lists them: 884 -> 883 C, 34.0 -> 43.4 %, 890.6 -> 873.1 C,
// 295.0 min / 10 drives -> 321.7 min / 11 drives). The title slide says so, in one line.
//
// Calibri throughout (Consolas for the formula lines): it ships with Office on Windows and
// Mac, so the deck looks the same wherever it is opened.

const fs = require('fs');
const pptxgen = require('pptxgenjs');
const JSZip = require('jszip');

const OUT = process.argv[2] || 'Project Update — 20 September (EN).pptx';
const F = 'Calibri', MONO = 'Consolas';

// ------------------------------------------------------------------ dark palette
const C = {
  bg: '16202B', card: '1C2A36', card2: '22303F', cardLn: '2D3E50', hdr: '2A3B4D',
  text: 'F2F4F6', text2: 'C9D3DD', text3: '93A5B6', muted: '7D8E9E',
  blue: '7FB2DC', blueLn: '2F6FA8', blueFill: '172B3D',
  red: 'E08A78', redLn: '7A4034', redFill: '2B1F1D',
  amber: 'E3A857', amberLn: '6E5427', amberFill: '2A2318',
};
const X0 = 0.89, CW = 11.55, XR = X0 + CW;

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.title = 'Project Update — 20 September';
pres.author = 'Graduation project team';

function T(slide, text, o) {
  slide.addText(text, Object.assign({
    fontFace: F, align: 'left', valign: 'top', margin: 0, isTextBox: true,
    color: C.text, fontSize: 15, lineSpacingMultiple: 1.15,
  }, o));
}
function kicker(slide, text, color = C.blue) {
  T(slide, text, { x: X0, y: 0.78, w: CW, h: 0.3, fontSize: 13, bold: true, color });
}
function title(slide, text, y = 1.08, size = 30) {
  T(slide, text, { x: X0, y, w: CW, h: 0.62, fontSize: size, bold: true, lineSpacingMultiple: 1.0 });
}
function card(slide, x, y, w, h, fill = C.card, line = C.cardLn) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, fill: { color: fill }, rectRadius: 0.08,
    line: line ? { color: line, width: 0.75 } : { type: 'none' },
  });
}
function table(slide, header, rows, o) {
  const hdr = header.map(t => ({ text: t, options: { bold: true, color: C.text, fill: { color: C.hdr }, fontSize: o.hdrSize || 13 } }));
  const body = rows.map((r, i) => r.map(cell => {
    const c = typeof cell === 'string' ? { text: cell } : cell;
    return { text: c.text, options: Object.assign({
      fill: { color: i % 2 ? C.card2 : C.card }, color: C.text2, fontSize: o.size || 13,
    }, c.o || {}) };
  }));
  slide.addTable([hdr].concat(body), {
    x: o.x, y: o.y, w: o.colW.reduce((a, b) => a + b, 0), colW: o.colW,
    fontFace: F, align: 'left', valign: 'middle',
    border: { type: 'solid', pt: 0.75, color: C.cardLn }, margin: [0.06, 0.12, 0.06, 0.12],
    rowH: o.rowH, autoPage: false,
  });
}
function bg(slide) { slide.background = { color: C.bg }; }

// ===================================================================== 1
{
  const s = pres.addSlide(); bg(s);
  T(s, 'Graduation Project · University of Jeddah', { x: X0, y: 0.89, w: CW, h: 0.3, fontSize: 14, color: C.blue });
  T(s, 'Project Update', { x: X0, y: 2.85, w: CW, h: 0.95, fontSize: 52, bold: true, lineSpacingMultiple: 1.0 });
  T(s, 'What happened since our meeting on Sunday, 13 September', { x: X0, y: 3.95, w: CW, h: 0.5, fontSize: 22, color: C.text2 });
  T(s, 'Figures as of 20 September 2026. The 1 October update lists what has changed since.', {
    x: X0, y: 4.6, w: CW, h: 0.32, fontSize: 13, italic: true, color: C.muted });
  T(s, '20 September 2026', { x: X0, y: 6.36, w: 4, h: 0.3, fontSize: 13, color: C.muted });
  T(s, 'Every number in this deck is printed by a script in the repository', {
    x: XR - 7, y: 6.36, w: 7, h: 0.3, fontSize: 13, color: C.muted, align: 'right' });
  s.addNotes('Open with this: "Since our last meeting we audited the simulator and found five defects that voided our earlier numbers. ' +
    'I will show what we found, what we did, and where we are." Do not start with an apology — start with the fact that the audit was our own decision.');
}

// ===================================================================== 2
{
  const s = pres.addSlide(); bg(s);
  title(s, 'The summary in three lines', 0.89, 34);
  [
    ['We audited the simulator and found five defects', 'Our earlier numbers were built on them, so they are void and must not be quoted'],
    ['After the fixes, the test scenario itself turned out to be weak', 'The engine was not loaded enough, so protection had no work to do'],
    ['We tried four remedies — one of them worked', 'The other three gave negative results that are worth publishing'],
  ].forEach(([h, sub], i) => {
    const y = 1.82 + i * 1.46;
    card(s, X0, y, CW, 1.26);
    T(s, h, { x: X0 + 0.3, y: y + 0.27, w: CW - 0.6, h: 0.36, fontSize: 19, bold: true });
    T(s, sub, { x: X0 + 0.3, y: y + 0.68, w: CW - 0.6, h: 0.36, fontSize: 15, color: C.text3 });
  });
  s.addNotes('This slide is the whole talk. If the doctor is short of time, it is enough on its own. ' +
    'The third point matters: negative results are not failure, they are part of the answer.');
}

// ===================================================================== 3
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'The five defects', C.red);
  title(s, 'The simulator was not running five things correctly');
  table(s, ['What', 'What was happening'], [
    [{ text: 'Cooling', o: { bold: true, color: C.text } }, 'Fan off and pump at its minimum — in the baseline car we compare against'],
    [{ text: 'Engine controller', o: { bold: true, color: C.text } }, 'Reads a phantom 224 kPa while the engine is really at 175 — so it retards the spark and heats the engine for no reason'],
    [{ text: 'The comparison test', o: { bold: true, color: C.text } }, 'An arithmetic identity that cannot fail — so it was not measuring anything at all'],
    [{ text: 'Gear selection', o: { bold: true, color: C.text } }, 'Upshifts in the middle of the climb — which no automatic car does'],
    [{ text: 'Gearbox', o: { bold: true, color: C.text } }, 'Six gears with invented ratios — the car has eight (ZF 8HP51)'],
  ], { x: X0, y: 1.95, colW: [2.75, 8.8], rowH: [0.45, 0.5, 0.5, 0.5, 0.5, 0.5], size: 14 });
  T(s, 'Gearbox ratios from Toyota\'s own document, confirmed by the car\'s logs: 86.7% of 79,105 samples fall on one of the eight ratios', {
    x: X0, y: 6.55, w: CW, h: 0.3, fontSize: 13, color: C.text3 });
  s.addNotes('If he asks "how did you confirm the gearbox?" — the answer is the last line: we took the ratio of engine speed to road speed for every sample ' +
    'and compared it with the eight published ratios; 86.7% fall on them. That also rules out the manual gearbox: its top ratio is 2.927, ' +
    'the car measures 1.993, and the automatic\'s is 2.016.');
}

// ===================================================================== 4
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'A declared retraction', C.red);
  title(s, 'The number we were proud of was not a result');
  card(s, X0, 2.05, CW, 2.7, C.card2, C.cardLn);
  T(s, [
    { text: 'We used to say: if we switch preview off, the model falls back to reactive behaviour with ' },
    { text: 'exactly the same number', options: { bold: true } },
    { text: ' — and we took it as our strongest evidence.' },
  ], { x: X0 + 0.35, y: 2.3, w: CW - 0.7, h: 0.8, fontSize: 17, color: C.text2 });
  T(s, 'But it could not have come out any other way.', { x: X0 + 0.35, y: 3.15, w: CW - 0.7, h: 0.45, fontSize: 21, bold: true, color: C.red });
  T(s, 'With preview off, its reading returns zeros, so the predictive policy literally becomes the reactive policy. We were running the same experiment twice and comparing the result with itself.', {
    x: X0 + 0.35, y: 3.75, w: CW - 0.7, h: 0.85, fontSize: 15.5, color: C.text3 });
  const w = (CW - 0.25) / 2;
  card(s, X0, 5.0, w, 1.3, C.blueFill, C.blueLn);
  T(s, 'The lesson', { x: X0 + 0.3, y: 5.2, w: w - 0.6, h: 0.3, fontSize: 13.5, color: C.blue });
  T(s, 'A test that cannot fail cannot confirm', { x: X0 + 0.3, y: 5.54, w: w - 0.6, h: 0.4, fontSize: 16 });
  card(s, X0 + w + 0.25, 5.0, w, 1.3, C.redFill, C.redLn);
  T(s, 'What it voids', { x: X0 + w + 0.55, y: 5.2, w: w - 0.6, h: 0.3, fontSize: 13.5, color: C.red });
  T(s, 'The 13.4-point preview advantage, and every number built on it', { x: X0 + w + 0.55, y: 5.54, w: w - 0.6, h: 0.65, fontSize: 16 });
  s.addNotes('The hardest and most important slide. Say it with confidence, not as an apology: we audited, we found it, and we withdrew the number. ' +
    'If he asks how you found it — a full code audit on 14 September, written up in AUDIT.md, with three critical findings.');
}

// ===================================================================== 5
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'The measurement that changed direction');
  title(s, 'How often does the car actually reach the protection limit?');
  table(s, ['Drive', 'Minutes', 'Peak temperature', 'Seconds over the limit'], [
    ['7475b5d7', '55.1', { text: '890.6 °C', o: { color: C.red, bold: true } }, { text: '36', o: { color: C.red, bold: true } }],
    ['drive10 — Taif', '119.4', '797.6 °C', '0'],
    ['670063b2', '7.3', '780.3 °C', '0'],
    [{ text: 'The other seven drives', o: { color: C.text3 } }, '110.2', '340–728 °C', '0'],
  ], { x: X0, y: 1.85, colW: [2.35, 1.2, 1.85, 2.0], rowH: [0.45, 0.48, 0.48, 0.48, 0.48], size: 13.5 });
  T(s, 'Ten drives · 295.0 minutes logged · protection limit 850 °C · the temperature is our model\'s estimate, because the car has no sensor there', {
    x: X0, y: 4.45, w: 7.4, h: 0.55, fontSize: 12, color: C.text3 });
  const xs = 8.65, ws = XR - xs;
  card(s, xs, 1.85, ws, 2.95, C.card2, C.cardLn);
  T(s, '0.206%', { x: xs + 0.3, y: 2.55, w: ws - 0.6, h: 0.75, fontSize: 46, bold: true, lineSpacingMultiple: 1.0 });
  T(s, '36 seconds out of 292.0 minutes of real driving', { x: xs + 0.3, y: 3.42, w: ws - 0.6, h: 0.7, fontSize: 14.5, color: C.text3 });
  card(s, X0, 5.15, CW, 1.15, C.blueFill, C.blueLn);
  T(s, [
    { text: 'One drive in ten touches the limit — ' },
    { text: 'and that is itself a result for the thesis', options: { bold: true } },
    { text: ': on this car, in this driving, the protected part is near its limit a fifth of one percent of the time. That is exactly the kind of answer the criterion exists to give.' },
  ], { x: X0 + 0.3, y: 5.32, w: CW - 0.6, h: 0.85, fontSize: 15 });
  s.addNotes('The point: we did not fail to find data — we measured, and the measurement is itself an answer. ' +
    'If he asks why you measure a temperature that has no sensor — say that this is the project: a model that estimates what the car does not measure, ' +
    'the same model calibrated on 26 operating points from our logs.');
}

// ===================================================================== 6
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Four attempts');
  title(s, 'We tried four ways to load the engine — one worked');
  const rows = [
    ['A rolling road — repeated up and down', 'Hypothesis: preview gains more the more the road changes', 'Failed — the reverse is true', 'the faster the change, the worse the result', C.red, C.cardLn, C.card],
    ['The published towing standard SAE J2807', 'Hypothesis: a world standard written precisely to load engines', 'Failed', '94 degrees short, even with a two-tonne trailer', C.red, C.cardLn, C.card],
    ['A real trip to Taif — two hours of mountain', 'Hypothesis: a real mountain climb is enough to reach the limit', 'Did not reach the limit', 'but it gave us three things', C.amber, C.cardLn, C.card],
    ['A climb computed from a measured envelope — 12% at 130 km/h', 'Not guessed: we measured eight grade × speed combinations and chose from the table', 'Worked', '34 degrees over the limit', C.blue, C.blueLn, C.blueFill],
  ];
  rows.forEach(([h, sub, out, outSub, col, ln, fill], i) => {
    const y = 1.85 + i * 1.12;
    card(s, X0, y, CW, 0.98, fill, ln);
    T(s, h, { x: X0 + 0.3, y: y + 0.17, w: 7.05, h: 0.36, fontSize: 17, bold: true });
    T(s, sub, { x: X0 + 0.3, y: y + 0.55, w: 7.05, h: 0.32, fontSize: 13.5, color: C.text3 });
    T(s, out, { x: 8.4, y: y + 0.17, w: XR - 8.4 - 0.3, h: 0.36, fontSize: 17, bold: true, color: col });
    T(s, outSub, { x: 8.4, y: y + 0.55, w: XR - 8.4 - 0.3, h: 0.32, fontSize: 13, color: C.text3 });
  });
  s.addNotes('The message: we did not try one thing and get lucky. We tried four; three gave negative results, and all of them are written in the repository ' +
    'with dates and numbers. Each of the three negative results goes into the thesis as a paragraph of its own.');
}

// ===================================================================== 7
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Negative result · 1', C.red);
  title(s, 'The world towing standard did not load the car');
  const wl = 6.05;
  card(s, X0, 1.85, wl, 4.3, C.redFill, C.redLn);
  T(s, 'Why it failed — which matters more than the failure itself', { x: X0 + 0.3, y: 2.05, w: wl - 0.6, h: 0.32, fontSize: 14, bold: true, color: C.red });
  T(s, 'Compare two rows that differ in everything:', { x: X0 + 0.3, y: 2.5, w: wl - 0.6, h: 0.32, fontSize: 15, color: C.text2 });
  T(s, '308 N·m → 756 °C', { x: X0 + 0.3, y: 2.9, w: wl - 0.6, h: 0.34, fontSize: 16, fontFace: MONO });
  T(s, '297 N·m → 812 °C', { x: X0 + 0.3, y: 3.27, w: wl - 0.6, h: 0.34, fontSize: 16, fontFace: MONO });
  T(s, [
    { text: 'Similar torque, 56 degrees apart. ', options: { bold: true } },
    { text: 'The turbine heats with ' },
    { text: 'exhaust flow', options: { bold: true } },
    { text: ', not torque — and the standard is written for trucks climbing slowly, so the engine turns slowly and the flow is small.' },
  ], { x: X0 + 0.3, y: 3.75, w: wl - 0.6, h: 1.1, fontSize: 14.5, color: C.text2 });
  T(s, [
    { text: 'A loaded engine climbing slowly makes a cool turbine. What heats it is ' },
    { text: 'road power', options: { bold: true } },
    { text: ': grade times speed.' },
  ], { x: X0 + 0.3, y: 5.05, w: wl - 0.6, h: 0.85, fontSize: 14, color: C.text3 });
  const xt = X0 + wl + 0.3, wt = XR - xt;
  table(s, ['Trailer weight', 'Peak temperature', 'Short of the limit by'], [
    ['No trailer', '432.4 °C', { text: '418', o: { color: C.text3 } }],
    ['One tonne', '587.0 °C', { text: '263', o: { color: C.text3 } }],
    ['Two tonnes', '756.3 °C', { text: '94', o: { color: C.red, bold: true } }],
  ], { x: xt, y: 1.85, colW: [wt * 0.34, wt * 0.33, wt * 0.33], rowH: [0.45, 0.48, 0.48, 0.48], size: 14 });
  T(s, 'SAE J2807 — the Arizona SR 68 road: 18.3 km, grade 0–7%, minimum speed 64 km/h, ambient 37.8 °C. We read it from the standard itself, not from a summary.', {
    x: xt, y: 4.05, w: wt, h: 0.9, fontSize: 12.5, color: C.text3 });
  s.addNotes('If the doctor asks why you do not use a published standard instead of your own scenario — this slide is the answer. ' +
    'We tried it, it did not load the car, and the reason is physical and written down. It had a second benefit: it taught us that what heats the turbine is road power, ' +
    'and that is what the successful scenario was built on.');
}

// ===================================================================== 8
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Negative result · 2', C.red);
  title(s, 'We drove to Taif and back — and it did not touch the limit');
  const wl = 7.25;
  card(s, X0, 1.85, wl, 1.55, C.blueFill, C.blueLn);
  T(s, 'Altitude proven without a pressure gauge — from the ambient sensor alone', { x: X0 + 0.3, y: 2.02, w: wl - 0.6, h: 0.32, fontSize: 13.5, bold: true, color: C.blue });
  T(s, '31.5 °C → 20.5 °C → 34.5 °C', { x: X0 + 0.3, y: 2.42, w: wl - 0.6, h: 0.4, fontSize: 19, fontFace: MONO });
  T(s, 'sea level · minute 50 at the top · then the descent', { x: X0 + 0.3, y: 2.9, w: wl - 0.6, h: 0.3, fontSize: 13, color: C.text3 });
  card(s, X0, 3.6, wl, 2.0, C.redFill, C.redLn);
  T(s, 'And it was not gentle driving', { x: X0 + 0.3, y: 3.78, w: wl - 0.6, h: 0.32, fontSize: 13.5, bold: true, color: C.red });
  T(s, 'Top speed 167 km/h · 15 seconds above 140 · 5 seconds above 160', { x: X0 + 0.3, y: 4.17, w: wl - 0.6, h: 0.34, fontSize: 15.5 });
  T(s, [
    { text: 'And the hottest moment of the trip was not the climb or the top speed, but ' },
    { text: 'an acceleration at 137 km/h and 5792 rpm', options: { bold: true } },
    { text: ', at minute 13.5' },
  ], { x: X0 + 0.3, y: 4.62, w: wl - 0.6, h: 0.8, fontSize: 14.5, color: C.text2 });
  const xs = X0 + wl + 0.3, ws = XR - xs;
  card(s, xs, 1.85, ws, 3.75, C.card2, C.cardLn);
  T(s, '797.6 °C', { x: xs + 0.3, y: 2.75, w: ws - 0.6, h: 0.8, fontSize: 46, bold: true, lineSpacingMultiple: 1.0 });
  T(s, '52 degrees short of the limit', { x: xs + 0.3, y: 3.65, w: ws - 0.6, h: 0.35, fontSize: 15.5, bold: true, color: C.red });
  T(s, 'zero seconds above the limit in 119.4 minutes', { x: xs + 0.3, y: 4.05, w: ws - 0.6, h: 0.6, fontSize: 14, color: C.text3 });
  card(s, X0, 5.85, CW, 1.05, C.card, C.cardLn);
  T(s, [
    { text: 'The mountain is taken at 60 to 90 km/h, which asks for 40–50 kW. The scenario we locked asks for ' },
    { text: '88.7 kW for twelve continuous minutes', options: { bold: true } },
    { text: '. Altitude does not heat the turbine — sustained power does.' },
  ], { x: X0 + 0.3, y: 6.02, w: CW - 0.6, h: 0.75, fontSize: 14.5, color: C.text2 });
  s.addNotes('If he says you chose an exaggerated scenario — this slide and the next one are the answer. We drove the hardest real road we have, ' +
    'and it is 86 degrees cooler than our scenario. So the scenario is harsher than reality on purpose: a declared design decision, not an accident.');
}

// ===================================================================== 9
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'What that trip bought');
  title(s, 'A trip that did not reach the limit, and gave us three things');
  [
    ['86 K', C.text, 'An answer to the hardest objection', 'Our harshest real climb is cooler than the test scenario by this much — so the scenario is above reality on purpose'],
    ['117 °C', C.amber, 'Oil temperature became checkable', 'The highest we had logged before was 107, below the published range, so we could not judge. Now we know our model is 7 degrees too cool'],
    ['+68%', C.blue, 'More data', 'From 175.5 to 295.0 minutes logged, in a single session'],
  ].forEach(([big, col, h, sub], i) => {
    const w = 3.73, gap = (CW - 3 * w) / 2, x = X0 + i * (w + gap), y = 1.85;
    card(s, x, y, w, 2.4);
    T(s, big, { x: x + 0.25, y: y + 0.24, w: w - 0.5, h: 0.6, fontSize: 30, bold: true, color: col, lineSpacingMultiple: 1.0 });
    T(s, h, { x: x + 0.25, y: y + 0.88, w: w - 0.5, h: 0.32, fontSize: 15.5, bold: true });
    T(s, sub, { x: x + 0.25, y: y + 1.25, w: w - 0.5, h: 1.05, fontSize: 13, color: C.text3 });
  });
  card(s, X0, 4.55, CW, 1.25, C.blueFill, C.blueLn);
  T(s, [
    { text: 'And a sentence we used to write in the thesis became void: ', options: {} },
    { text: '"we have no sustained mountain climb"', options: { color: C.text3 } },
  ], { x: X0 + 0.3, y: 4.72, w: CW - 0.6, h: 0.36, fontSize: 15, color: C.text2 });
  T(s, 'Now we have one — and it does not reach the limit. That is a measurement, not a gap in the data.', {
    x: X0 + 0.3, y: 5.12, w: CW - 0.6, h: 0.4, fontSize: 16.5, bold: true });
  s.addNotes('This slide turns the negative result into a gain. The most important part is the middle column: before Taif, the disagreement between our model ' +
    'and the published range could not be interpreted, because our car never reached that range at all. Now it has, so the disagreement is measured and its direction is known.');
}

// ===================================================================== 10
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'What worked');
  title(s, 'A locked scenario: a 12% grade at 130 km/h');
  card(s, X0, 1.82, 4.0, 1.4, C.card2, C.cardLn);
  T(s, 'Protection finally has work to do', { x: X0 + 0.25, y: 2.0, w: 3.5, h: 0.32, fontSize: 14.5, bold: true, color: C.text2 });
  T(s, 'Before this the engine stayed below the limit, so any protection and any preview were meaningless', {
    x: X0 + 0.25, y: 2.38, w: 3.5, h: 0.75, fontSize: 13, color: C.text3 });
  const ws = 3.6;
  [['34.0%', 'damage cut by protection'], ['884 °C', '34 degrees over the limit']].forEach(([big, sub], i) => {
    const x = X0 + 4.18 + i * (ws + 0.18);
    card(s, x, 1.82, ws, 1.4, C.blueFill, C.blueLn);
    T(s, big, { x: x + 0.25, y: 1.98, w: ws - 0.5, h: 0.6, fontSize: 34, bold: true, lineSpacingMultiple: 1.0 });
    T(s, sub, { x: x + 0.25, y: 2.65, w: ws - 0.5, h: 0.34, fontSize: 15, bold: true, color: C.blue });
  });
  card(s, X0, 3.45, CW, 1.85, C.card2, C.cardLn);
  T(s, 'We did not choose it by intuition — we measured eight combinations and found the boundary near 12% at 120 km/h', {
    x: X0 + 0.3, y: 3.65, w: CW - 0.6, h: 0.34, fontSize: 14.5, bold: true, color: C.blue });
  T(s, [
    { text: 'Different grade, different speed, ' },
    { text: 'same power, so the same temperature', options: { bold: true } },
    { text: '. That is what guided the choice instead of random trial.' },
  ], { x: X0 + 0.3, y: 4.12, w: 5.3, h: 1.0, fontSize: 14, color: C.text2 });
  card(s, X0 + 5.85, 4.1, CW - 6.15, 0.95, C.card, null);
  T(s, '12% @ 130 → 88.7 kW → 899 °C', { x: X0 + 6.1, y: 4.22, w: CW - 6.6, h: 0.32, fontSize: 14, fontFace: MONO });
  T(s, '16% @ 110 → 88.5 kW → 906 °C', { x: X0 + 6.1, y: 4.58, w: CW - 6.6, h: 0.32, fontSize: 14, fontFace: MONO });
  T(s, 'The numbers in the lower box come from the envelope sweep before the real gearbox was added. With the real eight-speed the scenario settled at 884 °C — and it still exceeds the limit.', {
    x: X0, y: 5.55, w: CW, h: 0.6, fontSize: 12.5, color: C.muted });
  s.addNotes('If he asks how you chose 12% and 130 — the answer is in the lower box, a sweep of eight combinations. If he asks about the difference between 899 and 884 — ' +
    'say the real gearbox changed the result slightly and the scenario still exceeds the limit; the last line is on the slide on purpose, so that it does not look as if we are hiding it.');
}

// ===================================================================== 11
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Where we are');
  title(s, 'The foundation is sound, and the original question is still open', 1.08, 28);
  const w = (CW - 0.25) / 2;
  card(s, X0, 1.85, w, 2.95, C.amberFill, C.amberLn);
  T(s, 'Not settled yet', { x: X0 + 0.3, y: 2.05, w: w - 0.6, h: 0.32, fontSize: 14.5, bold: true, color: C.amber });
  T(s, [
    { text: 'With hand-written policies, preview ' },
    { text: 'still loses', options: { bold: true } },
    { text: ': from minus 1.8 points to minus 0.4 points.' },
  ], { x: X0 + 0.3, y: 2.48, w: w - 0.6, h: 0.75, fontSize: 15, color: C.text2 });
  T(s, 'Five scenarios and three policies, and preview loses in all of them — by a margin that changes just by changing the formula of one line inside one of the policies.', {
    x: X0 + 0.3, y: 3.35, w: w - 0.6, h: 1.3, fontSize: 13.5, color: C.text3 });
  const xb = X0 + w + 0.25;
  card(s, xb, 1.85, w, 2.95, C.blueFill, C.blueLn);
  T(s, 'What is settled', { x: xb + 0.3, y: 2.05, w: w - 0.6, h: 0.32, fontSize: 14.5, bold: true, color: C.blue });
  T(s, 'The simulator is corrected of five defects, the gearbox is the real one and checked against the car\'s logs, the scenario really loads the engine, and protection cuts damage by 34%.', {
    x: xb + 0.3, y: 2.48, w: w - 0.6, h: 1.15, fontSize: 15, color: C.text2 });
  T(s, 'And the evaluation protocol is fixed in advance: 20 frozen test cases that do not change after seeing any result.', {
    x: xb + 0.3, y: 3.75, w: w - 0.6, h: 0.9, fontSize: 13.5, color: C.text3 });
  card(s, X0, 5.05, CW, 1.75, C.card2, C.cardLn);
  T(s, 'And that is itself a conclusion, not a stumble', { x: X0 + 0.3, y: 5.22, w: CW - 0.6, h: 0.32, fontSize: 14.5, bold: true, color: C.blue });
  T(s, 'The question "is preview worth acquiring?" cannot be answered by a policy written by hand.', {
    x: X0 + 0.3, y: 5.6, w: CW - 0.6, h: 0.38, fontSize: 17, bold: true });
  T(s, 'A hand-written policy protects all the time at the first sign of danger, so it pays the cost of protection on the easy parts of the road. The learning phase is not one route to the answer — it is the only one.', {
    x: X0 + 0.3, y: 6.05, w: CW - 0.6, h: 0.65, fontSize: 13.5, color: C.text3 });
  s.addNotes('Do not present this slide as bad news. Preview loses with hand-written policies because a hand-written policy is clumsy at using the information, ' +
    'not because the information is worthless. That is exactly what justifies the next phase scientifically. If he asks for a final number for preview — ' +
    'say it is still open, and it will be measured in the next phase with the frozen protocol.');
}

// ===================================================================== 12
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'The next step');
  title(s, 'The same comparison, but in a form that can fail');
  const w = (CW - 0.25) / 2;
  card(s, X0, 1.85, w, 1.75);
  T(s, 'A protocol frozen before the result', { x: X0 + 0.28, y: 2.05, w: w - 0.56, h: 0.34, fontSize: 16.5, bold: true });
  T(s, [
    { text: '20 fixed test cases · five random seeds · the median and the interquartile range · three reference comparisons. ' },
    { text: 'Changing the test after seeing the result is the one unforgivable mistake.', options: { bold: true, color: C.text2 } },
  ], { x: X0 + 0.28, y: 2.45, w: w - 0.56, h: 1.05, fontSize: 13.5, color: C.text3 });
  const xb = X0 + w + 0.25;
  card(s, xb, 1.85, w, 1.75);
  T(s, 'Two trained models, not two written policies', { x: xb + 0.28, y: 2.05, w: w - 0.56, h: 0.34, fontSize: 16.5, bold: true });
  T(s, 'One sees the road ahead and one does not, and both learn with the same budget. Then a tie becomes a result, because a difference was possible.', {
    x: xb + 0.28, y: 2.45, w: w - 0.56, h: 1.05, fontSize: 13.5, color: C.text3 });
  card(s, X0, 3.85, CW, 1.95, C.amberFill, C.amberLn);
  T(s, 'And three limits we will write into the thesis instead of hiding them', { x: X0 + 0.3, y: 4.03, w: CW - 0.6, h: 0.32, fontSize: 14.5, bold: true, color: C.amber });
  const lw = (CW - 0.6 - 0.4) / 3;
  [
    [{ text: 'The time step is not the same', options: { bold: true, color: C.text } }, { text: ' in training and evaluation, and we measured its effect: it moves the numbers by about the size of the signal itself' }],
    [{ text: 'The knock model is not validated', options: { bold: true, color: C.text } }, { text: ' against this car — we compared it with the spark retard the car itself applies, and there is no relationship' }],
    [{ text: 'The turbine\'s heat capacity is assumed', options: { bold: true, color: C.text } }, { text: ', not measured — which is why we sweep it over a 75-fold range, so the claim is about the ratio, not the number' }],
  ].forEach((runs, i) => {
    T(s, runs, { x: X0 + 0.3 + i * (lw + 0.2), y: 4.45, w: lw, h: 1.25, fontSize: 13, color: C.text2 });
  });
  T(s, 'In parallel: the live app runs beside the car with the same calibrated physics, and estimates a temperature the car has no sensor for. Ready to demo.', {
    x: X0, y: 6.05, w: CW, h: 0.6, fontSize: 13.5, color: C.text3 });
  s.addNotes('Close with this: we now know exactly what we are measuring, how we measure it, and what we will say if the result comes out negative. ' +
    'The protocol is frozen before the result on purpose. If there is time left, show the live app — it is the part people can see.');
}

// ------------------------------------------------------------------ write
// pptxgenjs 3.12 repeats <a:pPr> before every run of a multi-run paragraph (the schema
// allows one) and puts Chinese charsets on the East-Asian and complex-script font slots.
async function fixDeck(buf) {
  const zip = await JSZip.loadAsync(buf);
  for (const name of Object.keys(zip.files)) {
    if (!/^ppt\/(slides|charts|notesSlides)\/[^/]+\.xml$/.test(name)) continue;
    let x = await zip.file(name).async('string');
    x = x.replace(/<a:ea typeface="[^"]*" pitchFamily="34" charset="-122"\/>/g, '')
         .replace(/<a:cs typeface="([^"]*)" pitchFamily="34" charset="-120"\/>/g, '<a:cs typeface="$1"/>');
    // keep a number on the same line as its unit: "850 °C" must not break after 850
    x = x.replace(/<a:t>([^<]*)<\/a:t>/g, (m, t) =>
      '<a:t>' + t.replace(/(\d) (°C|kW|km\/h|rpm|N·m|kPa|min|s|K|m)(?![A-Za-z])/g, '$1 $2') + '</a:t>');
    x = x.replace(/<a:p>([\s\S]*?)<\/a:p>/g, (m, inner) => {
      let first = true;
      inner = inner.replace(/<a:pPr\b[^>]*?(?:\/>|>[\s\S]*?<\/a:pPr>)/g, pp => {
        if (first) { first = false; return pp; }
        return '';
      });
      return '<a:p>' + inner + '</a:p>';
    });
    zip.file(name, x);
  }
  return zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' });
}

pres.write({ outputType: 'nodebuffer' })
  .then(fixDeck)
  .then(buf => { fs.writeFileSync(OUT, buf); console.log('wrote', OUT); });
