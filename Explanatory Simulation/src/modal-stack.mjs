// A single owner per document keeps nested dialogs and body scrolling in sync.
const documents = new WeakMap();
const focusable = element => [...element.querySelectorAll('button, summary, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])')]
  .filter(item => item.offsetParent !== null && !item.hasAttribute('disabled') && item.getAttribute?.('aria-hidden') !== 'true');
const focusFirst = entry => (focusable(entry.element)[0] || entry.element).focus();
export function registerModal(doc, { element, onClose, returnFocus = doc.activeElement }) {
  let state = documents.get(doc);
  if (!state) {
    state = { entries: [], overflow: doc.body.style.overflow, origin: returnFocus };
    state.key = event => {
      const top = state.entries.at(-1);
      if (!top) return;
      if (event.key === 'Escape') { event.preventDefault(); top.onClose(); }
      if (event.key === 'Tab') {
        const items = focusable(top.element), first = items[0], last = items.at(-1);
        if (!items.length) { event.preventDefault(); top.element.focus(); }
        else if (!top.element.contains(doc.activeElement) || !items.includes(doc.activeElement)) { event.preventDefault(); (event.shiftKey ? last : first).focus(); }
        else if (event.shiftKey && doc.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && doc.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    };
    state.focus = event => { const top = state.entries.at(-1); if (top && !top.element.contains(event.target)) focusFirst(top); };
    documents.set(doc, state);
    doc.body.style.overflow = 'hidden';
    doc.addEventListener('keydown', state.key);
    doc.addEventListener('focusin', state.focus);
  }
  const entry = { element, onClose, returnFocus };
  state.entries.push(entry);
  focusFirst(entry);
  let removed = false;
  return () => {
    if (removed) return;
    removed = true;
    const wasTop = state.entries.at(-1) === entry;
    state.entries.splice(state.entries.indexOf(entry), 1);
    const top = state.entries.at(-1);
    if (top) {
      if (wasTop) {
        if (returnFocus?.isConnected && top.element.contains(returnFocus)) returnFocus.focus();
        else focusFirst(top);
      }
    } else {
      doc.removeEventListener('keydown', state.key);
      doc.removeEventListener('focusin', state.focus);
      doc.body.style.overflow = state.overflow;
      documents.delete(doc);
      const target = state.origin;
      if (target?.isConnected) target.focus();
    }
  };
}

