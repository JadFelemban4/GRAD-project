// The project map: every concept in content.json as a node, every upstream and
// downstream link as an arrow from cause to effect. The links come from the
// content files; only the grouping below is written here, and
// concept-map.test.mjs fails when a concept has no group.

export const GROUPS = [
  { id: 'road', ar: 'الطريق والسيناريو', en: 'Road and scenario' },
  { id: 'engine', ar: 'المحرك والاحتراق', en: 'Engine and combustion' },
  { id: 'air', ar: 'الهواء والعادم والتيربو', en: 'Air, exhaust and turbo' },
  { id: 'thermal', ar: 'الحرارة والضرر', en: 'Heat and damage' },
  { id: 'supervisor', ar: 'المشرف والمكافأة', en: 'Supervisor and reward' },
  { id: 'preview', ar: 'الرؤية المسبقة والسؤال البحثي', en: 'Preview and the research question' },
];

export const GROUP_OF = {
  grade: 'road', speed: 'road', scenario: 'road', aggression: 'road', torque_req: 'road', gear: 'road', ambient_temp: 'road', barometric_pressure: 'road', humidity: 'road',
  engine: 'engine', four_stroke: 'engine', rpm: 'engine', map: 'engine', tps: 'engine', lam: 'engine', fuel: 'engine', spark: 'engine', combustion: 'engine', knock: 'engine', engine_torque: 'engine', map_reference: 'engine',
  turbocharger: 'air', air: 'air', charge_temp: 'air', exhaust_flow: 'air', egt: 'air',
  t_block: 'thermal', t_oil: 'thermal', t_turb: 'thermal', thermal_time_constant: 'thermal', fan_duty: 'thermal', pump_duty: 'thermal', damage: 'thermal',
  agent: 'supervisor', baseline_ecu: 'supervisor', normalized_actions: 'supervisor', policy_action: 'supervisor', spark_trim: 'supervisor', lambda_trim: 'supervisor', boost_trim: 'supervisor', r_fuel: 'supervisor', r_life: 'supervisor', r_resp: 'supervisor', policy_reward: 'supervisor', constraint_costs: 'supervisor', weight_tracking: 'supervisor', weight_fuel: 'supervisor', weight_life: 'supervisor', diagnostic_frame: 'supervisor',
  preview: 'preview', preview_2s: 'preview', preview_5s: 'preview', preview_15s: 'preview', preview_30s: 'preview', h_over_tau: 'preview', preview_result: 'preview', research_claim: 'preview', measured_vs_modelled: 'preview',
};

// Nodes and directed edges. A link written on either end counts once.
export function buildGraph(concepts) {
  const ids = new Set(concepts.map(c => c.id));
  const seen = new Set();
  const edges = [];
  const add = (from, to) => {
    const key = from + '>' + to;
    if (from === to || seen.has(key) || !ids.has(from) || !ids.has(to)) return;
    seen.add(key);
    edges.push({ from, to });
  };
  for (const c of concepts) {
    for (const u of c.upstream || []) add(u, c.id);
    for (const d of c.downstream || []) add(c.id, d);
  }
  const degree = Object.fromEntries(concepts.map(c => [c.id, 0]));
  for (const e of edges) { degree[e.from]++; degree[e.to]++; }
  const nodes = concepts.map(c => ({ id: c.id, name: c.name, group: GROUP_OF[c.id] || 'preview', degree: degree[c.id], evidence: c.evidence_class || c.evidence || '' }));
  return { nodes, edges };
}

export const causesOf = (graph, id) => graph.edges.filter(e => e.to === id).map(e => e.from);
export const effectsOf = (graph, id) => graph.edges.filter(e => e.from === id).map(e => e.to);
export const radiusOf = (node) => 4 + Math.sqrt(node.degree) * 2.2;

// A deterministic force layout: groups start on a ring, linked nodes pull
// together, every pair pushes apart, and each node is pulled gently toward
// its group's anchor so the six parts of the project read as regions. Pushing
// stops past `reach` spacings, so a lightly linked node is not flung to the
// edge and the rest squeezed into the middle (median gap 36 -> 51 units).
export function layout(graph, { width = 1000, height = 640, iterations = 420, pad = 48, ring = 0.34, pull = 2, reach = 2 } = {}) {
  let seed = 20261030;
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  const anchors = Object.fromEntries(GROUPS.map((g, i) => {
    const a = -Math.PI / 2 + (i / GROUPS.length) * Math.PI * 2;
    return [g.id, [width / 2 + Math.cos(a) * width * ring, height / 2 + Math.sin(a) * height * ring]];
  }));
  const at = graph.nodes.map(n => { const [ax, ay] = anchors[n.group]; return { x: ax + (random() - 0.5) * 80, y: ay + (random() - 0.5) * 80 }; });
  const index = Object.fromEntries(graph.nodes.map((n, i) => [n.id, i]));
  const k = Math.sqrt((width * height) / graph.nodes.length) * 0.62;
  let heat = width / 9;
  for (let step = 0; step < iterations; step++) {
    const move = at.map(() => ({ x: 0, y: 0 }));
    for (let i = 0; i < at.length; i++) {
      for (let j = i + 1; j < at.length; j++) {
        let dx = at[i].x - at[j].x, dy = at[i].y - at[j].y;
        const d = Math.max(1, Math.hypot(dx, dy));
        if (d > reach * k) continue;
        const push = (k * k) / d;
        dx /= d; dy /= d;
        move[i].x += dx * push; move[i].y += dy * push;
        move[j].x -= dx * push; move[j].y -= dy * push;
      }
    }
    for (const e of graph.edges) {
      const a = index[e.from], b = index[e.to];
      let dx = at[a].x - at[b].x, dy = at[a].y - at[b].y;
      const d = Math.max(1, Math.hypot(dx, dy));
      const pull = (d * d) / k;
      dx /= d; dy /= d;
      move[a].x -= dx * pull; move[a].y -= dy * pull;
      move[b].x += dx * pull; move[b].y += dy * pull;
    }
    graph.nodes.forEach((n, i) => {
      const [ax, ay] = anchors[n.group];
      move[i].x += (ax - at[i].x) * pull;
      move[i].y += (ay - at[i].y) * pull;
      const d = Math.max(1, Math.hypot(move[i].x, move[i].y));
      at[i].x += (move[i].x / d) * Math.min(d, heat);
      at[i].y += (move[i].y / d) * Math.min(d, heat);
    });
    heat = Math.max(1.5, heat * 0.985);
  }
  // Keep every pair of circles apart, then fit the drawing into the frame.
  for (let pass = 0; pass < 60; pass++) {
    for (let i = 0; i < at.length; i++) {
      for (let j = i + 1; j < at.length; j++) {
        const gap = radiusOf(graph.nodes[i]) + radiusOf(graph.nodes[j]) + 16;
        const dx = at[j].x - at[i].x, dy = at[j].y - at[i].y;
        const d = Math.hypot(dx, dy) || 0.01;
        if (d < gap) {
          const shift = (gap - d) / 2;
          at[i].x -= (dx / d) * shift; at[i].y -= (dy / d) * shift;
          at[j].x += (dx / d) * shift; at[j].y += (dy / d) * shift;
        }
      }
    }
  }
  const xs = at.map(p => p.x), ys = at.map(p => p.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const scale = Math.min((width - pad * 2) / (x1 - x0 || 1), (height - pad * 2) / (y1 - y0 || 1));
  const ox = (width - (x1 - x0) * scale) / 2, oy = (height - (y1 - y0) * scale) / 2;
  return Object.fromEntries(graph.nodes.map((n, i) => [n.id, { x: ox + (at[i].x - x0) * scale, y: oy + (at[i].y - y0) * scale }]));
}

// Search over the current language's names and the ids.
export function searchNodes(graph, query, limit = 6) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return graph.nodes
    .map(n => ({ n, at: Math.min(...[n.name.toLowerCase().indexOf(q), n.id.indexOf(q)].map(i => (i < 0 ? 999 : i))) }))
    .filter(r => r.at < 999)
    .sort((a, b) => a.at - b.at || b.n.degree - a.n.degree)
    .slice(0, limit)
    .map(r => r.n);
}
