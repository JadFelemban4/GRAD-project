// RETIRED-OK: file -- a dated meeting deck (1 October 2026). It quotes the 20 September figures on purpose, beside the current ones.
//
// build_deck_en.js -- "Project Update — 1 October", the English edition, dark design.
//
//     npm install pptxgenjs@3      (once, in any folder; then run from there)
//     node build_deck_en.js [output.pptx]
//
// A translation of build_deck.js beside it (the Arabic deck), slide for slide and note
// for note, in the dark design Jad asked for on 1 October: every slide on the dark
// background, the light cards, tables and callouts turned into dark ones. Training is
// deliberately not part of this deck, as in the Arabic one. The figures and their
// sources are the Arabic deck's: validate.py (run 1 Oct), results/premise.json,
// CLAUDE.md's first box, SESSION_REPORT_2026-09-30_merge.md and _merge_review/reports/.

const fs = require('fs');
const pptxgen = require('pptxgenjs');
const JSZip = require('jszip');

const OUT = process.argv[2] || 'Project Update — 1 October (EN).pptx';
const F = 'Calibri';

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
pres.title = 'Project Update — 1 October';
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
const B = { bold: true, color: C.text };          // a bold, bright label cell

// ===================================================================== 1. title
{
  const s = pres.addSlide(); bg(s);
  T(s, 'Graduation Project · University of Jeddah', { x: X0, y: 0.89, w: CW, h: 0.3, fontSize: 14, color: C.blue });
  T(s, 'Project Update', { x: X0, y: 2.85, w: CW, h: 0.95, fontSize: 52, bold: true, lineSpacingMultiple: 1.0 });
  T(s, 'What happened since the 20 September update', { x: X0, y: 3.95, w: CW, h: 0.5, fontSize: 22, color: C.text2 });
  T(s, '1 October 2026', { x: X0, y: 6.36, w: 4, h: 0.3, fontSize: 13, color: C.muted });
  T(s, 'Every number in this deck is in the repository, with the script or report that produced it', {
    x: XR - 8, y: 6.36, w: 8, h: 0.3, fontSize: 13, color: C.muted, align: 'right' });
  s.addNotes('Open with this: "Since the last update we worked on two things: we made the simulator take its numbers from our own car, ' +
    'and we merged the team\'s work into one version. While merging, we found two defects in the simulator, and we know the fix for each." ' +
    'The last update was about correcting the simulator; this one is about making it take its numbers from the car itself.');
}

// ===================================================================== 2. summary
{
  const s = pres.addSlide(); bg(s);
  title(s, 'The summary in three lines', 0.89, 34);
  [
    ['The simulator\'s constants are now computed from our car\'s logs', 'Heat, boost ceiling, spark, enrichment and downshifts — all recomputed with every new drive'],
    ['We logged a new drive, and merged the team\'s work into one version', 'Drive B: forty-one full-throttle pulls in a held gear · The merge: 15 conflicting files, no file deleted'],
    ['And we found two defects in the simulator, with a known fix for each', 'The coolant calculation oscillates, and an artificial one-second "knock" at the start of every climb'],
  ].forEach(([h, sub], i) => {
    const y = 1.82 + i * 1.46;
    card(s, X0, y, CW, 1.26);
    T(s, h, { x: X0 + 0.3, y: y + 0.27, w: CW - 0.6, h: 0.36, fontSize: 19, bold: true });
    T(s, sub, { x: X0 + 0.3, y: y + 0.68, w: CW - 0.6, h: 0.36, fontSize: 15, color: C.text3 });
  });
  s.addNotes('This slide is the whole talk. If time is short, it is enough on its own. The third point is not bad news: ' +
    'we found the two defects ourselves while reviewing the merge, and the fix for each is written down and agreed between Jad and Ghassan.');
}

// ===================================================================== 3. drive B
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Data');
  title(s, 'A new drive: full-throttle pulls in a held gear');
  T(s, 'Why: our earlier drives never asked for high boost at low engine speed, so the simulator could not know what the car does there.', {
    x: X0, y: 1.78, w: CW, h: 0.36, fontSize: 14.5, color: C.text3 });
  [
    ['41', C.blue, 'full-throttle pulls', 'in 6th, 7th and 8th, held manually, over 26.7 minutes'],
    ['1.05 s', C.text, 'per reading', 'we logged only 7 channels, so each one is read every 1.05 seconds'],
    ['321.7', C.text, 'minutes logged now', 'over 11 drives, 8 of them carrying usable samples — it was 295.0 minutes over 10 drives'],
  ].forEach(([big, col, h, sub], i) => {
    const w = 3.73, gap = (CW - 3 * w) / 2, x = X0 + i * (w + gap), y = 2.35;
    card(s, x, y, w, 2.2);
    T(s, big, { x: x + 0.22, y: y + 0.22, w: w - 0.44, h: 0.6, fontSize: 30, bold: true, color: col, lineSpacingMultiple: 1.0 });
    T(s, h, { x: x + 0.22, y: y + 0.88, w: w - 0.44, h: 0.32, fontSize: 15.5, bold: true });
    T(s, sub, { x: x + 0.22, y: y + 1.24, w: w - 0.44, h: 0.85, fontSize: 13, color: C.text3 });
  });
  card(s, X0, 4.85, CW, 1.3, C.amberFill, C.amberLn);
  T(s, 'A lesson we paid for: we forgot the ambient-temperature channel', { x: X0 + 0.3, y: 5.03, w: CW - 0.6, h: 0.34, fontSize: 16, bold: true, color: C.amber });
  T(s, 'Every heat calculation in the model needs it. We filled it with 42 °C from our own afternoon drives and flagged every such row as assumed — and the channel is now on every drive\'s list.', {
    x: X0 + 0.3, y: 5.42, w: CW - 0.6, h: 0.62, fontSize: 14.5, color: C.text2 });
  s.addNotes('A full-throttle pull in a held gear: we hold the gear manually (M mode), floor it for a few seconds, then lift. ' +
    'The aim is to learn how much boost the turbo, and the engine, can give while turning slowly. ' +
    'One reading every 1.05 seconds is seven times faster than drive 7475b5d7, which logged 26 channels. ' +
    'If he asks about the ambient temperature: the mistake is logged as lesson 21, and the filled-in value is flagged in the data so it never mixes with measured rows.');
}

// ===================================================================== 4. derived constants
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'From the car itself');
  title(s, 'The constants now come from the car\'s logs, not typed by hand');
  table(s, ['Constant', 'Before', 'Now'], [
    [{ text: 'Block and oil heat', o: B }, 'Assumed numbers', 'Fitted on 7 drives that log oil, coolant and ambient'],
    [{ text: 'Turbo boost ceiling', o: B }, 'A formula fitted once, on 8 September', 'The measured envelope itself: the highest boost the car reached at each airflow'],
    [{ text: 'Spark offset', o: B }, '26.18 — and the fitted line was never used at all', '13.42 — it now sets the spark at 25 of 26 points, with zero bias'],
    [{ text: 'Enrichment timing', o: B }, '2 and 9 s, on a wrong time axis', '1.5 and 3.0 s, from the timestamps · 8 of 9 cells within 0.02 of the car'],
    [{ text: 'Downshift table', o: B }, 'Typed by hand', 'Measured from the simulator itself after every change'],
  ], { x: X0, y: 1.85, colW: [2.6, 3.65, 5.3], rowH: [0.46, 0.6, 0.6, 0.6, 0.6, 0.6], size: 13.5 });
  T(s, 'One script recomputes all of them with every new drive. What this car cannot provide is written down with the reason: turbine housing heat, exhaust back-pressure, and the radiator\'s split.', {
    x: X0, y: 5.45, w: CW, h: 0.6, fontSize: 13.5, color: C.text3 });
  s.addNotes('In plain words: instead of typing a number once and leaving it, the program computes it from the car\'s data every time a new drive arrives. ' +
    'The spark line was written down, but the simulator never used it: it sat above the knock limit at every point, so all the spark came from the knock model. ' +
    'If he asks about other cars: the same method could be tried on any car we log with the same channels — but we have not tried it yet, so we promise no result.');
}

// ===================================================================== 5. oil node
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Oil');
  title(s, 'The oil model was wrong in the shape of its equation, not its numbers', 1.08, 28);
  T(s, 'Model error on the Taif drive, °C', { x: X0, y: 1.85, w: 5.7, h: 0.32, fontSize: 14, bold: true });
  s.addChart(pres.charts.BAR, [
    { name: 'Before', labels: ['Oil', 'Coolant'], values: [7.55, 5.51] },
    { name: 'After', labels: ['Oil', 'Coolant'], values: [3.57, 2.28] },
  ], {
    x: X0, y: 2.2, w: 5.7, h: 3.0, barDir: 'col', barGrouping: 'clustered', barGapWidthPct: 60,
    chartColors: ['5D6E7D', C.blue], showValue: true, dataLabelPosition: 'outEnd',
    dataLabelFontFace: F, dataLabelFontSize: 13, dataLabelColor: C.text, dataLabelFormatCode: '0.00',
    catAxisLabelFontFace: F, catAxisLabelFontSize: 13, catAxisLabelColor: C.text2,
    catAxisLineShow: true, catAxisLineColor: C.cardLn,
    valAxisHidden: true, valGridLine: { style: 'none' }, catGridLine: { style: 'none' },
    valAxisMinVal: 0, valAxisMaxVal: 9,
    showLegend: true, legendPos: 'b', legendFontFace: F, legendFontSize: 12, legendColor: C.text3,
  });
  const xr = 6.9, wr = XR - xr;
  card(s, xr, 1.85, wr, 1.15);
  T(s, '11–15 °C above coolant', { x: xr + 0.25, y: 2.0, w: wr - 0.5, h: 0.36, fontSize: 18, bold: true, color: C.red });
  T(s, 'at 3700–4800 rpm and 70–100 km/h — the Taif drive', { x: xr + 0.25, y: 2.42, w: wr - 0.5, h: 0.4, fontSize: 13.5, color: C.text3 });
  card(s, xr, 3.15, wr, 1.15);
  T(s, '2–3 °C below coolant', { x: xr + 0.25, y: 3.3, w: wr - 0.5, h: 0.36, fontSize: 18, bold: true, color: C.blue });
  T(s, 'at 2600 rpm and 130–140 km/h — fast cruising on a flat road', { x: xr + 0.25, y: 3.72, w: wr - 0.5, h: 0.4, fontSize: 13.5, color: C.text3 });
  T(s, 'Oil temperature follows engine speed, and the air under the car cools the sump as road speed rises. The old model heated it with a fixed share of the fuel.', {
    x: xr, y: 4.45, w: wr, h: 0.85, fontSize: 14, bold: true });
  card(s, X0, 5.5, CW, 0.95, C.amberFill, C.amberLn);
  T(s, 'Still short: under sustained load it reads 97.0 °C where the car sits between 103 and 111, and the review found that fuel heats the oil too. Drive A is the data that settles it.', {
    x: X0 + 0.3, y: 5.66, w: CW - 0.6, h: 0.65, fontSize: 14, color: C.text2 });
  s.addNotes('If he asks why we did not tune the numbers until it matched: we tried, and every tuning improved one drive and broke another. ' +
    'When that happens, the problem is the shape of the equation, not its numbers — lesson 20 in our mistake log. ' +
    'The figures: oil error fell from 7.55 to 3.57 degrees, and to 3.90 if the constants are fitted without the Taif drive. ' +
    'The oil time constant is now 57 seconds instead of 14 by the equation, and 60 seconds when measured the same way as the car (the validation slide). ' +
    'The review found the sentence "fuel does not heat the oil" wrong: the gap rises 1.5 to 2.8 degrees for every gram of fuel per second, and we corrected it.');
}

// ===================================================================== 6. physics corrections
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Three physics corrections', C.red);
  title(s, 'Three errors in the equations — two of them cancel out');
  table(s, ['What', 'Was', 'Now', 'Effect on the peak temperature'], [
    [{ text: 'Exhaust flow into the turbine', o: B }, 'fuel × 15', 'air + fuel (conservation of mass)', { text: 'raises it 5.5 °C', o: { color: C.red, bold: true } }],
    [{ text: 'Air density in aerodynamic drag', o: B }, 'a fixed 1.2', 'from ambient: 1.12 at 42 °C', { text: 'lowers it 6.2 °C', o: { color: C.blue, bold: true } }],
    [{ text: 'Turbo inlet temperature, for the boost ceiling', o: B }, 'the charge temperature, after the turbo', 'ambient, as the ceiling\'s own definition says', '—'],
  ], { x: X0, y: 1.85, colW: [3.3, 2.6, 3.35, 2.3], rowH: [0.46, 0.62, 0.62, 0.62], size: 14 });
  card(s, X0, 4.45, CW, 1.45, C.blueFill, C.blueLn);
  T(s, [
    { text: 'That is why the peak on the test climb barely moved: 884, then 883 °C. ', options: { bold: true, color: C.text } },
    { text: 'Not because nothing changed — two opposite corrections of about the same size. The computed damage moved by 12–13%.' },
  ], { x: X0 + 0.3, y: 4.68, w: CW - 0.6, h: 1.0, fontSize: 15.5, color: C.text2 });
  s.addNotes('Conservation of mass means: what leaves through the exhaust = the air in + the fuel. The old formula (fuel × 15) was 4.5% low in normal running ' +
    'and 11% high when the engine is enriched, so it hid part of the cooling that enrichment really gives. ' +
    'If he notices that the peak did not change — that is exactly the point: the agreement is a coincidence, and we measured each correction on its own.');
}

// ===================================================================== 7. gearbox + spark line
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Gearbox and engine control');
  title(s, 'Two defects that changed how the simulated car behaved');
  const w = 5.66, y = 1.85, h = 3.25;
  card(s, X0, y, w, h);
  T(s, 'The gearbox would not downshift', { x: X0 + 0.28, y: y + 0.25, w: w - 0.56, h: 0.38, fontSize: 18, bold: true });
  T(s, 'In 8th at 130 km/h the simulated engine gives 333 N·m, and the gearbox only downshifted above 375. So on a grade of about 9% the car could not hold its speed.', {
    x: X0 + 0.28, y: y + 0.72, w: w - 0.56, h: 1.1, fontSize: 14, color: C.text3 });
  T(s, 'Now it downshifts when the engine falls short, as a real automatic does.', { x: X0 + 0.28, y: y + 1.9, w: w - 0.56, h: 0.6, fontSize: 14, bold: true, color: C.blue });
  T(s, 'The cost, stated: in that range the engine turns about 600 rpm faster than the real car would.', { x: X0 + 0.28, y: y + 2.55, w: w - 0.56, h: 0.6, fontSize: 13, color: C.amber });
  const xB = XR - w;
  card(s, xB, y, w, h);
  T(s, 'The fitted spark line was never used', { x: xB + 0.28, y: y + 0.25, w: w - 0.56, h: 0.38, fontSize: 18, bold: true });
  T(s, 'It sat 9.6° above the knock limit at all 26 points, so all part-load spark came from the knock model, which has not been validated.', {
    x: xB + 0.28, y: y + 0.72, w: w - 0.56, h: 1.1, fontSize: 14, color: C.text3 });
  T(s, 'A new offset computed from the car\'s own spark: the line now sets the spark at 25 of 26 points.', { x: xB + 0.28, y: y + 1.9, w: w - 0.56, h: 0.6, fontSize: 14, bold: true, color: C.blue });
  T(s, 'Zero bias, and an average error of 2.5°.', { x: xB + 0.28, y: y + 2.55, w: w - 0.56, h: 0.5, fontSize: 13, color: C.text3 });
  card(s, X0, 5.3, CW, 0.85, C.blueFill, C.blueLn);
  T(s, [
    { text: 'New check: 40 varied roads. ', options: { bold: true, color: C.text } },
    { text: 'The stock engine controller drives all of them without a torque shortfall, and 14 of them exceed the 850 °C protection limit.' },
  ], { x: X0 + 0.3, y: 5.5, w: CW - 0.6, h: 0.5, fontSize: 14.5, color: C.text2 });
  s.addNotes('A downshift: like flooring it on a hill and the car dropping a gear by itself. The simulator did not, so it asked the engine for torque it could not give. ' +
    'The knock limit: the most spark advance before combustion becomes irregular. ' +
    'The 26 points are steady operating points from our drives, between 30 and 75 kPa.');
}

// ===================================================================== 8. validation vs our car
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Validation');
  title(s, 'Oil and coolant compared with our own car, not textbook ranges', 1.08, 28);
  table(s, ['Quantity', 'Model', 'Our car\'s range', 'Status'], [
    ['Oil under sustained load (the hottest 10 minutes of the Taif drive)', '97.0 °C', '103–111', { text: 'outside', o: { color: C.red, bold: true } }],
    ['Oil time constant', '60 s', '70–100 s', { text: 'outside', o: { color: C.red, bold: true } }],
    ['Coolant on the test climb', '93.0 °C', '83.6–95.5', { text: 'inside', o: { color: C.blue, bold: true } }],
    ['Coolant over the whole Taif drive', '92.2 °C', '91.8–94', { text: 'inside', o: { color: C.blue, bold: true } }],
  ], { x: X0, y: 1.85, colW: [3.95, 1.15, 1.4, 0.95], rowH: [0.45, 0.62, 0.5, 0.5, 0.5], size: 13 });
  const ws = 3.6, xs = XR - ws;
  card(s, xs, 1.85, ws, 2.75, C.card2, C.cardLn);
  T(s, '8 of 11', { x: xs + 0.25, y: 2.3, w: ws - 0.5, h: 0.8, fontSize: 44, bold: true, lineSpacingMultiple: 1.0 });
  T(s, 'quantities inside their band', { x: xs + 0.25, y: 3.1, w: ws - 0.5, h: 0.35, fontSize: 15, bold: true, color: C.blue });
  T(s, '6 of 7 against literature, and 2 of 4 against our own car', { x: xs + 0.25, y: 3.5, w: ws - 0.5, h: 0.8, fontSize: 13.5, color: C.text3 });
  card(s, X0, 4.82, CW, 1.5);
  T(s, 'Three of the four ranges had no source; now they are computed from our drives by a fixed rule, before the comparison. Both misses are the oil, and drive A is the data they need.', {
    x: X0 + 0.3, y: 5.0, w: CW - 0.6, h: 0.75, fontSize: 14.5, bold: true });
  T(s, 'We also checked the GCC specification: no source shows stronger cooling, and even a 50% stronger radiator and fan moves the turbine temperature by half a degree. The fuel is 95 RON, as the model assumes.', {
    x: X0 + 0.3, y: 5.75, w: CW - 0.6, h: 0.5, fontSize: 13, color: C.text3 });
  s.addNotes('8 of 11 is the same count as before, but now 4 rows are compared with our real car — a harder and more honest test. ' +
    'The time constant: how many seconds the oil needs to catch up with a change in temperature. ' +
    'Row 7 (the turbine housing time constant, 48 seconds) is still scored against literature, because the car has no sensor there.');
}

// ===================================================================== 9. knock: untested
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'The knock model', C.amber);
  title(s, 'The knock model has not been tested yet — it has not failed');
  T(s, 'Last time we said there was no relationship between the knock model and the car\'s spark retard. But the drive we compared with was logged with 26 channels, and knock lasts only a second or two.', {
    x: X0, y: 1.8, w: CW, h: 0.7, fontSize: 15, color: C.text3 });
  [
    ['404 and 410', C.text, 'readings of the two spark angles', 'in 55 minutes — one every 8 seconds or so'],
    ['One third', C.text, 'of the reading pairs', 'had their two halves read more than a second apart'],
    ['3–8°', C.red, 'less advance in the real car', 'the car\'s spark under high boost is lower than our model\'s — only 31 readings, too few to calibrate'],
  ].forEach(([big, col, h, sub], i) => {
    const w = 3.73, gap = (CW - 3 * w) / 2, x = X0 + i * (w + gap), y = 2.65;
    card(s, x, y, w, 1.95);
    T(s, big, { x: x + 0.22, y: y + 0.2, w: w - 0.44, h: 0.55, fontSize: 26, bold: true, color: col, lineSpacingMultiple: 1.0 });
    T(s, h, { x: x + 0.22, y: y + 0.8, w: w - 0.44, h: 0.32, fontSize: 15, bold: true });
    T(s, sub, { x: x + 0.22, y: y + 1.15, w: w - 0.44, h: 0.7, fontSize: 13, color: C.text3 });
  });
  card(s, X0, 4.85, CW, 1.3, C.blueFill, C.blueLn);
  T(s, 'The fix: drive C', { x: X0 + 0.3, y: 5.02, w: CW - 0.6, h: 0.34, fontSize: 16, bold: true, color: C.blue });
  T(s, 'Only 6 channels, so both angles are read about every 1.25 s · a held gear at 2000–3500 rpm · in the afternoon heat · and the decision rule written before the drive.', {
    x: X0 + 0.3, y: 5.42, w: CW - 0.6, h: 0.6, fontSize: 14.5, color: C.text2 });
  s.addNotes('This is the same trap we fell into with the intake-air sensor: the correlation was 0.35 while the readings were slow, and 0.95 once we logged only 7 channels. ' +
    'So "we found no relationship" does not mean "there is no relationship" — the measurement was slower than the thing it measures. ' +
    'Drive C writes nothing to the car: it only logs, the passenger holds the phone and the driver drives.');
}

// ===================================================================== 10. two defects
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'A declared retraction', C.red);
  title(s, 'Two defects in the simulator, found while reviewing the merge');
  const w = 5.66, y = 1.9, h = 2.85;
  card(s, X0, y, w, h, C.blueFill, C.blueLn);
  T(s, 'Defect 1: the coolant calculation oscillates', { x: X0 + 0.28, y: y + 0.24, w: w - 0.56, h: 0.36, fontSize: 16.5, bold: true });
  T(s, 'The simulator updates temperatures once a second, and the model\'s coolant thermostat reacts faster than that step. So the coolant jumps about 2 °C every step, and with a 2-second step it swings between 85 and 95 °C and never settles.', {
    x: X0 + 0.28, y: y + 0.68, w: w - 0.56, h: 1.45, fontSize: 13.5, color: C.text2 });
  T(s, 'The fix: split every second into 10 small steps.', { x: X0 + 0.28, y: y + 2.2, w: w - 0.56, h: 0.4, fontSize: 14.5, bold: true, color: C.blue });
  const xB = XR - w;
  card(s, xB, y, w, h, C.redFill, C.redLn);
  T(s, 'Defect 2: a false one-second knock at each climb', { x: xB + 0.28, y: y + 0.24, w: w - 0.56, h: 0.36, fontSize: 16.5, bold: true });
  T(s, 'When a climb starts abruptly, the engine controller picks the spark for the previous second\'s pressure, while the load jumps in the same second. That one second holds 58.6 of the trip\'s 60.6 knock-damage units.', {
    x: xB + 0.28, y: y + 0.68, w: w - 0.56, h: 1.45, fontSize: 13.5, color: C.text2 });
  T(s, 'The fix: a climb that ramps in over 8 seconds brings it down to 2.4.', { x: xB + 0.28, y: y + 2.2, w: w - 0.56, h: 0.4, fontSize: 14.5, bold: true, color: C.red });
  card(s, X0, 5.0, CW, 1.2, C.card2, C.cardLn);
  T(s, 'What it voids', { x: X0 + 0.3, y: 5.15, w: CW - 0.6, h: 0.3, fontSize: 13.5, color: C.red });
  T(s, '"Hand-written preview loses by 0.3 points" — the whole gap is this one second; on turbine and oil damage alone the two policies tie. And no H/τ curve is quotable until defect 1 is fixed.', {
    x: X0 + 0.3, y: 5.48, w: CW - 0.6, h: 0.65, fontSize: 14.5 });
  s.addNotes('Say it with confidence, not as an apology: we found both defects ourselves, in the merge review. ' +
    'An example for the first: a driver who looks at the road once every two seconds over-corrects right, then left, and weaves. Looking every tenth of a second, he drives straight. ' +
    'The second does not happen in the real car: a real engine controller picks the spark every engine revolution, and a real road does not jump from flat to 12% in an instant. ' +
    'Jad and Ghassan agreed: both are fixed before any new measurement.');
}

// ===================================================================== 11. what changed since 20 Sep
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Numbers that changed since 20 September');
  title(s, 'What we said last time, and what it is now');
  table(s, ['Figure', 'On 20 September', 'Now', 'Why'], [
    [{ text: 'Data logged', o: B }, '295.0 min · 10 drives', '321.7 min · 11 drives', 'drive B'],
    [{ text: 'Peak temperature on the test climb', o: B }, '884 °C', '883 °C', 'two opposite corrections'],
    [{ text: 'Damage cut by protection', o: B }, '34.0%', '43.4%', 'exhaust flow corrected'],
    [{ text: 'Peak estimated temperature, drive 7475b5d7', o: B }, '890.6 °C', '873.1 °C', 'exhaust flow corrected'],
    [{ text: 'Hand-written preview vs "current grade"', o: B }, 'minus 0.4 points', 'minus 0.3 points', 'all of it is the knock second'],
    [{ text: 'Validation', o: B }, '8 of 11', '8 of 11', 'but 4 rows are now against our car'],
  ], { x: X0, y: 1.85, colW: [3.95, 2.35, 2.35, 2.9], rowH: [0.45, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5], size: 13.5 });
  T(s, 'The 0.206% figure — 36 seconds above the limit — has not yet been re-measured on the corrected physics. And every number here will move again after the two fixes.', {
    x: X0, y: 5.6, w: CW, h: 0.6, fontSize: 13.5, color: C.text3 });
  s.addNotes('Say this before he asks: the numbers changed because the simulator became more accurate, and every change has a written reason. ' +
    'He saw 34% in the last update, so he should hear why it is now 43.4%: the old exhaust formula understated the damage of the stock car, so the percentage came out lower than it really is. ' +
    '"Current grade" is a hand-written policy that protects according to the grade the car is on now, with no look ahead.');
}

// ===================================================================== 12. tools
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Tools we built');
  title(s, 'Tools that make mistakes show instead of hide');
  [
    ['3D drive-replay lab', 'Replays our logged drives in the browser: all eight gears, temperature curves, and H/τ moment by moment.',
      'While building it we found the fifth channel on this car whose name does not match what it measures: the "internal gear" channel sits at 8, so 8th gear showed as "measured" on 62% of one drive.'],
    ['Document guard', 'A script that recomputes every published number and compares it with the documents, failing with the file and the line.',
      'We cleaned 187 stale mentions down to zero. Now 73 checks and 837 number mentions all pass, and its self-test catches 16 of 16 planted errors.'],
    ['Merging the team\'s work', 'Ghassan\'s and Jad\'s branches are now one version, on the main branch.',
      '15 conflicting files and 91 decisions, each one written down, and no file deleted: 454 of 454. The rule: Ghassan\'s physics, Jad\'s verification method.'],
  ].forEach(([h, a, b], i) => {
    const w = 3.73, gap = (CW - 3 * w) / 2, x = X0 + i * (w + gap), y = 1.85;
    card(s, x, y, w, 3.55);
    T(s, h, { x: x + 0.22, y: y + 0.24, w: w - 0.44, h: 0.4, fontSize: 16.5, bold: true });
    T(s, a, { x: x + 0.22, y: y + 0.75, w: w - 0.44, h: 1.2, fontSize: 13.5, color: C.text2 });
    T(s, b, { x: x + 0.22, y: y + 2.0, w: w - 0.44, h: 1.45, fontSize: 13, color: C.text3 });
  });
  T(s, 'The live app and the replay lab are ready to demo if there is time.', { x: X0, y: 5.75, w: CW, h: 0.35, fontSize: 14, color: C.text3 });
  s.addNotes('The lab can be shown if there is time left: it replays a real drive in three dimensions, with the estimated temperature moment by moment. ' +
    'The document guard is why every number in this deck has a source: if a number changes in the simulator and we forget to update a document, the check fails.');
}

// ===================================================================== 13. next steps
{
  const s = pres.addSlide(); bg(s);
  kicker(s, 'Next step');
  title(s, 'Fix the two defects, then measure everything again');
  [
    ['1', 'Split the heat calculation', 'Ten small steps inside every second, then re-fit the constants the same way and re-run every check.'],
    ['2', 'Ramped climbs', 'Every change of grade ramps in over a few seconds, as on a real road.'],
    ['3', 'Drive C, then drive A', 'Drive C for knock: six channels, a held gear. Drive A: a long climb in the heat, then five minutes idling at the top.'],
    ['4', 'Update the numbers and documents', 'After the fixes, re-run every number and update the documents and pages once.'],
  ].forEach(([n, h, sub], i) => {
    const w = (CW - 0.3) / 2, col = i % 2, row = Math.floor(i / 2);
    const x = X0 + col * (w + 0.3), y = 1.85 + row * 1.42;
    card(s, x, y, w, 1.25);
    T(s, n, { x: x + 0.25, y: y + 0.22, w: 0.5, h: 0.6, fontSize: 30, bold: true, color: C.blue, lineSpacingMultiple: 1.0 });
    T(s, h, { x: x + 0.85, y: y + 0.2, w: w - 1.1, h: 0.36, fontSize: 16.5, bold: true });
    T(s, sub, { x: x + 0.85, y: y + 0.58, w: w - 1.1, h: 0.62, fontSize: 13, color: C.text3 });
  });
  card(s, X0, 4.8, CW, 1.45, C.amberFill, C.amberLn);
  T(s, 'Limits we write into the thesis instead of hiding them', { x: X0 + 0.3, y: 4.95, w: CW - 0.6, h: 0.32, fontSize: 14.5, bold: true, color: C.amber });
  const lw = (CW - 0.6 - 0.4) / 3;
  [
    'Altitude is not modelled: the test climb rises 2340 m while the engine breathes sea-level air',
    'The turbine housing\'s heat capacity is assumed, not measured',
    'The radiator\'s split between airflow and fan cannot be told apart from this car\'s data',
  ].forEach((t, i) => {
    T(s, t, { x: X0 + 0.3 + i * (lw + 0.2), y: 5.35, w: lw, h: 0.8, fontSize: 12.5, bold: true, color: C.text2 });
  });
  s.addNotes('Close with this: we know exactly what the two defects are, their fixes are written down and agreed, and after that we re-measure everything in one go. ' +
    'Drive C comes before A because C settles the knock question, and A settles the oil. ' +
    'If he asks about new cars: deriving the constants from the logs could work for any car we log with the same channels — but we have to try it before promising a result.');
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
