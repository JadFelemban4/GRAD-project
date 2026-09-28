// A fake page for running agents.mjs under node:test: a DOM holding only the
// ids a test names, a window whose address the test chooses, a history that
// records every replaceState, and a fetch whose every request waits until the
// test answers it, so the order of events is the test's.
//
// NOT a *.test.mjs file, so the glob "app/static/sim/*.test.mjs" never runs it
// on its own. Each test file that imports it owns its own process (node --test
// runs every file in one), and agents.mjs boots once, on import, in it:
//
//   const h = installFakePage({ search: '', ids: ['compute', ...] });
//   await import('./agents.mjs');
//
// Every id not listed is null, which agents.mjs tolerates. Do NOT list
// 'profile' or 'chase' unless the test is about them: FakeNode.querySelector
// returns null, and drawProfile would then fail on the car marker.
import { registerHooks } from 'node:module';

// The page loads its chase view with import('./agent-scene.mjs'), which needs
// Three.js and WebGL. In this process that one import resolves to a stand-in,
// whose behaviour each test sets through globalThis.chaseFake. The chase view
// is mounted only where a test puts a #chase node in the fake DOM.
const FAKE_SCENE = `data:text/javascript,${encodeURIComponent(`
export function createChaseScene() {
  const fake = globalThis.chaseFake;
  if (fake.fail) throw new Error(fake.fail);
  const scene = { disposed: false, update() {}, setTheme() {}, dispose() { scene.disposed = true; } };
  fake.scenes.push(scene);
  if (fake.onCreate) fake.onCreate();
  return scene;
}`)}`;

export class FakeNode {
  constructor(tag) {
    this.tagName = tag;
    this.children = [];
    this.own = '';
    this.hidden = false;
    this.disabled = false;
    this.className = '';
    this.value = '';
    this.dataset = {};
    this.style = {};
    this.attrs = {};
    this.listeners = {};
  }
  get textContent() { return this.own + this.children.map(c => c.textContent).join(''); }
  set textContent(v) { this.own = String(v); this.children = []; }
  appendChild(node) { this.children.push(node); return node; }
  append(...nodes) { this.children.push(...nodes); }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  getAttribute(name) { return name in this.attrs ? this.attrs[name] : null; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  fire(type) { for (const fn of this.listeners[type] || []) fn(); }
  click() { this.fire('click'); }
  querySelector() { return null; }
  querySelectorAll() { return []; }
}

// Every node under `node` whose class list holds `name`.
export function byClass(node, name, out = []) {
  if (String(node.className).split(' ').includes(name)) out.push(node);
  for (const child of node.children) byClass(child, name, out);
  return out;
}

const SELECTS = new Set(['pick-experiment', 'pick-pair', 'pick-episode', 'rate']);

/**
 * Install the fake page. `search` is window.location.search; `ids` are the
 * elements that exist. Returns the handles a test drives it with.
 */
export function installFakePage({ search = '', ids = [] } = {}) {
  registerHooks({
    resolve(specifier, context, next) {
      if (specifier === './agent-scene.mjs' && String(context.parentURL).endsWith('/agents.mjs')) {
        return { url: FAKE_SCENE, shortCircuit: true };
      }
      return next(specifier, context);
    },
  });
  globalThis.chaseFake = { fail: null, scenes: [], onCreate: null };

  const nodes = Object.fromEntries(ids.map(id => [id, new FakeNode(SELECTS.has(id) ? 'select' : 'div')]));
  const history = [];
  globalThis.document = {
    documentElement: new FakeNode('html'),
    activeElement: null,
    getElementById: id => nodes[id] || null,
    createElement: tag => new FakeNode(tag),
    querySelector: () => null,
    querySelectorAll: () => [],
  };
  globalThis.window = {
    location: { search },
    matchMedia: () => ({ matches: false }),
    history: { replaceState: (data, title, url) => { history.push(String(url)); } },
  };
  globalThis.getComputedStyle = () => ({ getPropertyValue: () => '' });
  globalThis.requestAnimationFrame = () => 0;

  // Each request waits until the test answers it, so the order is the test's.
  // `init` is fetch's second argument as the page passed it (method, headers,
  // body), so a test can read what a POST sent.
  const requests = [];
  let arrived = null;
  globalThis.fetch = (url, init = {}) => new Promise((resolve, reject) => {
    requests.push({ url: String(url), init, resolve, reject });
    if (arrived) { arrived(); arrived = null; }
  });
  // A request the page never sends fails the test after `ms` instead of
  // hanging the whole file.
  async function nextRequest(ms = 3000) {
    const deadline = Date.now() + ms;
    while (!requests.length) {
      const left = deadline - Date.now();
      if (left <= 0) throw new Error(`no request arrived within ${ms} ms`);
      await new Promise(resolve => {
        const timer = setTimeout(resolve, left);
        arrived = () => { clearTimeout(timer); resolve(); };
      });
    }
    return requests.shift();
  }
  const reply = (req, body, status = 200) => req.resolve({ status, json: async () => body });
  const fail = (req, error = new TypeError('Failed to fetch')) => req.reject(error);
  const settle = () => new Promise(resolve => setTimeout(resolve, 20));
  function seekTo(time) {
    nodes.seek.value = String(time);
    nodes.seek.fire('input');
  }
  // What a viewer's choice in a <select> does: the value changes, then 'change'.
  function change(node, value) {
    node.value = String(value);
    node.fire('change');
  }
  return { nodes, history, requests, nextRequest, reply, fail, settle, seekTo, change };
}
