import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
import { registerModal } from '../modal-stack.mjs';
const source = name => readFileSync(new URL(`../${name}.tsx`, import.meta.url), 'utf8').replaceAll('\r\n', '\n');
function environment() {
  const listeners = new Map();
  const doc = { body: { style: { overflow: 'auto' } }, activeElement: null,
    addEventListener(type, fn) { if (!listeners.has(type)) listeners.set(type, new Set()); listeners.get(type).add(fn); },
    removeEventListener(type, fn) { listeners.get(type)?.delete(fn); } };
  const element = (name, parent = null) => ({ name, parent, isConnected: true, offsetParent: {}, hasAttribute: () => false,
    focus() { doc.activeElement = this; }, contains(other) { return other === this || other?.parent === this; },
    querySelector() { return this.items?.[0]; }, querySelectorAll() { return this.items || []; } });
  const trigger = element('expand'); const scene = element('scene'); const explain = element('explain', scene); const sceneClose = element('scene-close', scene); scene.items = [sceneClose, explain];
  const sheet = element('sheet'); const close = element('sheet-close', sheet); const last = element('sheet-last', sheet); sheet.items = [close, last];
  trigger.focus();
  return { doc, element, trigger, scene, explain, sheet, close, last,
    key(key, shiftKey = false) { const event = { key, shiftKey, prevented: false, preventDefault() { this.prevented = true; } }; for (const fn of [...listeners.get('keydown') || []]) fn(event); return event; } };
}
// Model selector matching and the browser's default Tab separately: a native
// summary participates in sequential focus even without an explicit tabindex.
function detailsEnvironment({ summaryLast = false } = {}) {
  const e = environment();
  const summary = e.element('details-summary', e.sheet);
  const detail = e.element('detail-control', e.sheet);
  const sourceButton = e.element('source-button', e.sheet);
  summary.tagName = 'SUMMARY';
  for (const button of [e.close, detail, sourceButton]) button.tagName = 'BUTTON';
  let open = false;
  Object.defineProperty(detail, 'offsetParent', { get: () => open ? {} : null });
  const nodes = summaryLast ? [e.close, detail, summary] : [e.close, summary, detail, sourceButton];
  e.sheet.querySelectorAll = selector => nodes.filter(node => selector.split(',').some(part => part.trim() === node.tagName.toLowerCase()));
  return { ...e, summary, detail, sourceButton, setOpen(value) { open = value; },
    tab(shiftKey = false) {
      const event = e.key('Tab', shiftKey);
      if (!event.prevented) {
        const sequence = nodes.filter(node => node.offsetParent !== null);
        const next = sequence[sequence.indexOf(e.doc.activeElement) + (shiftKey ? -1 : 1)];
        assert.ok(next, 'native Tab remains within the modal');
        next.focus();
      }
      return event;
    } };
}
test('native summary preserves forward and reverse Tab through expanded details', () => {
  const e = detailsEnvironment(); e.setOpen(true);
  const remove = registerModal(e.doc, { element: e.sheet, onClose() {} });
  e.summary.focus(); assert.equal(e.tab().prevented, false); assert.equal(e.doc.activeElement, e.detail);
  assert.equal(e.tab(true).prevented, false); assert.equal(e.doc.activeElement, e.summary);
  assert.equal(e.tab(true).prevented, false); assert.equal(e.doc.activeElement, e.close);
  e.sourceButton.focus(); assert.equal(e.tab().prevented, true); assert.equal(e.doc.activeElement, e.close);
  remove();
});
test('closed details skip hidden controls and preserve summary to source navigation', () => {
  const e = detailsEnvironment();
  const remove = registerModal(e.doc, { element: e.sheet, onClose() {} });
  e.summary.focus(); assert.equal(e.tab().prevented, false); assert.equal(e.doc.activeElement, e.sourceButton);
  assert.equal(e.tab(true).prevented, false); assert.equal(e.doc.activeElement, e.summary);
  e.close.focus(); assert.equal(e.tab(true).prevented, true); assert.equal(e.doc.activeElement, e.sourceButton);
  remove();
});
test('native summary as last visible control wraps both modal endpoints', () => {
  const e = detailsEnvironment({ summaryLast: true });
  const remove = registerModal(e.doc, { element: e.sheet, onClose() {} });
  e.close.focus(); assert.equal(e.tab(true).prevented, true); assert.equal(e.doc.activeElement, e.summary);
  assert.equal(e.tab().prevented, true); assert.equal(e.doc.activeElement, e.close);
  remove();
});
async function mount(env, kind, onClose, origin) {
  const text = source(kind === 'scene' ? 'Scene' : 'App');
  if (text.includes("from './modal-stack.mjs'")) {
    const { registerModal } = await import('../modal-stack.mjs');
    const start = text.indexOf(kind === 'scene' ? '  useEffect(()=>{\n    if(!expanded' : '  useEffect(() => {\n    if (!compactInspection');
    const end = text.indexOf(kind === 'scene' ? '  },[expanded]);' : '  }, [compactInspection, mode]);', start);
    const effect = text.slice(start, end) + (kind === 'scene' ? '  },[expanded]);' : '  }, [compactInspection, mode]);');
    let cleanup;
    new Function('document', 'useEffect', 'expanded', 'compactInspection', 'mode', 'sceneElement', 'inspectionDialog', 'inspectionOrigin', 'setExpanded', 'setCompactInspection', 'registerModal', ts.transpile(effect, { target: ts.ScriptTarget.ES2022 }))(env.doc, cb => { cleanup = cb(); }, true, true, 'studio', { current: env.scene }, { current: env.sheet }, { current: origin }, onClose, onClose, registerModal);
    return cleanup;
  }
  const start = text.indexOf(kind === 'scene' ? '  useEffect(()=>{\n    if(!expanded' : '  useEffect(() => {\n    if (!compactInspection');
  const end = text.indexOf(kind === 'scene' ? '  },[expanded]);' : '  }, [compactInspection]);', start);
  const effect = text.slice(start, end) + (kind === 'scene' ? '  },[expanded]);' : '  }, [compactInspection]);');
  let cleanup;
  const js = ts.transpile(effect, { target: ts.ScriptTarget.ES2022 });
  new Function('document', 'useEffect', 'expanded', 'compactInspection', 'sceneElement', 'inspectionDialog', 'inspectionOrigin', 'setExpanded', 'setCompactInspection', js)(env.doc, cb => { cleanup = cb(); }, true, true, { current: env.scene }, { current: env.sheet }, { current: origin }, onClose, onClose);
  return cleanup;
}
test('nested Escape closes only inspector, then expanded scene and restores original overflow/focus', async () => {
  const e = environment(); const closed = []; let removeScene, removeSheet;
  removeScene = await mount(e, 'scene', () => { closed.push('scene'); removeScene(); }, e.trigger);
  e.explain.focus();
  removeSheet = await mount(e, 'sheet', () => { closed.push('sheet'); removeSheet(); }, e.explain);
  e.key('Escape'); assert.deepEqual(closed, ['sheet']); assert.equal(e.doc.body.style.overflow, 'hidden'); assert.equal(e.doc.activeElement, e.explain);
  e.key('Escape'); assert.deepEqual(closed, ['sheet', 'scene']); assert.equal(e.doc.body.style.overflow, 'auto'); assert.equal(e.doc.activeElement, e.trigger);
});
test('Tab belongs to top dialog, including focus that started outside it', async () => {
  const e = environment(); const removeScene = await mount(e, 'scene', () => {}, e.trigger); e.explain.focus(); const removeSheet = await mount(e, 'sheet', () => {}, e.explain);
  e.last.focus(); assert.equal(e.key('Tab').prevented, true); assert.equal(e.doc.activeElement, e.close);
  e.explain.focus(); assert.equal(e.key('Tab').prevented, true); assert.equal(e.doc.activeElement, e.close);
  assert.equal(e.key('Tab', true).prevented, true); assert.equal(e.doc.activeElement, e.last);
  removeSheet(); removeScene();
});
test('out-of-order removal preserves lock and focus in active inspector until final close', async () => {
  const e = environment(); const removeScene = await mount(e, 'scene', () => {}, e.trigger); e.explain.focus(); const removeSheet = await mount(e, 'sheet', () => {}, e.explain);
  removeScene(); assert.equal(e.doc.body.style.overflow, 'hidden'); assert.equal(e.doc.activeElement, e.close);
  e.scene.isConnected = false; e.explain.isConnected = false; removeSheet(); assert.equal(e.doc.body.style.overflow, 'auto'); assert.equal(e.doc.activeElement, e.trigger); removeSheet(); removeScene();
});


test('button/backdrop cleanup keeps expanded scene active and traps subsequent Tab', async () => {
  const e = environment(); const removeScene = await mount(e, 'scene', () => {}, e.trigger); e.explain.focus(); const removeSheet = await mount(e, 'sheet', () => {}, e.explain);
  removeSheet(); assert.equal(e.doc.activeElement, e.explain); assert.equal(e.doc.body.style.overflow, 'hidden');
  e.key('Tab'); assert.equal(e.doc.activeElement, e.scene.items[0]);
  removeScene(); assert.equal(e.doc.body.style.overflow, 'auto'); assert.equal(e.doc.activeElement, e.trigger);
});
test('single dialog restores a preexisting hidden overflow value on unmount', async () => {
  const e = environment(); e.doc.body.style.overflow = 'hidden'; const remove = await mount(e, 'sheet', () => {}, e.trigger);
  remove(); assert.equal(e.doc.body.style.overflow, 'hidden'); assert.equal(e.doc.activeElement, e.trigger);
});

async function mountSource(e, onClose) {
  e.sourceCallback = { current: onClose };
  const text = source('Inspector');
  const marker = text.includes("from './modal-stack.mjs'") ? '  useEffect(() => {\n    if (!sourceDialog.current)' : "  useEffect(() => { const key =";
  const start = text.indexOf(marker);
  const endMarker = text.includes("from './modal-stack.mjs'") ? '  }, []);' : '}, [onClose]);';
  const end = text.indexOf(endMarker, start);
  assert.ok(start >= 0 && end >= 0, 'SourceDialog registration effect exists');
  let cleanup;
  const { registerModal } = await import('../modal-stack.mjs');
  new Function('document', 'useEffect', 'onClose', 'closeSource', 'sourceDialog', 'registerModal', ts.transpile(text.slice(start, end) + endMarker, { target: ts.ScriptTarget.ES2022 }))(e.doc, (cb, deps) => { assert.deepEqual(deps, [], 'source registration survives inline callback rerenders'); cleanup = cb(); }, onClose, e.sourceCallback, { current: e.source }, registerModal);
  return cleanup;
}
test('source above inspector owns focus, Tab and each Escape in triple nesting', async () => {
  const e = environment(); e.source = e.element('source'); const sourceClose = e.element('source-close', e.source); e.source.items = [sourceClose];
  const closed = []; let removeScene, removeSheet, removeSource;
  removeScene = await mount(e, 'scene', () => { closed.push('scene'); removeScene(); }, e.trigger);
  e.explain.focus(); removeSheet = await mount(e, 'sheet', () => { closed.push('sheet'); removeSheet(); }, e.explain);
  e.last.focus(); removeSource = await mountSource(e, () => { closed.push('source'); removeSource(); });
  assert.equal(e.doc.activeElement, sourceClose); e.key('Tab'); assert.equal(e.doc.activeElement, sourceClose);
  e.key('Escape'); assert.deepEqual(closed, ['source']); assert.equal(e.doc.activeElement, e.last); assert.equal(e.doc.body.style.overflow, 'hidden');
  e.key('Escape'); assert.deepEqual(closed, ['source', 'sheet']); assert.equal(e.doc.activeElement, e.explain);
  e.key('Escape'); assert.deepEqual(closed, ['source', 'sheet', 'scene']); assert.equal(e.doc.activeElement, e.trigger); assert.equal(e.doc.body.style.overflow, 'auto');
});
test('last removal restores root origin rather than a stale connected background-dialog control', async () => {
  const e = environment(); const removeScene = await mount(e, 'scene', () => {}, e.trigger); e.explain.focus(); const removeSheet = await mount(e, 'sheet', () => {}, e.explain);
  removeScene(); removeSheet(); assert.equal(e.doc.activeElement, e.trigger); assert.equal(e.doc.body.style.overflow, 'auto');
});

test('SourceDialog uses latest close callback without re-registering or reordering its stack entry', async () => {
  const e = environment(); e.source = e.element('source'); e.source.items = [e.element('source-close', e.source)];
  const removeScene = await mount(e, 'scene', () => assert.fail('background closed'), e.trigger);
  const removeSheet = await mount(e, 'sheet', () => assert.fail('inspector closed'), e.explain);
  const removeSource = await mountSource(e, () => assert.fail('stale callback called'));
  let closed = 0; e.sourceCallback.current = () => { closed++; removeSource(); };
  e.key('Escape'); assert.equal(closed, 1); assert.equal(e.doc.body.style.overflow, 'hidden');
  removeSheet(); removeScene(); assert.equal(e.doc.body.style.overflow, 'auto');
});

