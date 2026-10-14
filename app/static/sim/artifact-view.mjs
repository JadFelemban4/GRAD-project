// Pure artifact display labels. The caller owns rendering and API requests.
import { t } from './i18n.mjs';
import './artifact-strings.mjs';

const LIFECYCLES = ['running', 'finalizing', 'finished', 'interrupted'];
const EVIDENCE = ['model', 'training_curve', 'training_record', 'evaluation_summary', 'evaluation_record', 'verdict'];
const KIND_KEYS = new Set(['run_pair', 'evaluation_text', 'agent_set']);

const displayValue = value => {
  if (value === null || value === undefined || value === '') return '—';
  if (Array.isArray(value)) return value.map(displayValue).join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
};

function reasonOf(item) {
  const compatibility = item?.compatibility;
  return compatibility && typeof compatibility === 'object'
    ? compatibility.reason
    : compatibility;
}

function issueText(issues) {
  if (issues == null) return [];
  return (Array.isArray(issues) ? issues : [issues]).map(displayValue).filter(Boolean);
}

/** Return localized source, lifecycle, evidence, compatibility, and issue text. */
export function itemView(item, lang) {
  const kind = KIND_KEYS.has(item?.kind) ? item.kind : 'run_pair';
  const lifecycle = LIFECYCLES.includes(item?.lifecycle) ? item.lifecycle : 'unknown';
  const files = Array.isArray(item?.source_files) ? item.source_files.filter(Boolean).map(displayValue) : [];
  const path = displayValue(item?.relative_path ?? item?.id);
  const source = `${t(lang, `artifact.kind.${kind}`)} · ${t(lang, 'artifact.source', { path })}${files.length ? ` · ${files.join(', ')}` : ''}`;
  const capabilities = item?.capabilities ?? {};
  let availability = EVIDENCE.map(name => t(lang,
    `artifact.evidence.${capabilities[name] === true ? 'available' : 'unavailable'}`,
    { name: t(lang, `artifact.evidence.${name}`) })).join(' · ');
  if (kind === 'agent_set') availability += ` · ${t(lang, 'artifact.reader.pending')}`;

  const refusalReason = reasonOf(item);
  const compatibility = item?.compatibility?.replay_allowed === true
    ? t(lang, 'artifact.compatibility.allowed')
    : item?.compatibility?.replay_allowed === false && refusalReason
      ? t(lang, 'artifact.compatibility.refused', { reason: displayValue(refusalReason) })
      : t(lang, 'artifact.compatibility.unknown');
  const issues = issueText(item?.issues);
  return {
    source,
    lifecycle: t(lang, `artifact.lifecycle.${kind !== 'run_pair' && lifecycle === 'finished' ? 'published' : lifecycle}`),
    availability,
    compatibility,
    issues: issues.length ? t(lang, 'artifact.issues.list', { items: issues.join(' · ') }) : t(lang, 'artifact.issues.none'),
  };
}

/** Return localized connection, last-success time, and restart-needed label. */
export function statusView(status, lang) {
  const state = status == null || status.error
    ? 'offline'
    : ['connected', 'updating', 'offline'].includes(status.state)
      ? status.state
      : status.updating ? 'updating' : 'connected';
  const lastSuccessAt = status?.lastSuccessAt ?? status?.last_success_at;
  const time = lastSuccessAt ? `\u2066${displayValue(lastSuccessAt)}\u2069` : '—';
  const lastSuccess = lastSuccessAt
    ? t(lang, 'artifact.status.last_success', { time })
    : t(lang, 'artifact.status.last_success', { time: '—' });
  return {
    connection: t(lang, `artifact.status.${state}`),
    lastSuccess,
    restartNeeded: t(lang, status?.restart_needed ?? status?.restartNeeded
      ? 'artifact.status.restart_needed'
      : 'artifact.status.restart_not_needed'),
  };
}
