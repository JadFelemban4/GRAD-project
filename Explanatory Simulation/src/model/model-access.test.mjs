import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';

// Execute the real App handlers without mounting physics or starting a session.
function handler(name, scope) {
  const source = readFileSync(new URL('../App.tsx', import.meta.url), 'utf8');
  const tree = ts.createSourceFile('App.tsx', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  let found;
  const visit = node => { if (ts.isFunctionDeclaration(node) && node.name?.text === name) found = node; ts.forEachChild(node, visit); };
  visit(tree);
  assert.ok(found, `Production navigation handler ${name} exists`);
  const emitted = ts.transpileModule(found.getText(tree), { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;
  return Function('scope', `with(scope) { ${emitted}; return ${name}; }`)(scope);
}
function destination() {
  const effects = [];
  return { effects, focus(options) { effects.push({ type: 'focus', ...options }); }, scrollIntoView(options) { effects.push({ type: 'reveal', ...options }); } };
}
function browser(reduced) {
  return { matchMedia(query) { assert.equal(query, '(prefers-reduced-motion: reduce)'); return { matches: reduced }; } };
}

test('model action focuses the viewing area and reveals it without a simulation step', () => {
  const modelViewport = destination();
  const session = { id: 'existing', time: 17, draft: [2, 0, 5, .4, .5] };
  const before = structuredClone(session);
  handler('showModel', { modelViewport, session, window: browser(false), api() { assert.fail('Navigation must not call simulation API'); } })();
  assert.equal(modelViewport.effects[0].type, 'focus');
  assert.equal(modelViewport.effects[0].preventScroll, true);
  assert.equal(modelViewport.effects[1].type, 'reveal');
  assert.equal(modelViewport.effects[1].block, 'center');
  assert.equal(modelViewport.effects[1].behavior, 'smooth');
  assert.deepEqual(session, before);
});

test('reduced motion reaches both model and explanation without animated scrolling', () => {
  const modelViewport = destination(), action = destination();
  const scope = { modelViewport, journeyAction: { current: action }, window: browser(true) };
  handler('showModel', scope)();
  handler('returnToJourney', scope)();
  for (const target of [modelViewport, action]) {
    assert.equal(target.effects[0].preventScroll, true);
    assert.equal(target.effects[1].behavior, 'instant');
  }
});

test('unready or removed targets leave navigation idle', () => {
  const scope = { modelViewport: null, journeyAction: { current: null }, window: { matchMedia() { assert.fail('No target, no navigation'); } } };
  handler('showModel', scope)();
  handler('returnToJourney', scope)();
});
