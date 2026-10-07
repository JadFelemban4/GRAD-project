import { commandChains } from './supervisor.mjs';
import { buildProjectStory } from './project-story.mjs';
export function resolveReading(context, options) {
  if (!context || !options.sessionId || context.sessionId !== options.sessionId || context.conceptId !== options.conceptId) return null;
  const story = buildProjectStory(options.frame, options);
  const [collection, key, member] = context.field.split('.');
  let value = story[collection];
  if (collection === 'chains') value = commandChains(options.frame).find(item=>item.id===key)?.[member];
  else if (collection === 'memory') value = story.memory.find(item => item.id === key)?.[member];
  else if (collection === 'controls') value = story.controls.find(item => item.id === key)?.value;
  else if (collection === 'previewSlots') value = story.previewSlots[Number(key)]?.gradePct;
  else if (key) value = value?.[key];
  return { ...context, value: typeof value === 'number' && Number.isFinite(value) ? value : null, inputS: story.timeline.inputS, endS: story.timeline.endS };
}
