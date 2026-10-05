// The results tab's drawing library (/results).
//
// A COPY, not an import: the generic drawing helpers of Ghassan's published
// page, results/page/template.html (lines 747-978, and sideLabel at 992-996, as
// of commit a7ce729). His page and make_page.py are never edited (design Q4),
// so the copy is adapted here instead (design 7.3):
//  - every class it writes carries the rc- prefix. The lab's style.css styles
//    bare svg elements and .chart/.grid, and results.css resets those for the
//    tab and styles these names only;
//  - plot() writes NO axis titles: they are HTML beside the chart (design 7.2),
//    so an Arabic word never reaches SVG text, and its svg gets no role="img"
//    (design 7.3: the focusable marks are never inside role=img). o.aria, when
//    given, labels the svg as a group;
//  - sideLabel MEASURES its label with getComputedTextLength() instead of
//    guessing 6.8 px a character, and falls back to that guess only where
//    nothing could be measured (a node that is not laid out);
//  - the mounting code is a factory, createMounter(): one ResizeObserver over
//    every chart, one document pointerdown listener, an error hook, and a
//    teardown, so the page can redraw every chart after a language switch and
//    drop them all when it rebuilds, without stacking listeners;
//  - the number formatter f() and the heat colour mix() of the template are
//    not copied: results-format.mjs formats numbers, and no R1a figure is a
//    heat map.
// Nothing here reads a result or a string: results-charts.mjs decides WHAT is
// drawn, this file only HOW.

export const NS = 'http://www.w3.org/2000/svg';
let UID = 0;

// ------------------------------------------------------------ dom helpers
export function S(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  if (attrs) for (const k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
export function T(parent, x, y, str, attrs) {
  const t = S('text', Object.assign({ x, y }, attrs || {}), parent);
  t.textContent = str;
  return t;
}
export function H(tag, attrs, parent) {
  const e = document.createElement(tag);
  if (attrs) for (const k in attrs) {
    if (k === 'text') e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]);
  }
  if (parent) parent.appendChild(e);
  return e;
}
export const fin = v => v != null && Number.isFinite(v);

// ----------------------------------------------------------------- scales
export function lin(d0, d1, r0, r1) {
  const s = v => r0 + (v - d0) / (d1 - d0) * (r1 - r0);
  s.inv = p => d0 + (p - r0) / (r1 - r0) * (d1 - d0);
  return s;
}
export function logs(d0, d1, r0, r1) {
  const a = Math.log(d0), b = Math.log(d1);
  const s = v => r0 + (Math.log(v) - a) / (b - a) * (r1 - r0);
  s.inv = p => Math.exp(a + (p - r0) / (r1 - r0) * (b - a));
  return s;
}
export function ticks(lo, hi, n) {
  const raw = (hi - lo) / Math.max(1, n);
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const e = raw / mag;
  const step = (e >= 7.5 ? 10 : e >= 3.5 ? 5 : e >= 1.5 ? 2 : 1) * mag;
  const out = [];
  for (let v = Math.ceil(lo / step - 1e-9) * step; v <= hi + step * 1e-9; v += step)
    out.push(+v.toFixed(10));
  return out;
}

// ------------------------------------------------------------------- plot
export function plot(host, o) {
  const W = o.w, Hh = o.h;
  const m = Object.assign({ t: 12, r: 16, b: 42, l: 52 }, o.m || {});
  const svg = S('svg', { width: W, height: Hh, viewBox: `0 0 ${W} ${Hh}`, class: 'rc-plot',
                         role: o.aria ? 'group' : null, 'aria-label': o.aria || null }, host);
  const x = (o.x.log ? logs : lin)(o.x.d[0], o.x.d[1], m.l, W - m.r);
  const y = (o.y.log ? logs : lin)(o.y.d[0], o.y.d[1], Hh - m.b, m.t);
  const grid = S('g', { class: 'rc-grid' }, svg);
  const pw = W - m.l - m.r, ph = Hh - m.t - m.b;
  if (!o.x.none) {
    const xt = o.x.ticks || ticks(o.x.d[0], o.x.d[1], Math.max(2, Math.round(pw / 80)));
    for (const v of xt) {
      const px = x(v);
      if (o.xgrid !== false) S('line', { x1: px, x2: px, y1: m.t, y2: Hh - m.b }, grid);
      T(svg, px, Hh - m.b + 16, (o.x.fmt || String)(v), { 'text-anchor': 'middle' });
    }
  }
  if (!o.y.none) {
    const yt = o.y.ticks || ticks(o.y.d[0], o.y.d[1], Math.max(2, Math.round(ph / 48)));
    for (const v of yt) {
      const py = y(v);
      S('line', { x1: m.l, x2: W - m.r, y1: py, y2: py }, grid);
      T(svg, m.l - 7, py + 4, (o.y.fmt || String)(v), { 'text-anchor': 'end' });
    }
  }
  S('line', { x1: m.l, x2: W - m.r, y1: Hh - m.b, y2: Hh - m.b, class: 'rc-axis' }, svg);
  // o.x.label and o.y.label are ignored on purpose: axis titles are HTML.
  const id = 'rc-clip' + (++UID);
  S('rect', { x: m.l, y: m.t - 2, width: pw, height: ph + 4 }, S('clipPath', { id }, S('defs', {}, svg)));
  const g = S('g', { 'clip-path': `url(#${id})` }, svg);
  const top = S('g', {}, svg);
  return { svg, g, top, x, y, m, W, H: Hh, pw, ph, host };
}
export function line(P, xs, ys, st) {
  let d = '', pen = false;
  for (let i = 0; i < xs.length; i++) {
    if (!fin(ys[i]) || !fin(xs[i])) { pen = false; continue; }
    d += (pen ? 'L' : 'M') + P.x(xs[i]).toFixed(1) + ',' + P.y(ys[i]).toFixed(1);
    pen = true;
  }
  return S('path', { d, class: 'rc-ln', style: `stroke:${st.c};stroke-width:${st.w || 2};` +
    (st.dash ? `stroke-dasharray:${st.dash};` : '') + (st.op ? `opacity:${st.op};` : '') }, P.g);
}
export function hline(P, v, st) {
  const py = P.y(v);
  const el = S('line', { x1: P.m.l, x2: P.W - P.m.r, y1: py, y2: py,
              style: `stroke:${st.c};stroke-width:${st.w || 1.3};stroke-dasharray:${st.dash || '5 4'}` }, P.g);
  if (st.label) T(P.top, st.right ? P.W - P.m.r - 4 : P.m.l + 6, py + (st.below ? 14 : -6), st.label,
                  { class: 'rc-lbl', style: `fill:${st.c}`, 'text-anchor': st.right ? 'end' : 'start' });
  return el;
}
export function vline(P, v, st) {
  const px = P.x(v);
  const el = S('line', { x1: px, x2: px, y1: P.m.t, y2: P.H - P.m.b,
              style: `stroke:${st.c};stroke-width:${st.w || 1.3};stroke-dasharray:${st.dash || '5 4'}` }, P.g);
  if (st.label) T(P.top, px + 5, P.m.t + (st.dy || 12), st.label,
                  { class: 'rc-lbl', style: `fill:${st.c}` });
  return el;
}

// -------------------------------------------------------------- tooltip
export function tip(host) {
  let t = host.querySelector(':scope > .rc-tip');
  if (!t) { t = H('div', { class: 'rc-tip', role: 'status' }, host); t.hidden = true; }
  return t;
}
export function showTip(host, px, py, title, rows) {
  const t = tip(host);
  t.replaceChildren();
  if (title) H('div', { class: 'rc-tt', text: title }, t);
  for (const r of rows) {
    const row = H('div', { class: 'rc-tr' }, t);
    const k = H('span', { class: 'rc-key' }, row);
    k.style.borderColor = r.c || 'transparent';
    H('b', { text: r.v }, row);
    if (r.k) H('span', { class: 'rc-tl', text: r.k }, row);
  }
  t.hidden = false;
  const hw = host.clientWidth, tw = t.offsetWidth, th = t.offsetHeight;
  let left = px + 14;
  if (left + tw > hw) left = px - 14 - tw;
  if (left < 0) left = Math.max(0, Math.min(hw - tw, px - tw / 2));
  let top = py - th - 12;
  if (top < 0) top = py + 16;
  t.style.left = left + 'px';
  t.style.top = top + 'px';
}
export function hideTip(host) {
  const t = host.querySelector(':scope > .rc-tip');
  if (t) t.hidden = true;
}
export function localXY(P, e) {
  const r = P.svg.getBoundingClientRect();
  return [e.clientX - r.left, e.clientY - r.top];
}
export function onPointer(el, move, leave) {
  el.addEventListener('pointermove', move);
  el.addEventListener('pointerdown', move);
  el.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') leave(); });
}

// Crosshair: snaps to the nearest x, lists every series at that x.
export function crosshair(P, xs, series, xfmt) {
  const hair = S('line', { class: 'rc-hair', y1: P.m.t, y2: P.H - P.m.b, visibility: 'hidden' }, P.top);
  const dots = series.map(s => S('circle', { r: 4, class: 'rc-hdot', style: `fill:${s.c}`, visibility: 'hidden' }, P.top));
  const hit = S('rect', { x: P.m.l, y: P.m.t, width: P.pw, height: P.ph, class: 'rc-hit' }, P.top);
  const leave = () => {
    hair.setAttribute('visibility', 'hidden');
    dots.forEach(d => d.setAttribute('visibility', 'hidden'));
    hideTip(P.host);
  };
  onPointer(hit, e => {
    const [px, py] = localXY(P, e);
    const xv = P.x.inv(px);
    let lo = 0, hi = xs.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (xs[mid] < xv) lo = mid; else hi = mid; }
    const i = Math.abs(xs[lo] - xv) < Math.abs(xs[hi] - xv) ? lo : hi;
    const X = P.x(xs[i]);
    hair.setAttribute('x1', X); hair.setAttribute('x2', X); hair.setAttribute('visibility', 'visible');
    series.forEach((s, k) => {
      const v = s.ys[i];
      if (fin(v)) {
        dots[k].setAttribute('cx', X); dots[k].setAttribute('cy', P.y(v)); dots[k].setAttribute('visibility', 'visible');
      } else dots[k].setAttribute('visibility', 'hidden');
    });
    showTip(P.host, X, py, xfmt(xs[i]), series.map(s => ({ c: s.c, v: s.f(s.ys[i]), k: s.name })));
  }, leave);
}
// Nearest point: the pointer only has to be closest, not on the dot.
export function nearest(P, pts, rowsOf, radius) {
  const px = pts.map(p => p.px != null ? [p.px, p.py] : [P.x(p.x), P.y(p.y)]);
  const ring = S('circle', { r: 8, class: 'rc-ring', visibility: 'hidden' }, P.top);
  const hit = S('rect', { x: P.m.l, y: P.m.t, width: P.pw, height: P.ph, class: 'rc-hit' }, P.top);
  const leave = () => { ring.setAttribute('visibility', 'hidden'); hideTip(P.host); };
  onPointer(hit, e => {
    const [mx, my] = localXY(P, e);
    let best = -1, bd = (radius || 32) ** 2;
    for (let i = 0; i < px.length; i++) {
      const d = (px[i][0] - mx) ** 2 + (px[i][1] - my) ** 2;
      if (d < bd) { bd = d; best = i; }
    }
    if (best < 0) return leave();
    ring.setAttribute('cx', px[best][0]); ring.setAttribute('cy', px[best][1]); ring.setAttribute('visibility', 'visible');
    const r = rowsOf(pts[best]);
    showTip(P.host, px[best][0], px[best][1], r.title, r.rows);
  }, leave);
}
// Per-mark hover and keyboard focus for bars, dots and cells.
export function markTip(P, el, cx, cy, title, rows) {
  el.setAttribute('tabindex', '0');
  el.classList.add('rc-mark');
  const show = () => showTip(P.host, cx, cy, title, rows);
  el.addEventListener('pointerenter', show);
  el.addEventListener('pointerdown', show);
  el.addEventListener('focus', show);
  el.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') hideTip(P.host); });
  el.addEventListener('blur', () => hideTip(P.host));
}
// A label right of a point, or left of it when it would leave the plot. The
// width is measured; 6.8 px a character only where nothing could be measured.
export function sideLabel(P, x, y, str, style) {
  const t = T(P.top, x + 14, y, str, { class: 'rc-lbl', 'text-anchor': 'start', style });
  let w = 0;
  try { w = typeof t.getComputedTextLength === 'function' ? t.getComputedTextLength() : 0; } catch { w = 0; }
  if (!(w > 0)) w = String(str).length * 6.8;
  if (x + 14 + w >= P.W - P.m.r) {
    t.setAttribute('x', x - 14);
    t.setAttribute('text-anchor', 'end');
  }
  return t;
}

// ------------------------------------------------------------ mounting
// mount(host, draw, hOf): draw(host, w, h) now and on every width change.
// renderAll(force): redraw every chart whose width changed, or every chart
// when forced (a language switch). A zero width never draws: a host that is
// not laid out yet is drawn by the ResizeObserver once it has a width.
// clear(): forget every chart (the page rebuilds its sections); dispose():
// clear, disconnect the observer and remove the document listener.
export function createMounter({ onError } = {}) {
  const charts = [];
  const report = typeof onError === 'function'
    ? onError
    : (host, err) => console.error('results chart', host && host.id, err);
  const RO = globalThis.ResizeObserver;
  const ro = typeof RO === 'function' ? new RO(() => renderAll()) : null;
  const doc = globalThis.document;
  const onDown = e => {
    const target = e && e.target;
    if (target && typeof target.closest === 'function' && target.closest('.rc-chart')) return;
    for (const c of charts) hideTip(c.host);
  };
  if (doc && typeof doc.addEventListener === 'function') doc.addEventListener('pointerdown', onDown);

  function render(c, force) {
    const w = Math.floor(c.host.clientWidth) || 0;
    if (!w || (!force && w === c.w)) return;
    c.w = w;
    c.host.querySelectorAll(':scope > svg').forEach(s => s.remove());
    hideTip(c.host);
    const h = c.hOf ? c.hOf(w) : Math.round(Math.min(400, Math.max(250, w * 0.56)));
    try {
      c.draw(c.host, w, h);
    } catch (err) {
      c.host.querySelectorAll(':scope > svg').forEach(s => s.remove());
      report(c.host, err);
    }
  }
  function mount(host, draw, hOf) {
    if (!host) return;
    const c = { host, draw, hOf, w: 0 };
    charts.push(c);
    if (ro) ro.observe(host);
    render(c, false);
  }
  function renderAll(force = false) {
    for (const c of charts) render(c, force);
  }
  function clear() {
    if (ro) for (const c of charts) ro.unobserve(c.host);
    charts.length = 0;
  }
  function dispose() {
    clear();
    if (ro) ro.disconnect();
    if (doc && typeof doc.removeEventListener === 'function') doc.removeEventListener('pointerdown', onDown);
  }
  return { mount, renderAll, clear, dispose };
}
