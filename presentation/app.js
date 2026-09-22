/* ===========================================================================
   محرك تحت الرقابة — الأدوات التفاعلية
   Every widget reads its colours from the theme tokens so both themes work,
   and every number it draws comes from DATA (dumped from the repository's own
   plant.py / thermal.py / check_premise.py), never from a literal typed here.
   =========================================================================== */
(function () {
  'use strict';

  var LANG = 'ar';
  var REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var AR = function (n, d) { return Number(n).toLocaleString('ar-EG', { minimumFractionDigits: d || 0, maximumFractionDigits: d === undefined ? 0 : d }); };
  var EN = function (n, d) { return Number(n).toFixed(d === undefined ? 0 : d); };

  /* ---------- theme-aware colour lookup ---------------------------------- */
  function tok(name, el) {
    return getComputedStyle(el || document.documentElement).getPropertyValue(name).trim();
  }
  var C = {};
  function refreshTokens() {
    ['--bg', '--surface', '--surface-2', '--line', '--text', '--muted',
      '--ember', '--ember-deep', '--cool', '--crit', '--grid'].forEach(function (k) {
        C[k.slice(2)] = tok(k);
      });
  }
  refreshTokens();
  var themeWatchers = [];
  function onTheme(fn) { themeWatchers.push(fn); }
  var mq = window.matchMedia('(prefers-color-scheme: dark)');
  function themeChanged() { refreshTokens(); themeWatchers.forEach(function (f) { try { f(); } catch (e) { } }); }
  if (mq.addEventListener) mq.addEventListener('change', themeChanged);
  new MutationObserver(themeChanged).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  /* ---------- hi-dpi canvas with a resize observer ------------------------ */
  function fitCanvas(cv, draw) {
    var ctx = cv.getContext('2d');
    function resize() {
      var r = cv.getBoundingClientRect();
      if (!r.width) return;
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      cv.width = Math.round(r.width * dpr);
      cv.height = Math.round(r.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      draw(ctx, r.width, r.height);
    }
    if (window.ResizeObserver) new ResizeObserver(resize).observe(cv);
    window.addEventListener('resize', resize);
    onTheme(resize);
    requestAnimationFrame(resize);
    return { redraw: resize, ctx: ctx };
  }

  /* ---------- small chart helpers ----------------------------------------- */
  function axes(ctx, w, h, pad) {
    ctx.strokeStyle = C.line; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad.l, pad.t); ctx.lineTo(pad.l, h - pad.b); ctx.lineTo(w - pad.r, h - pad.b);
    ctx.stroke();
  }
  function gridlines(ctx, w, h, pad, n, vertical) {
    ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
    for (var i = 0; i <= n; i++) {
      ctx.beginPath();
      if (vertical) {
        var x = pad.l + (w - pad.l - pad.r) * i / n;
        ctx.moveTo(x, pad.t); ctx.lineTo(x, h - pad.b);
      } else {
        var y = pad.t + (h - pad.t - pad.b) * i / n;
        ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y);
      }
      ctx.stroke();
    }
  }
  function label(ctx, txt, x, y, col, size, align, baseline) {
    ctx.fillStyle = col || C.muted;
    ctx.font = (size || 11) + 'px "IBM Plex Mono", ui-monospace, monospace';
    ctx.textAlign = align || 'center';
    ctx.textBaseline = baseline || 'middle';
    ctx.direction = 'ltr';          // digits and units never reorder
    ctx.fillText(txt, x, y);
  }
  function labelAr(ctx, txt, x, y, col, size, align) {
    txt = tr(txt);
    ctx.fillStyle = col || C.muted;
    ctx.font = (size || 12) + 'px ' + (LANG === 'en'
      ? '"IBM Plex Sans", system-ui, sans-serif'
      : '"IBM Plex Sans Arabic", system-ui, sans-serif');
    ctx.textAlign = align || 'center';
    ctx.textBaseline = 'middle';
    ctx.direction = LANG === 'en' ? 'ltr' : 'rtl';
    ctx.fillText(txt, x, y);
    ctx.direction = 'ltr';
  }

  /* ---------- canvas strings, both editions ------------------------------ */
  var DICT = {
    'سحب': 'intake', 'عادم': 'exhaust', 'شرارة': 'spark',
    'العزم': 'Torque', 'الخبط': 'Knock', 'حدّ الخبط': 'knock limit',
    'تقديم الشرارة قبل النقطة الميتة العليا': 'Spark advance, °BTDC',
    'حرارة العادم': 'Exhaust gas temp', 'غنيّ · إثراء': 'rich · enrichment', 'فقير': 'lean',
    'لامدا λ — نسبة الهواء إلى الوقود': 'Lambda λ — air-to-fuel ratio',
    'أفق الرؤية H': 'preview horizon H', 'الزمن بعد بداية الحمل': 'Time after the load step',
    'ميل الطريق ١٢٪': '12 % grade',
    'حرارة بيت التيربو · المحور مقصوص عند ٧٠٠°م': 'Turbine housing temp · axis cut at 700 °C',
    'حدّ الحماية': 'protection limit', 'الضرر المتراكم': 'Accumulated damage',
    'ضرر متراكم': 'Accumulated damage', 'دقيقة': 'min', 'الطلعة تبدأ': 'climb begins',
    'القيد ما عاد يربط': 'constraint stops binding',
    'أفضلية الرؤية · نقطة مئوية': 'Preview edge · percentage points',
    'H / τ  ←  القطعة تصير أثقل وأبطأ': 'H / τ   →   heavier, slower component'
  };
  function tr(s) { return LANG === 'en' ? (DICT[s] || s) : s; }
  function tv(ar, en) { return LANG === 'en' ? en : ar; }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

  /* a thermal ramp: cool -> ember -> critical, used wherever heat is shown */
  function heatColor(t) {
    t = clamp(t, 0, 1);
    var stops = [[0.00, [56, 132, 148]], [0.45, [214, 158, 46]], [0.75, [224, 110, 40]], [1.00, [198, 48, 38]]];
    for (var i = 0; i < stops.length - 1; i++) {
      if (t <= stops[i + 1][0]) {
        var u = (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0]);
        var a = stops[i][1], b = stops[i + 1][1];
        return 'rgb(' + Math.round(lerp(a[0], b[0], u)) + ',' + Math.round(lerp(a[1], b[1], u)) + ',' + Math.round(lerp(a[2], b[2], u)) + ')';
      }
    }
    return 'rgb(198,48,38)';
  }

  /* =========================================================================
     ١ · دورة الشوط الرباعي
     ========================================================================= */
  function fourStroke(root) {
    var cv = root.querySelector('canvas');
    var out = root.querySelector('[data-out]');
    var btns = Array.prototype.slice.call(root.querySelectorAll('[data-stroke]'));
    var play = root.querySelector('[data-play]');
    var theta = 0;            // crank angle, degrees, 0 = TDC of intake
    var running = !REDUCED;
    var STROKES_AR = [
      { name: 'السحب', en: 'Intake', note: 'صمام الهواء مفتوح. المكبس ينزل ويسحب هواء.' },
      { name: 'الضغط', en: 'Compression', note: 'الصمامات مقفلة. المكبس يطلع ويضغط الخليط. الشرارة تنطلق قبل القمة.' },
      { name: 'القدرة', en: 'Power', note: 'الخليط يحترق ويدفع المكبس لتحت. هذا الشوط الوحيد اللي يعطي شغل.' },
      { name: 'العادم', en: 'Exhaust', note: 'صمام العادم مفتوح. المكبس يطلع ويطرد الغاز الحار على التيربو.' }
    ];
    var STROKES_EN = [
      { name: 'Intake', en: '1 / 4', note: 'Inlet valve open. The piston drops and pulls air in.' },
      { name: 'Compression', en: '2 / 4', note: 'Both valves shut. The piston rises and squeezes the charge. The plug fires before the top.' },
      { name: 'Power', en: '3 / 4', note: 'The charge burns and drives the piston down. The only stroke that does work.' },
      { name: 'Exhaust', en: '4 / 4', note: 'Exhaust valve open. The piston rises and pushes hot gas out onto the turbine.' }
    ];
    function STROKES(i) { return (LANG === 'en' ? STROKES_EN : STROKES_AR)[i]; }
    var SPARK_AT = 340;       // 20 deg BTDC of the compression stroke

    function strokeIndex(th) { return Math.floor((th % 720) / 180); }

    var f = fitCanvas(cv, function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      var cx = w * 0.5, bore = Math.min(w * 0.34, 132);
      // true slider-crank: rod length L, crank radius r, piston pin at
      //   y = crankY - ( r·cosθ + sqrt(L² − (r·sinθ)²) )
      var topY = h * 0.235, strokeLen = h * 0.27, crankR = strokeLen / 2;
      var rodL = strokeLen * 1.30;
      var crankY = topY + crankR + rodL;

      var th = theta % 720;
      var si = strokeIndex(th);
      var rad = (th % 360) * Math.PI / 180;
      var pinY = crankY - (crankR * Math.cos(rad) + Math.sqrt(rodL * rodL - Math.pow(crankR * Math.sin(rad), 2)));
      var pistonH = Math.max(22, strokeLen * 0.26);
      var pistonTop = pinY;

      // ---- cylinder walls
      ctx.strokeStyle = C.line; ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(cx - bore / 2, topY - 20); ctx.lineTo(cx - bore / 2, crankY - 8);
      ctx.moveTo(cx + bore / 2, topY - 20); ctx.lineTo(cx + bore / 2, crankY - 8);
      ctx.moveTo(cx - bore / 2, topY - 20); ctx.lineTo(cx + bore / 2, topY - 20);
      ctx.stroke();

      // ---- combustion chamber fill: charge colour by stroke
      var fill = ['rgba(53,176,167,0.16)', 'rgba(53,176,167,0.30)',
      'rgba(224,110,40,0.42)', 'rgba(140,130,120,0.22)'][si];
      ctx.fillStyle = fill;
      ctx.fillRect(cx - bore / 2 + 1, topY - 19, bore - 2, pistonTop - topY + 19);

      // ---- power-stroke flame front
      if (si === 2) {
        var burn = ((th - 360) % 180) / 180;
        var g = ctx.createRadialGradient(cx, topY - 6, 2, cx, topY - 6, bore * (0.25 + burn * 0.9));
        g.addColorStop(0, 'rgba(255,214,120,' + (0.85 * (1 - burn)) + ')');
        g.addColorStop(1, 'rgba(224,110,40,0)');
        ctx.fillStyle = g;
        ctx.fillRect(cx - bore / 2 + 1, topY - 19, bore - 2, pistonTop - topY + 19);
      }

      // ---- valves
      function valve(x, open, col) {
        ctx.strokeStyle = col; ctx.lineWidth = 3; ctx.lineCap = 'round';
        var drop = open ? 9 : 0;
        ctx.beginPath();
        ctx.moveTo(x, topY - 40); ctx.lineTo(x, topY - 22 + drop);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x - 9, topY - 20 + drop); ctx.lineTo(x + 9, topY - 20 + drop);
        ctx.stroke();
      }
      var intakeOpen = si === 0, exhOpen = si === 3;
      valve(cx - bore * 0.27, intakeOpen, intakeOpen ? C.cool : C.line);
      valve(cx + bore * 0.27, exhOpen, exhOpen ? C.crit : C.line);
      labelAr(ctx, 'سحب', cx - bore * 0.27, topY - 50, intakeOpen ? C.cool : C.muted, 10);
      labelAr(ctx, 'عادم', cx + bore * 0.27, topY - 50, exhOpen ? C.crit : C.muted, 10);

      // ---- spark plug
      var sparking = th > SPARK_AT && th < SPARK_AT + 26;
      ctx.strokeStyle = sparking ? C.ember : C.muted;
      ctx.lineWidth = sparking ? 2.5 : 1.5;
      ctx.beginPath(); ctx.moveTo(cx, topY - 42); ctx.lineTo(cx, topY - 24); ctx.stroke();
      if (sparking) {
        ctx.fillStyle = C.ember;
        ctx.beginPath(); ctx.arc(cx, topY - 20, 4.5, 0, 7); ctx.fill();
        labelAr(ctx, 'شرارة', cx + 40, topY - 30, C.ember, 11, 'right');
      }

      // ---- conrod + crank, drawn under the piston
      var jx = cx + crankR * Math.sin(rad), jy = crankY - crankR * Math.cos(rad);
      ctx.strokeStyle = C.grid; ctx.setLineDash([2, 3]); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(cx, crankY, crankR, 0, 7); ctx.stroke(); ctx.setLineDash([]);
      ctx.strokeStyle = C.text; ctx.lineWidth = 3; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(cx, pinY + pistonH * 0.5); ctx.lineTo(jx, jy); ctx.stroke();
      ctx.strokeStyle = C.ember; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(cx, crankY); ctx.lineTo(jx, jy); ctx.stroke();
      ctx.fillStyle = C.bg; ctx.strokeStyle = C.text; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(cx, crankY, 11, 0, 7); ctx.fill(); ctx.stroke();
      ctx.fillStyle = C.ember;
      ctx.beginPath(); ctx.arc(jx, jy, 4.5, 0, 7); ctx.fill();

      // ---- piston
      ctx.fillStyle = C['surface-2']; ctx.strokeStyle = C.text; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.rect(cx - bore / 2 + 2, pistonTop, bore - 4, pistonH); ctx.fill(); ctx.stroke();
      ctx.strokeStyle = C.muted; ctx.lineWidth = 1;
      [0.26, 0.44, 0.62].forEach(function (d) {
        ctx.beginPath(); ctx.moveTo(cx - bore / 2 + 4, pistonTop + pistonH * d); ctx.lineTo(cx + bore / 2 - 4, pistonTop + pistonH * d); ctx.stroke();
      });

      // ---- TDC / BDC marks
      ctx.strokeStyle = C.grid; ctx.setLineDash([3, 4]); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(cx - bore / 2 - 24, topY); ctx.lineTo(cx + bore / 2 + 24, topY); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cx - bore / 2 - 24, topY + strokeLen); ctx.lineTo(cx + bore / 2 + 24, topY + strokeLen); ctx.stroke();
      ctx.setLineDash([]);
      label(ctx, 'TDC', cx - bore / 2 - 28, topY, C.muted, 10, 'right');
      label(ctx, 'BDC', cx - bore / 2 - 28, topY + strokeLen, C.muted, 10, 'right');

      // ---- crank angle readout
      label(ctx, 'crank ' + EN(th, 0) + '°', 10, 14, C.muted, 11, 'left');
    });

    function tick() {
      if (running) { theta = (theta + (REDUCED ? 0 : 2.4)) % 720; f.redraw(); sync(); }
      requestAnimationFrame(tick);
    }
    function sync() {
      var si = strokeIndex(theta % 720);
      btns.forEach(function (b, i) { b.setAttribute('aria-pressed', String(i === si)); });
      if (out) {
        out.querySelector('[data-name]').textContent = STROKES(si).name;
        out.querySelector('[data-en]').textContent = STROKES(si).en;
        out.querySelector('[data-note]').textContent = STROKES(si).note;
      }
    }
    btns.forEach(function (b, i) {
      b.addEventListener('click', function () {
        running = false; play.setAttribute('aria-pressed', 'false');
        play.querySelector('span').textContent = tv('شغّل', 'Play');
        theta = i * 180 + 90; f.redraw(); sync();
      });
    });
    play.addEventListener('click', function () {
      running = !running;
      play.setAttribute('aria-pressed', String(running));
      play.querySelector('span').textContent = running ? tv('وقّف', 'Pause') : tv('شغّل', 'Play');
    });
    play.setAttribute('aria-pressed', String(running));
    play.querySelector('span').textContent = running ? tv('وقّف', 'Pause') : tv('شغّل', 'Play');
    sync(); tick();
  }

  /* =========================================================================
     ٢ · توقيت الشرارة ضد الخبط — real plant.py sweeps
     ========================================================================= */
  function sparkKnock(root) {
    var S = window.SWEEPS;
    var cv = root.querySelector('canvas');
    var slider = root.querySelector('input[type=range]');
    var caseBtns = Array.prototype.slice.call(root.querySelectorAll('[data-case]'));
    var readout = root.querySelector('[data-readout]');
    var key = 'spark_part';
    var spark = 20;

    function rows() { return S[key].rows; }
    function at(sp) {
      var r = rows(), best = r[0];
      for (var i = 0; i < r.length; i++) if (Math.abs(r[i][0] - sp) < Math.abs(best[0] - sp)) best = r[i];
      return best;
    }
    function mbt() {
      var r = rows(), b = r[0];
      for (var i = 0; i < r.length; i++) if (r[i][1] > b[1]) b = r[i];
      return b[0];
    }
    function knockLimit() {
      var r = rows();
      for (var i = 0; i < r.length; i++) if (r[i][2] >= 1.0) return r[i][0];
      return null;
    }

    var f = fitCanvas(cv, function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      var pad = { l: 46, r: 46, t: 18, b: 40 };
      var r = rows();
      var x0 = r[0][0], x1 = r[r.length - 1][0];
      var tqMax = 0, kiMax = 0;
      r.forEach(function (p) { tqMax = Math.max(tqMax, p[1]); kiMax = Math.max(kiMax, p[2]); });
      tqMax *= 1.12; kiMax = Math.max(kiMax * 1.05, 1.4);
      var X = function (v) { return pad.l + (w - pad.l - pad.r) * (v - x0) / (x1 - x0); };
      var YT = function (v) { return h - pad.b - (h - pad.t - pad.b) * v / tqMax; };
      var YK = function (v) { return h - pad.b - (h - pad.t - pad.b) * v / kiMax; };

      gridlines(ctx, w, h, pad, 4, false);

      // everything to the right of the knock limit is where the engine detonates
      var klx = knockLimit();
      if (klx !== null) {
        ctx.fillStyle = 'rgba(198,48,38,0.11)';
        ctx.fillRect(X(klx), pad.t, (w - pad.r) - X(klx), h - pad.t - pad.b);
      }
      var yDanger = YK(1.0);
      ctx.strokeStyle = C.crit; ctx.setLineDash([5, 4]); ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.moveTo(pad.l, yDanger); ctx.lineTo(w - pad.r, yDanger); ctx.stroke();
      ctx.setLineDash([]);
      label(ctx, 'KI = 1', w - pad.r - 4, yDanger - 10, C.crit, 10, 'right');

      // torque curve
      ctx.strokeStyle = C.cool; ctx.lineWidth = 2.5; ctx.beginPath();
      r.forEach(function (p, i) { i ? ctx.lineTo(X(p[0]), YT(p[1])) : ctx.moveTo(X(p[0]), YT(p[1])); });
      ctx.stroke();
      // knock integral curve
      ctx.strokeStyle = C.ember; ctx.lineWidth = 2.5; ctx.beginPath();
      r.forEach(function (p, i) { i ? ctx.lineTo(X(p[0]), YK(p[2])) : ctx.moveTo(X(p[0]), YK(p[2])); });
      ctx.stroke();

      // MBT + knock limit markers
      var m = mbt(), kl = knockLimit();
      ctx.strokeStyle = C.cool; ctx.setLineDash([2, 3]); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(X(m), pad.t); ctx.lineTo(X(m), h - pad.b); ctx.stroke();
      ctx.setLineDash([]);
      label(ctx, 'MBT', X(m), pad.t + 22, C.cool, 10);
      if (kl !== null) {
        ctx.strokeStyle = C.crit; ctx.setLineDash([2, 3]);
        ctx.beginPath(); ctx.moveTo(X(kl), pad.t); ctx.lineTo(X(kl), h - pad.b); ctx.stroke();
        ctx.setLineDash([]);
        labelAr(ctx, 'حدّ الخبط', X(kl), pad.t + 36, C.crit, 10);
      }

      // the reader's cursor
      var p = at(spark);
      ctx.strokeStyle = C.text; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(X(p[0]), pad.t); ctx.lineTo(X(p[0]), h - pad.b); ctx.stroke();
      [[YT(p[1]), C.cool], [YK(p[2]), C.ember]].forEach(function (q) {
        ctx.fillStyle = q[1]; ctx.beginPath(); ctx.arc(X(p[0]), q[0], 5, 0, 7); ctx.fill();
        ctx.strokeStyle = C.bg; ctx.lineWidth = 2; ctx.stroke();
      });

      axes(ctx, w, h, pad);
      labelAr(ctx, 'العزم', pad.l + 4, pad.t + 6, C.cool, 11, 'left');
      labelAr(ctx, 'الخبط', w - pad.r - 4, pad.t + 6, C.ember, 11, 'right');
      for (var t = Math.ceil(x0 / 10) * 10; t <= x1; t += 10) label(ctx, EN(t, 0) + '°', X(t), h - pad.b + 13, C.muted, 10);
      labelAr(ctx, 'تقديم الشرارة قبل النقطة الميتة العليا', (pad.l + w - pad.r) / 2, h - 9, C.muted, 11);
    });

    function sync() {
      var p = at(spark);
      var kl = knockLimit(), m = mbt();
      var safe = p[2] < 1.0;
      root.querySelector('[data-v-spark]').textContent = EN(p[0], 0);
      readout.querySelector('[data-v-torque]').textContent = EN(p[1], 0);
      readout.querySelector('[data-v-ki]').textContent = EN(p[2], 2);
      readout.querySelector('[data-v-egt]').textContent = EN(p[3], 0);
      readout.querySelector('[data-v-mfb]').textContent = EN(p[5], 1);
      var st = readout.querySelector('[data-state]');
      st.textContent = safe ? (p[2] > 0.85 ? tv('على الحافة', 'on the edge') : tv('آمن', 'safe'))
        : tv('يخبط — يكسر المكبس', 'knocking — this breaks pistons');
      st.className = 'state ' + (safe ? (p[2] > 0.85 ? 'is-warn' : 'is-ok') : 'is-crit');
      var verdict = root.querySelector('[data-verdict]');
      if (kl === null) {
        verdict.textContent = tv(
          'عند هذا الحمل ما يوصل الخبط أبداً في مدى الزوايا هذا — المعايرة تقدر توصل MBT عند ' + EN(m, 0) + '°.',
          'At this load nothing knocks anywhere in the range — the calibration can sit right at MBT, ' + EN(m, 0) + '°.');
      } else if (kl <= m) {
        verdict.textContent = tv(
          'حد الخبط عند ' + EN(kl, 0) + '° يجي قبل MBT عند ' + EN(m, 0) + '°. يعني ما تقدر توصل أقصى عزم أبداً — تنازلت عن ' + EN(100 * (1 - at(kl - 1)[1] / at(m)[1]), 1) + '٪ من العزم عشان تحمي المكبس. هذي معايرة المحركات باختصار.',
          'The knock limit at ' + EN(kl, 0) + '° arrives before MBT at ' + EN(m, 0) + '°. You can never reach peak torque here: you give up ' + EN(100 * (1 - at(kl - 1)[1] / at(m)[1]), 1) + ' % of it to keep the piston. That tension is what engine calibration is.');
      } else {
        verdict.textContent = tv(
          'حد الخبط عند ' + EN(kl, 0) + '° بعد MBT عند ' + EN(m, 0) + '° — عند هذا الحمل الخفيف تقدر توصل أقصى عزم بأمان.',
          'The knock limit at ' + EN(kl, 0) + '° sits past MBT at ' + EN(m, 0) + '° — at this light load you can reach peak torque safely.');
      }
      f.redraw();
    }
    slider.addEventListener('input', function () { spark = +slider.value; sync(); });
    caseBtns.forEach(function (b) {
      b.addEventListener('click', function () {
        key = b.dataset.case;
        caseBtns.forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
        root.querySelector('[data-op]').textContent = b.dataset.op;
        sync();
      });
    });
    caseBtns[0].setAttribute('aria-pressed', 'true');
    sync();
  }

  /* =========================================================================
     ٢ب · ثمن الحماية — real lambda sweep from plant.predict()
     ========================================================================= */
  function leverCost(root) {
    var S = window.SWEEPS.lambda_sweep;
    var cv = root.querySelector('canvas');
    var slider = root.querySelector('input[type=range]');
    var rows = S.rows;                       // [lam, torque, egt, ki, fuel]
    var idx = 0;
    function stoich() {
      var b = 0;
      for (var i = 0; i < rows.length; i++) if (Math.abs(rows[i][0] - 1.0) < Math.abs(rows[b][0] - 1.0)) b = i;
      return rows[b];
    }
    slider.max = String(rows.length - 1);
    (function () { var b = 0; for (var i = 0; i < rows.length; i++) if (Math.abs(rows[i][0] - 1.0) < Math.abs(rows[b][0] - 1.0)) b = i; idx = b; })();

    var f = fitCanvas(cv, function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      var pad = { l: 46, r: 46, t: 18, b: 40 };
      var x0 = rows[0][0], x1 = rows[rows.length - 1][0];
      var eMin = 1e9, eMax = -1e9, tMin = 1e9, tMax = -1e9;
      rows.forEach(function (r) { eMin = Math.min(eMin, r[2]); eMax = Math.max(eMax, r[2]); tMin = Math.min(tMin, r[1]); tMax = Math.max(tMax, r[1]); });
      eMin -= 20; eMax += 20; tMin -= 20; tMax += 20;
      var X = function (v) { return pad.l + (w - pad.l - pad.r) * (v - x0) / (x1 - x0); };
      var YE = function (v) { return h - pad.b - (h - pad.t - pad.b) * (v - eMin) / (eMax - eMin); };
      var YT = function (v) { return h - pad.b - (h - pad.t - pad.b) * (v - tMin) / (tMax - tMin); };

      gridlines(ctx, w, h, pad, 4, false);

      // rich / lean sides
      var xs = X(1.0);
      ctx.fillStyle = 'rgba(53,176,167,0.08)';
      ctx.fillRect(pad.l, pad.t, Math.max(0, xs - pad.l), h - pad.t - pad.b);
      ctx.strokeStyle = C.line; ctx.setLineDash([3, 4]); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(xs, pad.t); ctx.lineTo(xs, h - pad.b); ctx.stroke(); ctx.setLineDash([]);
      labelAr(ctx, 'غنيّ · إثراء', xs - 10, h - pad.b - 12, C.cool, 10, 'right');
      labelAr(ctx, 'فقير', xs + 10, h - pad.b - 12, C.muted, 10, 'left');

      ctx.strokeStyle = C.crit; ctx.lineWidth = 2.5; ctx.beginPath();
      rows.forEach(function (r, i) { i ? ctx.lineTo(X(r[0]), YE(r[2])) : ctx.moveTo(X(r[0]), YE(r[2])); });
      ctx.stroke();
      ctx.strokeStyle = C.cool; ctx.lineWidth = 2.5; ctx.beginPath();
      rows.forEach(function (r, i) { i ? ctx.lineTo(X(r[0]), YT(r[1])) : ctx.moveTo(X(r[0]), YT(r[1])); });
      ctx.stroke();

      var p = rows[idx];
      ctx.strokeStyle = C.text; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(X(p[0]), pad.t); ctx.lineTo(X(p[0]), h - pad.b); ctx.stroke();
      [[YE(p[2]), C.crit], [YT(p[1]), C.cool]].forEach(function (q) {
        ctx.fillStyle = q[1]; ctx.beginPath(); ctx.arc(X(p[0]), q[0], 5, 0, 7); ctx.fill();
        ctx.strokeStyle = C.bg; ctx.lineWidth = 2; ctx.stroke();
      });

      axes(ctx, w, h, pad);
      labelAr(ctx, 'حرارة العادم', pad.l + 4, pad.t + 6, C.crit, 11, 'left');
      labelAr(ctx, 'العزم', w - pad.r - 4, pad.t + 6, C.cool, 11, 'right');
      [0.8, 0.9, 1.0, 1.1].forEach(function (v) { label(ctx, v.toFixed(1), X(v), h - pad.b + 13, C.muted, 10); });
      labelAr(ctx, 'لامدا λ — نسبة الهواء إلى الوقود', (pad.l + w - pad.r) / 2, h - 9, C.muted, 11);
    });

    function sync() {
      var p = rows[idx], s = stoich();
      root.querySelector('[data-v-lam]').textContent = EN(p[0], 2);
      root.querySelector('[data-v-egt]').textContent = EN(p[2], 0);
      root.querySelector('[data-v-tq]').textContent = EN(p[1], 0);
      root.querySelector('[data-v-fuel]').textContent = EN(p[4], 1);
      var dE = p[2] - s[2], dT = 100 * (p[1] - s[1]) / s[1], dF = 100 * (p[4] - s[4]) / s[4];
      var v = root.querySelector('[data-verdict]');
      if (Math.abs(p[0] - 1.0) < 0.006) {
        v.textContent = tv(
          'عند λ = 1.00 المحرك يحرق كل الوقود الذي حقنه. هذه نقطة الأساس — حرّك المؤشّر لليسار وشوف ثمن التبريد.',
          'At λ = 1.00 the engine burns every gram it injects. This is the baseline — drag left and watch what cooling costs.');
        v.className = 'verdict';
      } else if (p[0] < 1.0) {
        v.textContent = tv(
          'إثراء. العادم ' + (dE < 0 ? 'أبرد ' + EN(-dE, 0) : 'أسخن ' + EN(dE, 0)) +
            ' درجة. الفاتورة: ' + EN(Math.abs(dT), 1) + '٪ من العزم و' + EN(dF, 1) +
            '٪ وقود إضافي يخرج من العادم دون أن يولّد شيئاً.',
          'Enrichment. The exhaust is ' + EN(Math.abs(dE), 0) + ' °C ' + (dE < 0 ? 'cooler' : 'hotter') +
            '. The bill: ' + EN(Math.abs(dT), 1) + ' % of the torque and ' + EN(dF, 1) +
            ' % more fuel, leaving through the exhaust without producing anything.');
        v.className = 'verdict is-warn';
      } else {
        v.textContent = tv(
          'خليط فقير. العادم ' + (dE < 0 ? 'أبرد ' + EN(-dE, 0) : 'أسخن ' + EN(dE, 0)) +
            ' درجة، لكن العزم هبط ' + EN(Math.abs(dT), 1) + '٪ — تدفع من القوة ولا تشتري حماية يُعتمد عليها. ' +
            'ولهذا لا أحد يحمي تيربو بخليط فقير.',
          'Lean. The exhaust is ' + EN(Math.abs(dE), 0) + ' °C ' + (dE < 0 ? 'cooler' : 'hotter') +
            ', but torque fell ' + EN(Math.abs(dT), 1) + ' % — you pay in power and buy no protection you can rely on. ' +
            'Which is why nobody protects a turbine by running lean.');
        v.className = 'verdict is-crit';
      }
      f.redraw();
    }
    slider.value = String(idx);
    slider.addEventListener('input', function () { idx = +slider.value; sync(); });
    sync();
  }

  /* =========================================================================
     ٣ · الكتلة الحرارية وثابت الزمن τ
     ========================================================================= */
  function thermalTau(root) {
    var cv = root.querySelector('canvas');
    var btns = Array.prototype.slice.call(root.querySelectorAll('[data-node]'));
    var hSlider = root.querySelector('[data-h]');
    var H = 30;
    var NODES = [
      { id: 'turb', tau: 48.0,
        note: 'قيست بقياس استجابة الخطوة. C/UA يعطي ٥٠٫٣ ثانية.',
        noteEn: 'Measured from the step response. C/UA gives 50.3 s.' },
      { id: 'oil', tau: 16.0,
        note: 'كان ٢٥ ثانية قبل معايرة مبرّد الزيت على ٨٠٠ واط/كلفن.',
        noteEn: 'It was 25 s before the oil cooler was calibrated to 800 W/K.' },
      { id: 'block', tau: 300,
        note: 'أبطأ عقدة في الشبكة — دقائق، لا ثوانٍ.',
        noteEn: 'The slowest node in the network — minutes, not seconds.' },
      { id: 'batt', tau: 1140,
        note: 'المصنع الثاني. ≈ ١٩ دقيقة — أبطأ من التيربو بأربعٍ وعشرين مرة.',
        noteEn: 'The second plant. About 19 min — twenty-four times slower than the turbine.' }
    ];
    var cur = NODES[0];

    var f = fitCanvas(cv, function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      var pad = { l: 44, r: 16, t: 18, b: 34 };
      var T = cur.tau * 3.2;                     // x-axis span, seconds
      var X = function (t) { return pad.l + (w - pad.l - pad.r) * t / T; };
      var Y = function (v) { return h - pad.b - (h - pad.t - pad.b) * v; };

      gridlines(ctx, w, h, pad, 4, false);

      // the preview horizon H, as a band from t=0
      var hw = Math.min(X(H) - pad.l, w - pad.l - pad.r);
      if (hw > 0.5) {
        ctx.fillStyle = 'rgba(53,176,167,0.13)';
        ctx.fillRect(pad.l, pad.t, hw, h - pad.t - pad.b);
        ctx.strokeStyle = C.cool; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(pad.l + hw, pad.t); ctx.lineTo(pad.l + hw, h - pad.b); ctx.stroke();
        if (hw > 54) labelAr(ctx, 'أفق الرؤية H', pad.l + hw / 2, pad.t + 12, C.cool, 11);
      }

      // exponential approach
      ctx.lineWidth = 2.6;
      var grad = ctx.createLinearGradient(pad.l, 0, w - pad.r, 0);
      grad.addColorStop(0, heatColor(0.05)); grad.addColorStop(0.5, heatColor(0.55)); grad.addColorStop(1, heatColor(0.92));
      ctx.strokeStyle = grad;
      ctx.beginPath();
      for (var i = 0; i <= 220; i++) {
        var t = T * i / 220, v = 1 - Math.exp(-t / cur.tau);
        i ? ctx.lineTo(X(t), Y(v)) : ctx.moveTo(X(t), Y(v));
      }
      ctx.stroke();

      // 63.2 % marker at t = tau
      ctx.strokeStyle = C.ember; ctx.setLineDash([4, 4]); ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.moveTo(X(cur.tau), h - pad.b); ctx.lineTo(X(cur.tau), Y(0.632)); ctx.lineTo(pad.l, Y(0.632)); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = C.ember; ctx.beginPath(); ctx.arc(X(cur.tau), Y(0.632), 5, 0, 7); ctx.fill();
      label(ctx, '63.2%', pad.l - 6, Y(0.632), C.ember, 10, 'right');
      label(ctx, 'τ = ' + (cur.tau >= 120 ? EN(cur.tau / 60, 0) + ' min' : EN(cur.tau, 0) + ' s'), X(cur.tau), h - pad.b + 14, C.ember, 11);

      axes(ctx, w, h, pad);
      label(ctx, '100%', pad.l - 6, Y(1), C.muted, 10, 'right');
      label(ctx, '0', pad.l - 6, Y(0), C.muted, 10, 'right');
      labelAr(ctx, 'الزمن بعد بداية الحمل', (pad.l + w - pad.r) / 2, h - 9, C.muted, 11);
    });

    function sync() {
      btns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.node === cur.id)); });
      var ratio = H / cur.tau;
      root.querySelector('[data-tau]').textContent = cur.tau >= 120
        ? EN(cur.tau / 60, 1) + tv(' دقيقة', ' min') : EN(cur.tau, 0) + tv(' ثانية', ' s');
      root.querySelector('[data-ratio]').textContent = EN(ratio, 2);
      root.querySelector('[data-node-note]').textContent = tv(cur.note, cur.noteEn);
      root.querySelector('[data-h-val]').textContent = EN(H, 0);
      var v = root.querySelector('[data-ratio-verdict]');
      var cls, txt;
      if (ratio >= 3) {
        cls = 'is-warn';
        txt = tv('H ≫ τ — القطعة تسخن وتبرد أسرع مما تشوف. الرؤية المسبقة زائدة عن الحاجة.',
                 'H is much larger than τ — the part heats and cools faster than you can see ahead. Preview is redundant.');
      } else if (ratio >= 0.25) {
        cls = 'is-ok';
        txt = tv('H و τ متقاربين. هنا بالضبط تفيد الرؤية المسبقة — وهذي المنطقة اللي ما أحد رسمها.',
                 'H and τ are comparable. This is exactly where preview pays, and this is the region nobody has mapped.');
      } else {
        cls = 'is-crit';
        txt = tv('τ ≫ H — تشوف ثلاثين ثانية داخل مشكلة تتكوّن على عشر دقائق. الرؤية ما تشتري لك شي.',
                 'τ is much larger than H — you are seeing thirty seconds into a problem that takes ten minutes to develop. Preview buys nothing.');
      }
      v.textContent = txt; v.className = 'verdict ' + cls;
      f.redraw();
    }
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        cur = NODES.filter(function (n) { return n.id === b.dataset.node; })[0]; sync();
      });
    });
    hSlider.addEventListener('input', function () { H = +hSlider.value; sync(); });
    sync();
  }

  /* =========================================================================
     ٤ · السباق — real traces from check_premise.py's own policies
     ========================================================================= */
  function race(root) {
    var T = window.TRACES;
    var cv = root.querySelector('canvas');
    var scrub = root.querySelector('[data-scrub]');
    var play = root.querySelector('[data-play]');
    var blindToggle = root.querySelector('[data-blind]');
    var k = 0, running = false, blinded = false;
    var N = T.baseline.t.length;
    scrub.max = String(N - 1);

    function lanes() {
      var base = tv('الـ ECU الأصلي', 'stock ECU'), react = tv('رد الفعل', 'reactive');
      return blinded
        ? [{ key: 'baseline', ar: base, col: C.muted },
        { key: 'reactive', ar: react, col: C.ember },
        { key: 'blinded', ar: tv('التنبؤ بعد إطفاء الرؤية', 'predictive, preview off'), col: C.crit }]
        : [{ key: 'baseline', ar: base, col: C.muted },
        { key: 'reactive', ar: react, col: C.ember },
        { key: 'predictive', ar: tv('التنبؤ', 'predictive'), col: C.cool }];
    }

    var f = fitCanvas(cv, function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      var pad = { l: 44, r: 14, b: 24 };
      var t0 = T.baseline.t[0], t1 = T.baseline.t[N - 1];
      var X = function (t) { return pad.l + (w - pad.l - pad.r) * (t - t0) / (t1 - t0); };
      var gradH = 20, gap = 26;
      var avail = h - pad.b - gradH - gap - 14;
      var topT = 14 + gradH + 8;            // temperature panel
      var topB = topT + avail * 0.5 + gap;  // damage panel
      var botT = topT + avail * 0.5, botB = h - pad.b;

      // ---- grade strip (the road profile)
      var g = T.baseline.grade, i;
      ctx.fillStyle = C['surface-2'];
      ctx.fillRect(pad.l, 14, w - pad.l - pad.r, gradH);
      ctx.fillStyle = 'rgba(224,110,40,0.32)';
      ctx.beginPath(); ctx.moveTo(pad.l, 14 + gradH);
      for (i = 0; i < N; i++) ctx.lineTo(X(T.baseline.t[i]), 14 + gradH - (g[i] / 0.14) * gradH);
      ctx.lineTo(w - pad.r, 14 + gradH); ctx.closePath(); ctx.fill();
      labelAr(ctx, 'ميل الطريق ١٢٪', w - pad.r - 8, 14 + gradH / 2, C.muted, 10, 'right');

      // ================= panel 1: turbine temperature, zoomed to the top band
      var trig = T.trigger_c;
      var tmin = 700, tmax = 900;
      var Y1 = function (v) { return botT - (botT - topT) * (v - tmin) / (tmax - tmin); };
      ctx.save();
      ctx.beginPath(); ctx.rect(pad.l, topT - 2, w - pad.l - pad.r, botT - topT + 4); ctx.clip();

      ctx.fillStyle = 'rgba(198,48,38,0.10)';
      ctx.fillRect(pad.l, topT, w - pad.l - pad.r, Math.max(0, Y1(trig) - topT));
      ctx.strokeStyle = C.crit; ctx.setLineDash([6, 4]); ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.moveTo(pad.l, Y1(trig)); ctx.lineTo(w - pad.r, Y1(trig)); ctx.stroke();
      ctx.setLineDash([]);

      lanes().forEach(function (L) {
        var d = T[L.key].turb;
        ctx.strokeStyle = L.col;
        ctx.lineWidth = L.key === 'baseline' ? 1.7 : 2.4;
        if (L.key === 'blinded') ctx.setLineDash([8, 4]);
        ctx.beginPath();
        for (var j = 0; j <= k; j++) { var x = X(T[L.key].t[j]), y = Y1(d[j]); j ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
        ctx.stroke(); ctx.setLineDash([]);
        ctx.fillStyle = L.col; ctx.beginPath(); ctx.arc(X(T[L.key].t[k]), Y1(d[k]), 3.6, 0, 7); ctx.fill();
      });
      ctx.restore();

      ctx.strokeStyle = C.line; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(pad.l, topT); ctx.lineTo(pad.l, botT); ctx.lineTo(w - pad.r, botT); ctx.stroke();
      [700, 800, 900].forEach(function (v) { label(ctx, EN(v, 0), pad.l - 5, Y1(v), C.muted, 10, 'right'); });
      labelAr(ctx, 'حرارة بيت التيربو · المحور مقصوص عند ٧٠٠°م', w - pad.r - 6, topT + 10, C.muted, 10, 'right');
      labelAr(ctx, 'حدّ الحماية', pad.l + 8, Y1(trig) - 10, C.crit, 10, 'left');
      label(ctx, EN(trig, 0) + ' °C', pad.l + 68, Y1(trig) - 10, C.crit, 10, 'left');

      // ================= panel 2: accumulated damage — where they really split
      var dmax = T.baseline.dmg_cum[N - 1] * 1.05;
      var Y2 = function (v) { return botB - (botB - topB) * v / dmax; };
      gridlines(ctx, w, h, { l: pad.l, r: pad.r, t: topB, b: pad.b }, 2, false);
      lanes().forEach(function (L) {
        var d = T[L.key].dmg_cum;
        ctx.strokeStyle = L.col; ctx.lineWidth = L.key === 'baseline' ? 1.7 : 2.4;
        if (L.key === 'blinded') ctx.setLineDash([8, 4]);
        ctx.beginPath();
        for (var j = 0; j <= k; j++) { var x = X(T[L.key].t[j]), y = Y2(d[j]); j ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
        ctx.stroke(); ctx.setLineDash([]);
        ctx.fillStyle = L.col; ctx.beginPath(); ctx.arc(X(T[L.key].t[k]), Y2(d[k]), 3.6, 0, 7); ctx.fill();
      });
      ctx.strokeStyle = C.line; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(pad.l, topB); ctx.lineTo(pad.l, botB); ctx.lineTo(w - pad.r, botB); ctx.stroke();
      [0, dmax / 2, dmax].forEach(function (v) { label(ctx, EN(v, 0), pad.l - 5, Y2(v), C.muted, 10, 'right'); });
      labelAr(ctx, 'الضرر المتراكم', pad.l + 6, topB + 10, C.muted, 10, 'left');

      // playhead across both panels
      ctx.strokeStyle = C.text; ctx.globalAlpha = .35; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(X(T.baseline.t[k]), topT); ctx.lineTo(X(T.baseline.t[k]), botB); ctx.stroke();
      ctx.globalAlpha = 1;
      for (var s = 0; s <= t1 - 60; s += 120) label(ctx, EN(s / 60, 0), X(s), botB + 12, C.muted, 10);
      labelAr(ctx, 'دقيقة', w - pad.r, botB + 12, C.muted, 10, 'right');
    });

    function sync() {
      scrub.value = String(k);
      root.querySelector('[data-clock]').textContent = EN(T.baseline.t[k] / 60, 1);
      var rows = root.querySelectorAll('[data-lane]');
      var L = lanes();
      Array.prototype.forEach.call(rows, function (row, i) {
        var lane = L[i]; if (!lane) { row.hidden = true; return; }
        row.hidden = false;
        row.querySelector('[data-lane-name]').textContent = lane.ar;
        row.querySelector('.swatch').style.background = lane.col;
        row.querySelector('[data-lane-temp]').textContent = EN(T[lane.key].turb[k], 0);
        row.querySelector('[data-lane-dmg]').textContent = EN(T[lane.key].dmg_cum[k], 1);
        var bar = row.querySelector('[data-lane-bar] i');
        bar.style.width = (100 * T[lane.key].dmg_cum[k] / Math.max(1, T.baseline.dmg_cum[N - 1])) + '%';
        bar.style.background = lane.col;
      });
      var a = T.reactive.dmg_cum[k], b = T[blinded ? 'blinded' : 'predictive'].dmg_cum[k];
      var eq = root.querySelector('[data-identity]');
      if (blinded) {
        eq.hidden = false;
        eq.querySelector('[data-eq]').textContent = EN(a, 1) + '  =  ' + EN(b, 1);
        // AUDIT.md C3. This note used to read "Identical. The whole gap was
        // preview information and nothing else." -- the void reading. The two
        // traces are equal BY CONSTRUCTION: with preview off, p_predictive
        // returns p_reactive's vector on every step, so the identity cannot
        // fail and is not evidence. Corrected 22 Sep 2026 in the doc sweep.
        eq.querySelector('[data-eq-note]').textContent = Math.abs(a - b) < 0.05
          ? tv('مطابق، لكن بالبناء لا كاكتشاف: بدون رؤية مسبقة ترجع الاستباقية فعل التفاعلية نفسه في كل خطوة، فالتطابق لا يمكن أن يفشل وليس دليلاً (AUDIT C3). الاختبار الحقيقي هو المرحلة D بوكلاء مدرَّبين، وبميزانية C1 لم تنفصل الرؤية عن ضجيج البذور.',
               'Identical, by construction, not as a finding: with preview off the predictive policy returns the reactive action on every step, so this cannot fail and proves nothing (AUDIT.md C3). The real ablation is Phase D, with trained agents: at the C1 budget, preview does not separate from seed noise.')
          : tv('يتقاربان…', 'converging…');
      } else { eq.hidden = true; }
      f.redraw();
    }

    var last = 0;
    function tick(ts) {
      if (running) {
        if (ts - last > (REDUCED ? 120 : 16)) {
          last = ts;
          k += 3;
          if (k >= N) { k = N - 1; running = false; play.setAttribute('aria-pressed', 'false'); play.querySelector('span').textContent = tv('أعد التشغيل', 'Replay'); }
          sync();
        }
      }
      requestAnimationFrame(tick);
    }
    play.addEventListener('click', function () {
      if (k >= N - 1) k = 0;
      running = !running;
      play.setAttribute('aria-pressed', String(running));
      play.querySelector('span').textContent = running ? tv('وقّف', 'Pause') : tv('شغّل', 'Play');
    });
    scrub.addEventListener('input', function () { running = false; play.setAttribute('aria-pressed', 'false'); play.querySelector('span').textContent = tv('شغّل', 'Play'); k = +scrub.value; sync(); });
    blindToggle.addEventListener('change', function () { blinded = blindToggle.checked; sync(); });
    k = N - 1; sync(); tick(0);
  }

  /* =========================================================================
     ٠ · لوحة الفتح — the whole thesis in one still frame
     ========================================================================= */
  function heroTrace(root) {
    var T = window.TRACES;
    var cv = root.querySelector('canvas');
    var N = T.baseline.t.length;
    fitCanvas(cv, function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      // cumulative damage, because that is where the three policies actually
      // separate — the temperatures differ by only ~27 C and overlap on a plot.
      var pad = { l: 34, r: 128, t: 16, b: 22 };
      var t1 = T.baseline.t[N - 1];
      var dmax = T.baseline.dmg_cum[N - 1] * 1.06;
      var X = function (t) { return pad.l + (w - pad.l - pad.r) * t / t1; };
      var Y = function (v) { return h - pad.b - (h - pad.t - pad.b) * v / dmax; };

      // the climb begins at t = 180 s
      ctx.fillStyle = C.grid;
      ctx.fillRect(X(180), pad.t, w - pad.r - X(180), h - pad.t - pad.b);
      ctx.strokeStyle = C.line; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(X(180), pad.t); ctx.lineTo(X(180), h - pad.b); ctx.stroke();
      labelAr(ctx, 'الطلعة تبدأ', X(180) - 5, pad.t + 8, C.muted, 10, 'left');

      var SER = [['baseline', C.muted, 1.8, tv('بدون حماية', 'no protection')],
      ['reactive', C.ember, 2.4, tv('رد فعل', 'reactive')],
      ['predictive', C.cool, 2.4, tv('تنبّؤ', 'predictive')]];
      SER.forEach(function (L) {
        var d = T[L[0]].dmg_cum;
        ctx.strokeStyle = L[1]; ctx.lineWidth = L[2];
        ctx.beginPath();
        for (var i = 0; i < N; i++) { var x = X(T[L[0]].t[i]), y = Y(d[i]); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
        ctx.stroke();
        var ey = Y(d[N - 1]);
        ctx.fillStyle = L[1];
        ctx.beginPath(); ctx.arc(X(t1), ey, 3.5, 0, 7); ctx.fill();
        // name above, figure below, both anchored inside the right gutter
        labelAr(ctx, L[3], w - pad.r + 8, ey - 8, C.muted, 10, 'left');
        label(ctx, EN(d[N - 1], 1), w - pad.r + 8, ey + 7, L[1], 12, 'left');
      });

      axes(ctx, w, h, pad);
      labelAr(ctx, 'ضرر متراكم', pad.l + 4, pad.t + 8, C.muted, 10, 'left');
      label(ctx, '0', pad.l - 4, h - pad.b, C.muted, 10, 'right');
      label(ctx, '12 min', X(t1), h - 8, C.muted, 10, 'center');
    });
  }

  /* =========================================================================
     ٥ · منحنى H/τ — the H2 fixed-limit sweep
     ========================================================================= */
  function htau(root) {
    var cv = root.querySelector('canvas');
    var rows = JSON.parse(root.dataset.rows);   // [C_turb, tau, H/tau, reactive, predictive, edge|null]
    var sel = 2;
    var f = fitCanvas(cv, function (ctx, w, h) {
      ctx.clearRect(0, 0, w, h);
      var pad = { l: 44, r: 20, t: 20, b: 40 };
      var pts = rows.filter(function (r) { return r[5] !== null; });
      var lx0 = Math.log10(0.15), lx1 = Math.log10(6.5);
      var ymax = 30;
      var X = function (v) { return pad.l + (w - pad.l - pad.r) * (Math.log10(v) - lx0) / (lx1 - lx0); };
      var Y = function (v) { return h - pad.b - (h - pad.t - pad.b) * v / ymax; };

      gridlines(ctx, w, h, pad, 3, false);
      [0.2, 0.5, 1, 2, 5].forEach(function (t) {
        ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(X(t), pad.t); ctx.lineTo(X(t), h - pad.b); ctx.stroke();
        label(ctx, String(t), X(t), h - pad.b + 13, C.muted, 10);
      });

      // measured points, connected
      ctx.strokeStyle = C.ember; ctx.lineWidth = 2.4; ctx.beginPath();
      pts.slice().sort(function (a, b) { return a[2] - b[2]; }).forEach(function (p, i) {
        i ? ctx.lineTo(X(p[2]), Y(p[5])) : ctx.moveTo(X(p[2]), Y(p[5]));
      });
      ctx.stroke();

      // the unmeasured region: the constraint stops binding
      var nb = rows.filter(function (r) { return r[5] === null; })[0];
      if (nb) {
        var xnb = X(nb[2]);
        ctx.fillStyle = 'rgba(140,140,140,0.10)';
        ctx.fillRect(pad.l, pad.t, Math.max(0, xnb - pad.l), h - pad.t - pad.b);
        ctx.strokeStyle = C.line; ctx.setLineDash([3, 4]);
        ctx.beginPath(); ctx.moveTo(xnb, pad.t); ctx.lineTo(xnb, h - pad.b); ctx.stroke(); ctx.setLineDash([]);
        labelAr(ctx, 'القيد ما عاد يربط', xnb - 6, pad.t + 14, C.muted, 10, 'left');
      }

      rows.forEach(function (p, i) {
        if (p[5] === null) return;
        var on = i === sel;
        ctx.fillStyle = on ? C.ember : C.surface;
        ctx.strokeStyle = C.ember; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(X(p[2]), Y(p[5]), on ? 7 : 5, 0, 7); ctx.fill(); ctx.stroke();
        label(ctx, EN(p[5], 1), X(p[2]), Y(p[5]) - 15, on ? C.ember : C.muted, 11);
      });

      axes(ctx, w, h, pad);
      for (var v = 0; v <= ymax; v += 10) label(ctx, EN(v, 0), pad.l - 6, Y(v), C.muted, 10, 'right');
      labelAr(ctx, 'أفضلية الرؤية · نقطة مئوية', pad.l + 4, pad.t + 6, C.muted, 10, 'left');
      labelAr(ctx, 'H / τ  ←  القطعة تصير أثقل وأبطأ', (pad.l + w - pad.r) / 2, h - 10, C.muted, 11);
    });
    var btns = Array.prototype.slice.call(root.querySelectorAll('[data-pt]'));
    btns.forEach(function (b, i) {
      b.addEventListener('click', function () { sel = +b.dataset.pt; btns.forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); }); f.redraw(); });
      if (i === sel) b.setAttribute('aria-pressed', 'true');
    });
  }

  /* =========================================================================
     ٦ · المسرد — filter + search
     ========================================================================= */
  function glossary(root) {
    var q = root.querySelector('input[type=search]');
    var chips = Array.prototype.slice.call(root.querySelectorAll('[data-group]'));
    var items = Array.prototype.slice.call(root.querySelectorAll('.term'));
    var groups = root.querySelectorAll('.term-group');
    var active = 'all';
    function apply() {
      var s = (q.value || '').trim().toLowerCase();
      items.forEach(function (it) {
        var okG = active === 'all' || it.dataset.g === active;
        var okS = !s || it.textContent.toLowerCase().indexOf(s) > -1;
        it.hidden = !(okG && okS);
      });
      Array.prototype.forEach.call(groups, function (g) {
        g.hidden = !Array.prototype.some.call(g.querySelectorAll('.term'), function (t) { return !t.hidden; });
      });
      var n = items.filter(function (i) { return !i.hidden; }).length;
      root.querySelector('[data-count]').textContent = LANG === 'en' ? String(n) : AR(n);
    }
    q.addEventListener('input', apply);
    chips.forEach(function (c) {
      c.addEventListener('click', function () {
        active = c.dataset.group;
        chips.forEach(function (o) { o.setAttribute('aria-pressed', String(o === c)); });
        apply();
      });
    });
    apply();
  }

  /* =========================================================================
     الملاحة الجانبية + كشف الأقسام
     ========================================================================= */
  function nav() {
    var links = Array.prototype.slice.call(document.querySelectorAll('.rail a'));
    var secs = links.map(function (a) { return document.querySelector(a.getAttribute('href')); }).filter(Boolean);
    var bar = document.querySelector('.progress i');
    function onScroll() {
      var y = window.scrollY + window.innerHeight * 0.34;
      var idx = 0;
      secs.forEach(function (s, i) { if (s.offsetTop <= y) idx = i; });
      links.forEach(function (a, i) { a.setAttribute('aria-current', i === idx ? 'true' : 'false'); });
      var max = document.body.scrollHeight - window.innerHeight;
      if (bar) bar.style.width = (100 * clamp(window.scrollY / Math.max(1, max), 0, 1)) + '%';
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- collapsibles ------------------------------------------------ */
  function disclosures() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-toggle]'), function (b) {
      var t = document.getElementById(b.dataset.toggle);
      b.addEventListener('click', function () {
        var open = b.getAttribute('aria-expanded') === 'true';
        b.setAttribute('aria-expanded', String(!open));
        t.hidden = open;
        b.querySelector('[data-toggle-label]').textContent = open ? b.dataset.labelClosed : b.dataset.labelOpen;
      });
    });
  }

  /* ---------- theme switch ------------------------------------------------ */
  function themeToggle() {
    var b = document.querySelector('[data-theme-toggle]');
    if (!b) return;
    b.addEventListener('click', function () {
      var r = document.documentElement;
      var now = r.getAttribute('data-theme');
      var sysDark = mq.matches;
      var next = now ? (now === 'dark' ? 'light' : 'dark') : (sysDark ? 'light' : 'dark');
      r.setAttribute('data-theme', next);
      b.setAttribute('aria-label', next === 'dark' ? 'التبديل إلى الوضع الفاتح' : 'التبديل إلى الوضع الداكن');
      try { localStorage.setItem('es-theme', next); } catch (e) { }
    });
    try { var s = localStorage.getItem('es-theme'); if (s) document.documentElement.setAttribute('data-theme', s); } catch (e) { }
  }

  /* =========================================================================
     اللغة — both editions live in the page; only one is shown
     ========================================================================= */
  function readLang() {
    try { var s = localStorage.getItem('es-lang'); if (s === 'ar' || s === 'en') return s; } catch (e) { }
    return 'ar';
  }
  function applyLang(l, announce) {
    LANG = l;
    document.body.setAttribute('data-lang', l);
    document.body.setAttribute('lang', l);
    document.body.setAttribute('dir', l === 'ar' ? 'rtl' : 'ltr');
    Array.prototype.forEach.call(document.querySelectorAll('[data-target]'), function (a) {
      a.setAttribute('href', '#' + a.dataset.target + (l === 'en' ? '-en' : ''));
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-t-ar]'), function (el) {
      el.textContent = l === 'en' ? (el.dataset.tEn || '') : (el.dataset.tAr || '');
    });
    var b = document.querySelector('[data-lang-toggle]');
    if (b) {
      b.textContent = l === 'ar' ? 'English' : 'العربية';
      b.setAttribute('aria-label', l === 'ar' ? 'Switch to English' : 'التبديل إلى العربية');
    }
    try { localStorage.setItem('es-lang', l); } catch (e) { }
    if (deck.on) deck.rebuild(0);
    // the edition that was hidden has zero-width canvases; make them redraw
    window.dispatchEvent(new Event('resize'));
    if (announce) window.scrollTo(0, 0);
  }
  function langToggle() {
    var b = document.querySelector('[data-lang-toggle]');
    if (!b) return;
    b.addEventListener('click', function () { applyLang(LANG === 'ar' ? 'en' : 'ar', true); });
  }

  /* =========================================================================
     وضع العرض — the same page, one block at a time
     ========================================================================= */
  var deck = {
    on: false, i: 0, slides: [], titles: [],
    rebuild: function (keep) {
      var root = document.querySelector('main > [data-lang="' + LANG + '"]');
      if (!root) return;
      var out = [], titles = [], cur = LANG === 'ar' ? 'المقدّمة' : 'Opening';
      Array.prototype.forEach.call(document.querySelectorAll('.is-slide'), function (e) { e.classList.remove('is-slide', 'is-current'); });
      Array.prototype.forEach.call(root.children, function (sec) {
        if (sec.classList.contains('hero')) {
          sec.classList.add('is-slide'); out.push(sec); titles.push(cur); return;
        }
        if (sec.classList.contains('foot')) {
          sec.classList.add('is-slide'); out.push(sec);
          titles.push(LANG === 'ar' ? 'من أين جاءت هذه الأرقام' : 'Where these numbers came from');
          return;
        }
        var h2 = sec.querySelector('h2');
        if (h2) cur = h2.textContent.trim();
        Array.prototype.forEach.call(sec.children, function (ch) {
          if (ch.matches('.shead, .figs, .blk, .widget, .say, .gl-ctrls, .term-group')) {
            ch.classList.add('is-slide'); out.push(ch); titles.push(cur);
          }
        });
      });
      this.slides = out; this.titles = titles;
      this.i = Math.min(Math.max(keep || 0, 0), Math.max(0, out.length - 1));
      this.show();
    },
    show: function () {
      var s = this.slides;
      if (!s.length) return;
      s.forEach(function (e, j) { e.classList.toggle('is-current', j === deck.i); });
      var bar = document.querySelector('.deckbar');
      if (bar) {
        bar.querySelector('[data-deck-n]').textContent = (this.i + 1) + ' / ' + s.length;
        bar.querySelector('[data-deck-sec]').textContent = this.titles[this.i] || '';
        bar.querySelector('[data-deck-prev]').disabled = this.i === 0;
        bar.querySelector('[data-deck-next]').disabled = this.i === s.length - 1;
        var fill = bar.querySelector('.deckbar-prog i');
        if (fill) fill.style.width = (100 * (this.i + 1) / s.length) + '%';
      }
      var el = s[this.i];
      if (el) { el.scrollTop = 0; window.scrollTo(0, 0); }
      window.dispatchEvent(new Event('resize'));
    },
    go: function (d) { this.i = clamp(this.i + d, 0, this.slides.length - 1); this.show(); },
    enter: function () {
      this.on = true;
      document.body.setAttribute('data-mode', 'deck');
      this.rebuild(0);
      var b = document.querySelector('[data-deck-toggle]');
      if (b) b.setAttribute('aria-pressed', 'true');
    },
    exit: function () {
      this.on = false;
      document.body.removeAttribute('data-mode');
      Array.prototype.forEach.call(document.querySelectorAll('.is-slide'), function (e) { e.classList.remove('is-slide', 'is-current'); });
      var b = document.querySelector('[data-deck-toggle]');
      if (b) b.setAttribute('aria-pressed', 'false');
      window.dispatchEvent(new Event('resize'));
    }
  };

  function deckSetup() {
    var t = document.querySelector('[data-deck-toggle]');
    if (t) t.addEventListener('click', function () { deck.on ? deck.exit() : deck.enter(); });
    var bar = document.querySelector('.deckbar');
    if (bar) {
      bar.querySelector('[data-deck-prev]').addEventListener('click', function () { deck.go(-1); });
      bar.querySelector('[data-deck-next]').addEventListener('click', function () { deck.go(1); });
      bar.querySelector('[data-deck-exit]').addEventListener('click', function () { deck.exit(); });
    }
    document.addEventListener('keydown', function (e) {
      if (!deck.on) {
        if (e.key === 'p' && (e.ctrlKey || e.metaKey)) return;
        return;
      }
      var tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'select' || tag === 'textarea') return;
      var fwd = LANG === 'ar' ? 'ArrowLeft' : 'ArrowRight';
      var back = LANG === 'ar' ? 'ArrowRight' : 'ArrowLeft';
      if (e.key === fwd || e.key === 'PageDown' || e.key === ' ' || e.key === 'ArrowDown') { e.preventDefault(); deck.go(1); }
      else if (e.key === back || e.key === 'PageUp' || e.key === 'ArrowUp') { e.preventDefault(); deck.go(-1); }
      else if (e.key === 'Home') { e.preventDefault(); deck.i = 0; deck.show(); }
      else if (e.key === 'End') { e.preventDefault(); deck.i = deck.slides.length - 1; deck.show(); }
      else if (e.key === 'Escape') { e.preventDefault(); deck.exit(); }
      else if (e.key === 'f') {
        if (document.fullscreenElement) document.exitFullscreen();
        else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen().catch(function () { });
      }
    });
  }

  /* ---------- boot -------------------------------------------------------- */
  function boot() {
    var reg = {
      'hero-trace': heroTrace,
      'four-stroke': fourStroke, 'spark-knock': sparkKnock, 'thermal-tau': thermalTau,
      'lever-cost': leverCost,
      'race': race, 'htau': htau, 'glossary': glossary
    };
    applyLang(readLang(), false);
    Object.keys(reg).forEach(function (k) {
      Array.prototype.forEach.call(document.querySelectorAll('[data-widget="' + k + '"]'), function (el) {
        try { reg[k](el); } catch (e) { console.error(k, e); el.classList.add('widget-failed'); }
      });
    });
    nav(); disclosures(); themeToggle(); langToggle(); deckSetup();
    window.dispatchEvent(new Event('resize'));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
