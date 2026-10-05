// A fake DOM for the results tab's chart tests under node:test: just enough of
// document.createElementNS / createElement and of an element for
// charts-lib.mjs to build a chart, so a test can read back every attribute,
// every SVG text and every listener without a browser.
//
// NOT a *.test.mjs file, so the glob "static/sim/*.test.mjs" never runs it on
// its own. node --test runs each test file in its own process, so the
// globalThis.document a test installs never reaches another file.

export class FakeEl {
  constructor(tag, ns = null) {
    this.tagName = tag;
    this.namespaceURI = ns;
    this.attrs = {};
    this.children = [];
    this.parentNode = null;
    this.listeners = {};
    this.style = {};
    this.own = '';
    this.hidden = false;
    this.clientWidth = 0;
    this.offsetWidth = 120;
    this.offsetHeight = 60;
    const el = this;
    this.classList = {
      add(...names) {
        const have = el.classes();
        for (const n of names) if (!have.includes(n)) have.push(n);
        el.attrs.class = have.join(' ');
      },
      contains(name) { return el.classes().includes(name); },
    };
  }
  classes() { return String(this.attrs.class || '').split(/\s+/).filter(Boolean); }
  get textContent() { return this.own + this.children.map(c => c.textContent).join(''); }
  set textContent(v) { this.own = String(v); this.children = []; }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  getAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attrs, name) ? this.attrs[name] : null; }
  hasAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attrs, name); }
  appendChild(node) {
    if (node.parentNode) node.remove();
    node.parentNode = this;
    this.children.push(node);
    return node;
  }
  replaceChildren(...nodes) {
    for (const c of this.children) c.parentNode = null;
    this.children = [];
    for (const n of nodes) this.appendChild(n);
  }
  remove() {
    if (!this.parentNode) return;
    const kids = this.parentNode.children;
    kids.splice(kids.indexOf(this), 1);
    this.parentNode = null;
  }
  // Only the two selector shapes charts-lib.mjs uses: ":scope > .class" and
  // ":scope > tag".
  matchesDirect(sel) {
    const m = /^:scope > (\.)?([\w-]+)$/.exec(sel);
    if (!m) throw new Error(`fake DOM: unsupported selector ${sel}`);
    return el => (m[1] ? el.classes().includes(m[2]) : el.tagName === m[2]);
  }
  querySelector(sel) { return this.children.find(this.matchesDirect(sel)) || null; }
  querySelectorAll(sel) { return this.children.filter(this.matchesDirect(sel)); }
  closest(sel) {
    const m = /^\.([\w-]+)$/.exec(sel);
    if (!m) throw new Error(`fake DOM: unsupported selector ${sel}`);
    for (let el = this; el; el = el.parentNode) if (el.classes().includes(m[1])) return el;
    return null;
  }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  removeEventListener(type, fn) {
    this.listeners[type] = (this.listeners[type] || []).filter(f => f !== fn);
  }
  dispatch(type, init = {}) {
    for (const fn of [...(this.listeners[type] || [])]) fn({ type, target: this, ...init });
  }
  getBoundingClientRect() { return { left: 0, top: 0, width: this.clientWidth, height: 0 }; }
  // A text's rendered width, as the test sets it: FakeEl.textWidth(text) or 0.
  getComputedTextLength() {
    return typeof FakeEl.textWidth === 'function' ? FakeEl.textWidth(this.textContent) : 0;
  }
}
FakeEl.textWidth = null;

/** Install globalThis.document; returns it. Its listeners are recorded too. */
export function installFakeDocument() {
  const doc = new FakeEl('#document');
  doc.createElementNS = (ns, tag) => new FakeEl(tag, ns);
  doc.createElement = tag => new FakeEl(tag);
  globalThis.document = doc;
  return doc;
}

/** A chart host: a div of the given width, inside a .rc-chart parent chain. */
export function fakeHost(width, id = 'chart') {
  const host = new FakeEl('div');
  host.setAttribute('class', 'rc-chart');
  host.setAttribute('id', id);
  host.id = id;
  host.clientWidth = width;
  return host;
}

/** Every element under `node` (itself included), in document order. */
export function walk(node, out = []) {
  out.push(node);
  for (const c of node.children) walk(c, out);
  return out;
}

/** The text of every SVG <text> under `node`, in document order. */
export function svgTexts(node) {
  return walk(node).filter(el => el.tagName === 'text').map(el => el.textContent);
}
