/** Scene source ownership and component lifetime must use the same predicate. */
export function thermalContext(mode, layer, panel, studioEnabled) {
  const active = panel !== 'results' && layer === 'thermal' && (mode === 'studio' ? studioEnabled : panel === 'thermal');
  return { active, mount: active, key: `thermal-${mode}` };
}
export function shouldSwitchMode(currentMode, nextMode, panel) {
  return currentMode !== nextMode || panel === 'results';
}
