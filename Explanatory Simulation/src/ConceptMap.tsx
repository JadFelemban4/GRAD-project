import { useEffect, useMemo, useRef, useState } from 'react';
import { Code2, RotateCcw, Search } from 'lucide-react';
import { usePreferences } from './Preferences';
import { Evidence } from './Inspector';
import type { Meta } from './types';
import { GROUPS, buildGraph, causesOf, effectsOf, layout, radiusOf, searchNodes } from './model/concept-map.mjs';
import './concept-map.css';
const W = 1000, H = 640;
type View = { x: number; y: number; k: number };
const HOME: View = { x: 0, y: 0, k: 1 };
/** The project map: every concept as a node, every upstream/downstream link as an arrow from cause to effect, drawn from content.json. */
export default function ConceptMap({ meta, onSelect, onSource }: { meta: Meta; onSelect: (id: string) => void; onSource: (source: any) => void }) {
  const { t, language } = usePreferences();
  const graph = useMemo(() => buildGraph(meta.concepts), [meta]);
  const at = useMemo(() => layout(graph, { width: W, height: H }), [graph]);
  const byId = useMemo(() => Object.fromEntries(graph.nodes.map((n: any) => [n.id, n])), [graph]);
  const [selected, setSelected] = useState('');
  const [hover, setHover] = useState('');
  const [group, setGroup] = useState('');
  const [query, setQuery] = useState('');
  const [view, setView] = useState<View>(HOME);
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{ x: number; y: number; view: View; moved: boolean } | null>(null);
  const active = hover || selected;
  const near = useMemo(() => new Set(active ? [active, ...causesOf(graph, active), ...effectsOf(graph, active)] : []), [graph, active]);
  const found = useMemo(() => searchNodes(graph, query), [graph, query]);
  const concept = meta.concepts.find(c => c.id === selected);
  const groupName = (id: string) => { const g = GROUPS.find(g => g.id === id); return g ? (language === 'ar' ? g.ar : g.en) : ''; };
  const local = (event: { clientX: number; clientY: number }) => { const m = svg.current?.getScreenCTM(); return m ? new DOMPoint(event.clientX, event.clientY).matrixTransform(m.inverse()) : new DOMPoint(); };
  useEffect(() => {
    const el = svg.current;
    if (!el) return;
    const wheel = (event: WheelEvent) => {
      event.preventDefault();
      const p = local(event);
      setView(v => { const k = Math.min(4, Math.max(0.6, v.k * (event.deltaY < 0 ? 1.15 : 1 / 1.15))); return { k, x: p.x - ((p.x - v.x) * k) / v.k, y: p.y - ((p.y - v.y) * k) / v.k }; });
    };
    el.addEventListener('wheel', wheel, { passive: false });
    return () => el.removeEventListener('wheel', wheel);
  }, []);
  function choose(id: string, center = false) {
    setSelected(id);
    setQuery('');
    onSelect(id);
    if (center) { const p = at[id]; const k = Math.max(view.k, 1.6); setView({ k, x: W / 2 - p.x * k, y: H / 2 - p.y * k }); }
  }
  const chips = (ids: string[]) => ids.length ? ids.map(id => <button key={id} type="button" data-group={byId[id].group} onClick={() => choose(id, true)}><i/>{byId[id].name}</button>) : <span className="concept-map__none">{t('لا شيء', 'None')}</span>;
  const lit = (id: string) => (!active || near.has(id)) && (!group || byId[id].group === group);
  // Names go below their node, or above when below is taken; a name with no room waits for the pointer.
  const labels = useMemo(() => {
    const focused = !!active || !!group;
    const wanted = graph.nodes.filter((n: any) => focused ? lit(n.id) : n.degree >= 7 || view.k >= 1.7);
    wanted.sort((a: any, b: any) => Number(b.id === active) - Number(a.id === active) || Number(near.has(b.id)) - Number(near.has(a.id)) || b.degree - a.degree);
    const placed: { x0: number; x1: number; y0: number; y1: number }[] = [];
    const out: Record<string, number> = {};
    for (const n of wanted as any[]) {
      const p = at[n.id], r = radiusOf(n), half = (n.name.length * 7) / 2;
      for (const dy of [r + 13, -r - 6]) {
        const box = { x0: p.x - half, x1: p.x + half, y0: p.y + dy - 12, y1: p.y + dy + 3 };
        if (placed.some(q => box.x0 < q.x1 && box.x1 > q.x0 && box.y0 < q.y1 && box.y1 > q.y0)) continue;
        placed.push(box); out[n.id] = dy; break;
      }
    }
    return out;
  }, [graph, at, near, view.k, group, active]);
  return <section className="concept-map" aria-label={t('خريطة المشروع', 'Project map')}>
    <header className="concept-map__head">
      <div><span className="small-label">{t('خريطة المشروع', 'Project map')}</span><h1>{t('كل براميتر، ومن يؤثر فيه، وعلى من يؤثر', 'Every parameter, what moves it, and what it moves')}</h1>
        <p>{t('السهم يمشي من السبب إلى الأثر. الروابط مأخوذة من مفاهيم المختبر نفسها. اضغط نقطة لتقرأ عنها، أو ابحث بالاسم.', 'Arrows run from cause to effect. The links are the lab’s own concept links. Click a node to read about it, or search by name.')}</p></div>
      <div className="concept-map__search"><Search size={16}/><input type="search" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && found[0]) choose(found[0].id, true); if (e.key === 'Escape') setQuery(''); }} placeholder={t('ابحث: التوربين، الشرارة، H/τ…', 'Search: turbine, spark, H/τ…')} aria-label={t('ابحث عن براميتر', 'Search for a parameter')}/>
        {found.length > 0 && <ul role="listbox">{found.map((n: any) => <li key={n.id}><button type="button" onClick={() => choose(n.id, true)} data-group={n.group}><i/>{n.name}<small dir="ltr">{n.id}</small></button></li>)}</ul>}</div>
    </header>
    <div className="concept-map__body">
      <div className="concept-map__canvas">
        <svg ref={svg} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={t(`خريطة ${graph.nodes.length} مفهومًا و${graph.edges.length} رابطًا من السبب إلى الأثر`, `A map of ${graph.nodes.length} concepts and ${graph.edges.length} cause-to-effect links`)}
          onPointerDown={e => { if ((e.target as Element).closest('.concept-map__node')) return; drag.current = { x: e.clientX, y: e.clientY, view, moved: false }; (e.currentTarget as Element).setPointerCapture(e.pointerId); }}
          onPointerMove={e => { const d = drag.current; if (!d) return; const a = local(e), b = local({ clientX: d.x, clientY: d.y }); if (Math.abs(e.clientX - d.x) + Math.abs(e.clientY - d.y) > 3) d.moved = true; setView({ ...d.view, x: d.view.x + a.x - b.x, y: d.view.y + a.y - b.y }); }}
          onPointerUp={() => { const d = drag.current; drag.current = null; if (d && !d.moved) { setSelected(''); setGroup(''); } }}>
          <defs><marker id="concept-map-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z"/></marker></defs>
          <g transform={`translate(${view.x} ${view.y}) scale(${view.k})`}>
            {graph.edges.map((e: any) => {
              const a = at[e.from], b = at[e.to]; const d = Math.hypot(b.x - a.x, b.y - a.y) || 1;
              const ra = radiusOf(byId[e.from]) + 2, rb = radiusOf(byId[e.to]) + 3;
              const on = active && (e.from === active || e.to === active);
              const dim = (active && !on) || (group && byId[e.from].group !== group && byId[e.to].group !== group);
              return <line key={e.from + '>' + e.to} className={`concept-map__edge${on ? ' is-on' : ''}${dim ? ' is-dim' : ''}`} data-way={on ? (e.to === active ? 'cause' : 'effect') : undefined}
                x1={a.x + ((b.x - a.x) * ra) / d} y1={a.y + ((b.y - a.y) * ra) / d} x2={b.x - ((b.x - a.x) * rb) / d} y2={b.y - ((b.y - a.y) * rb) / d} markerEnd={on ? 'url(#concept-map-arrow)' : undefined}/>;
            })}
            {graph.nodes.map((n: any) => {
              const p = at[n.id]; const r = radiusOf(n);
              const dy = labels[n.id] ?? (n.id === hover ? r + 13 : undefined);
              return <g key={n.id} className={`concept-map__node${lit(n.id) ? '' : ' is-dim'}${n.id === selected ? ' is-selected' : ''}`} data-group={n.group} data-id={n.id} transform={`translate(${p.x} ${p.y})`}
                onPointerEnter={() => setHover(n.id)} onPointerLeave={() => setHover('')} onClick={() => choose(n.id)}>
                <circle className="concept-map__halo" r={r + 5}/><circle className="concept-map__dot" r={r}/>
                {dy !== undefined && <text y={dy} textAnchor="middle" direction={language === 'ar' ? 'rtl' : 'ltr'}>{n.name}</text>}
              </g>;
            })}
          </g>
        </svg>
        <div className="concept-map__tools"><button type="button" onClick={() => setView(HOME)} aria-label={t('أعد المنظور', 'Reset the view')}><RotateCcw size={15}/></button><span>{t('اسحب للتحريك · العجلة للتكبير', 'Drag to move · wheel to zoom')}</span></div>
      </div>
      <aside className="concept-map__side">
        <ul className="concept-map__legend" aria-label={t('أجزاء المشروع', 'Parts of the project')}>{GROUPS.map(g => <li key={g.id}><button type="button" data-group={g.id} aria-pressed={group === g.id} onClick={() => setGroup(group === g.id ? '' : g.id)}><i/>{language === 'ar' ? g.ar : g.en}<small dir="ltr">{graph.nodes.filter((n: any) => n.group === g.id).length}</small></button></li>)}</ul>
        {concept ? <div className="concept-map__card">
          <span className="small-label">{groupName(byId[concept.id].group)}</span>
          <h2>{concept.name} <Evidence value={(concept as any).evidence_class || concept.evidence}/></h2>
          <p>{concept.meaning}</p>
          <h3>{t('يتأثر بـ', 'Moved by')}</h3><div className="concept-map__chips">{chips(causesOf(graph, concept.id))}</div>
          <h3>{t('يؤثر في', 'Moves')}</h3><div className="concept-map__chips">{chips(effectsOf(graph, concept.id))}</div>
          {(concept as any).source?.file && <button type="button" className="concept-map__source" onClick={() => onSource((concept as any).source)}><Code2 size={14}/>{t('افتح مكانه في الشيفرة', 'Open it in the code')} <bdi dir="ltr">{(concept as any).source.file}</bdi></button>}
        </div> : <p className="concept-map__hint">{t('اضغط أي نقطة: تضيء أسبابها وآثارها، ويظهر هنا معناها ومكانها في الشيفرة. اضغط لونًا في القائمة لترى جزءًا واحدًا من المشروع.', 'Click any node: its causes and effects light up, and its meaning and place in the code appear here. Click a colour in the list to see one part of the project.')}</p>}
      </aside>
    </div>
  </section>;
}
