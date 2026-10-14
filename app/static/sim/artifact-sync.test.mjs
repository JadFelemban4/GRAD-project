import test from 'node:test';
import assert from 'node:assert/strict';
import { createArtifactSync } from './artifact-sync.mjs';

const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };

function harness(readRevision, { visible = true, onChange = null } = {}) {
  let nextId = 1;
  const timers = new Map();
  const delays = [];
  const schedule = (fn, ms) => { const id = nextId++; timers.set(id, fn); delays.push(ms); return id; };
  const cancel = id => timers.delete(id);
  const fire = async (id = timers.keys().next().value) => {
    const fn = timers.get(id);
    assert.ok(fn, `timer ${id} exists`);
    timers.delete(id);
    fn();
    await Promise.resolve();
    await Promise.resolve();
  };
  const changes = [];
  const statuses = [];
  const sync = createArtifactSync({ readRevision, onChange: async (prev, next) => {
    changes.push([prev, next]);
    if (onChange) await onChange(prev, next);
  },
    onStatus: state => statuses.push(state), schedule, cancel, isVisible: () => visible });
  return { sync, timers, delays, changes, statuses, fire, setVisible: value => { visible = value; } };
}

test('first revision publishes once and unchanged revisions keep a two-second poll', async () => {
  const row = { revision: 'a', training_revision: 't', results_revision: 'r', plant_revision: 'p', updating: false, last_success_at: 'now', restart_needed: false };
  const h = harness(async () => row);
  h.sync.start();
  await Promise.resolve(); await Promise.resolve();
  assert.deepEqual(h.changes, [[null, row]]);
  assert.deepEqual(h.delays, [2000]);
  await h.fire();
  assert.equal(h.changes.length, 1);
  assert.deepEqual(h.delays, [2000, 2000]);
  h.sync.stop();
  assert.equal(h.timers.size, 0);
});

test('a sub-revision change refreshes once even when the aggregate revision is unchanged', async () => {
  const rows = [
    { revision: 'a', training_revision: 't1' },
    { revision: 'a', training_revision: 't2' },
  ];
  const h = harness(async () => rows.shift());
  h.sync.start(); await flush();
  await h.fire(); await flush();
  assert.equal(h.changes.length, 2);
  assert.equal(h.changes[1][1].training_revision, 't2');
  h.sync.stop();
});

test('a new revision waits for its async refresh before scheduling the next poll', async () => {
  let release;
  const rows = [{ revision: 'a' }, { revision: 'b' }];
  const h = harness(async () => rows.shift(), { onChange: async (_prev, next) => {
    if (next.revision === 'b') await new Promise(resolve => { release = resolve; });
  } });
  h.sync.start(); await flush();
  assert.equal(h.delays.at(-1), 2000);
  await h.fire(); await flush();
  assert.equal(release instanceof Function, true);
  assert.equal(h.changes.length, 2);
  assert.equal(h.delays.length, 1, 'the next timer is scheduled only after the callback settles');
  release(); await flush();
  assert.equal(h.delays.length, 2);
  h.sync.stop();
});

test('resume waits for a refresh callback already in progress while the page was hidden', async () => {
  let release;
  let reads = 0;
  const h = harness(async () => { reads += 1; return { revision: 'a' }; }, { onChange: async () => {
    if (reads === 1) await new Promise(resolve => { release = resolve; });
  } });
  h.sync.start(); await flush();
  assert.equal(reads, 1);
  h.setVisible(false); h.sync.visibilityChanged();
  h.setVisible(true); h.sync.visibilityChanged();
  await flush();
  assert.equal(reads, 1, 'resume does not overlap the earlier refresh callback');
  release(); await flush();
  assert.equal(reads, 2, 'a fresh read starts after the earlier callback settles');
  h.sync.stop();
});

test('updating responses retry the refresh at the same revision until stable', async () => {
  const rows = [
    { revision: 'same', updating: true },
    { revision: 'same', updating: false },
  ];
  const h = harness(async () => rows.shift());
  h.sync.start(); await Promise.resolve(); await Promise.resolve();
  assert.equal(h.changes.length, 1);
  await h.fire();
  assert.equal(h.changes.length, 2);
  assert.equal(h.changes[1][1].updating, false);
  h.sync.stop();
});

test('hidden pages pause and visible pages refresh immediately', async () => {
  const h = harness(async () => ({ revision: 'a' }));
  h.setVisible(false);
  h.sync.start();
  assert.equal(h.timers.size, 0);
  h.setVisible(true); h.sync.visibilityChanged();
  await Promise.resolve(); await Promise.resolve();
  assert.equal(h.changes.length, 1);
  h.sync.stop();
});

test('failures back off 2, 4, 8, then 30 seconds and expose offline status', async () => {
  const h = harness(async () => { throw new Error('offline'); });
  h.sync.start();
  for (const wait of [2, 4, 8, 30]) {
    await Promise.resolve(); await Promise.resolve();
    assert.equal(h.delays.at(-1), wait * 1000);
    assert.equal(h.statuses.at(-1).state, 'offline');
    if (wait !== 30) await h.fire();
  }
  h.sync.stop();
});

test('stop aborts an in-flight read and ignores its late response', async () => {
  let resolveRead;
  let signal;
  const h = harness((_signal) => { signal = _signal; return new Promise(resolve => { resolveRead = resolve; }); });
  h.sync.start(); await Promise.resolve();
  h.sync.stop();
  assert.equal(signal.aborted, true);
  resolveRead({ revision: 'late' });
  await Promise.resolve(); await Promise.resolve();
  assert.deepEqual(h.changes, []);
  assert.equal(h.timers.size, 0);
});

test('failed refresh callback does not consume that revision', async () => {
  let attempts = 0;
  const row = { revision: 'a' };
  const h = harness(async () => row, { onChange: async () => { if (++attempts === 1) throw new Error('refresh failed'); } });
  h.sync.start(); await Promise.resolve(); await Promise.resolve(); await Promise.resolve();
  assert.equal(h.statuses.at(-1).state, 'offline');
  await h.fire(); await Promise.resolve(); await Promise.resolve(); await Promise.resolve();
  assert.equal(attempts, 2);
  h.sync.stop();
});

test('resolved API error is offline and does not consume the previous revision', async () => {
  const rows = [
    { revision: 'a' },
    { error: 'temporary server error', revision: 'b' },
    { revision: 'b' },
  ];
  const h = harness(async () => rows.shift());
  h.sync.start(); await flush();
  await h.fire(); await flush();
  assert.equal(h.statuses.at(-1).state, 'offline');
  assert.equal(h.changes.length, 1);
  await h.fire(); await flush();
  assert.equal(h.changes.length, 2, 'the valid b revision is refreshed after the API error');
  assert.equal(h.changes.at(-1)[1].revision, 'b');
  h.sync.stop();
});

test('stop then start ignores status from the old pending refresh and loads the new generation', async () => {
  let releaseOld;
  let reads = 0;
  const h = harness(async () => {
    reads += 1;
    return reads === 1
      ? { revision: 'old', last_success_at: 'old-time' }
      : { revision: 'new', last_success_at: 'new-time' };
  }, { onChange: async (_prev, next) => {
    if (next.revision === 'old') await new Promise(resolve => { releaseOld = resolve; });
  } });
  h.sync.start(); await flush();
  assert.equal(releaseOld instanceof Function, true);
  h.sync.stop();
  h.sync.start(); await flush();
  assert.deepEqual(h.statuses, [{ state: 'connected', lastSuccessAt: 'new-time' }]);
  assert.equal(h.changes.at(-1)[1].revision, 'new');
  releaseOld(); await flush();
  assert.deepEqual(h.statuses, [{ state: 'connected', lastSuccessAt: 'new-time' }]);
  h.sync.stop();
});
