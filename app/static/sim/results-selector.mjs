// Selection helpers for /results. A new arrival never changes a valid choice;
// a deleted choice falls back deterministically to the first evaluation.
export function resolveChoice(choices, currentId, hash = '') {
  const ids = new Set(choices.map(choice => choice.id));
  if (ids.has(currentId)) return currentId;
  const decoded = parseSelectionHash(hash, choices);
  if (decoded) return decoded.primary;
  const linked = hash.startsWith('#') ? hash.slice(1) : hash;
  if (ids.has(linked)) return linked;
  return choices.find(choice => choice.type === 'evaluation' && choice.section?.state === 'ok')?.id
    || choices.find(choice => choice.type === 'evaluation')?.id
    || choices.find(choice => choice.type === 'agent_set' && choice.ready)?.id
    || choices[0]?.id || '';
}

const decode = value => {
  try { return decodeURIComponent(value); } catch { return null; }
};

export function parseSelectionHash(hash, choices) {
  const fragment = typeof hash === 'string' && hash.startsWith('#') ? hash.slice(1) : '';
  if (fragment.startsWith('compare:')) {
    const parts = fragment.slice('compare:'.length).split(':');
    if (parts.length !== 2) return null;
    const [primary, compare] = parts.map(decode);
    const primaryChoice = choices.find(choice => choice.id === primary && choice.type === 'evaluation');
    const compareChoice = choices.find(choice => choice.id === compare && choice.type === 'evaluation');
    return primaryChoice && compareChoice && primary !== compare
      ? { primary, compare, compareEnabled: true } : null;
  }
  if (fragment.startsWith('set:')) {
    const id = decode(fragment.slice('set:'.length));
    const choice = choices.find(item => item.type === 'agent_set' && item.item.id === id);
    return choice ? { primary: choice.id, compare: '', compareEnabled: false } : null;
  }
  const id = decode(fragment);
  const choice = choices.find(item => ['evaluation','reference'].includes(item.type) && item.id === id);
  return choice ? { primary: choice.id, compare: '', compareEnabled: false } : null;
}

export function selectionHash(primaryId, compareId, choices) {
  const primary = choices.find(choice => choice.id === primaryId);
  if (!primary) return '';
  if (primary.type === 'agent_set') return `#set:${encodeURIComponent(primary.item.id)}`;
  const compare = choices.find(choice => choice.id === compareId && choice.type === 'evaluation');
  if (compare && compare.id !== primary.id) {
    return `#compare:${encodeURIComponent(primary.id)}:${encodeURIComponent(compare.id)}`;
  }
  return `#${primary.id}`;
}

export function selectedSections(sections, primaryId, compareId = '') {
  const byId = new Map(sections.map(section => [section.id, section]));
  const selected = [];
  if (byId.has(primaryId)) selected.push(byId.get(primaryId));
  if (compareId && compareId !== primaryId && byId.has(compareId)) selected.push(byId.get(compareId));
  return selected;
}
