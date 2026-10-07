import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { commandChains, commandReadings, editorPresentation, stepControls } from './supervisor.mjs';
import { resolveReading } from './reading-context.mjs';

const projectRoot = fileURLToPath(new URL('../../', import.meta.url));
const virtualenvPython = fileURLToPath(new URL(
  process.platform === 'win32'
    ? '../../../.venv/Scripts/python.exe'
    : '../../../.venv/bin/python',
  import.meta.url,
));
const pythonCandidates = process.env.CATALOG_TEST_PYTHON
  ? [process.env.CATALOG_TEST_PYTHON]
  : [
      ...(existsSync(virtualenvPython) ? [virtualenvPython] : []),
      ...(process.platform === 'win32' ? ['python', 'python3'] : ['python3', 'python']),
    ];

function loadCatalog() {
  for (const python of pythonCandidates) {
    try {
      const output = execFileSync(python, [
        '-c', 'import json; from backend.catalog import metadata; print(json.dumps(metadata("ar")))',
      ], { cwd: projectRoot, encoding: 'utf8' });
      return JSON.parse(output).concepts;
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw new Error(`Catalog metadata failed using Python ${python}: ${error.message}`, { cause: error });
      }
    }
  }
  throw new Error(
    'Catalog tests require Python. Create GRAD-project/.venv, set CATALOG_TEST_PYTHON to a Python executable, or install Python on PATH.',
  );
}

const catalog = loadCatalog();
const frame = {
  input_time_s: 170,
  time_s: 171,
  dt: 1,
  action: [0, 0, 0, 0, 0],
  requested: [-8, -.15, -40, 0, .3],
  command: [-1.5, -.03, -10, .75, .8],
  baseline: { spark: 19.6, lam: 1, map_kpa: 60, fan: 0 },
  spark: 18.1,
  lam: .97,
  map_kpa: 91,
};

const semantics = {
  baseline_ecu: [/مرجع ECU/, /يجدول/, 'class BaselineECU'],
  map_reference: [/PI/, /الموازية/, 'base, map_b = self._track_torque'],
  spark: [/توقيت الإشعال الفعلي/, /الأساس/, 'self.spark ='],
  spark_trim: [/تصحيح الإشعال/, /أمر إضافي/, 'ACT_LO'],
  lam: [/^لامبدا$/, /نسبة الهواء والوقود/, '(self.lam - 1.0) * 8.0'],
  lambda_trim: [/تصحيح لامبدا/, /أمر إضافي/, 'ACT_LO'],
  map: [/ضغط مجمع السحب/, /الضغط المطلق/, 'self.map_kpa / 120.0 - 1.0'],
  boost_trim: [/تصحيح MAP/, /إزاحة MAP/, 'ACT_LO'],
};

test('production selections build real explanations with independent source paths', () => {
  const expected = [
    ['baseline_ecu', 'spark_trim', 'spark_trim', 'spark'],
    ['baseline_ecu', 'lambda_trim', 'lambda_trim', 'lam'],
    ['map_reference', 'boost_trim', 'boost_trim', 'map'],
    ['baseline_ecu', 'fan_duty', 'fan_duty', 'fan_duty'],
    ['baseline_ecu', 'pump_duty', 'pump_duty', 'pump_duty'],
  ];
  for (const chain of commandChains(frame)) {
    for (const [index, row] of commandReadings(chain, 's').entries()) {
      assert.equal(row.conceptId, expected[chain.index][index]);
      const concept = catalog.find(c => c.id === row.conceptId);
      assert.ok(concept?.name);
      assert.ok(concept?.meaning);
      assert.ok(concept?.source.line > 0);
      assert.doesNotMatch(concept.meaning, /undefined/);
      if (semantics[concept.id]) {
        const [title, meaning, source] = semantics[concept.id];
        assert.match(concept.name, title);
        assert.match(concept.meaning, meaning);
        assert.equal(concept.source.variable, source);
      }
      const options = { frame, sessionId: 's', conceptId: concept.id };
      const reading = resolveReading(row, options);
      assert.equal(reading.value, chain[row.field.split('.').at(-1)]);
      assert.equal(reading.unit, row.unit);
      assert.equal(reading.digits, chain.digits);
      assert.equal(reading.inputS, 170);
      assert.equal(reading.endS, 171);
      if (index === 0) assert.notEqual(concept.source.variable, 'ACT_LO');
      if (index === 3 && chain.index === 0) assert.equal(reading.value, 18.1);
      if (index === 2 && chain.index === 0) assert.equal(reading.value, -1.5);
      assert.equal(resolveReading(row, { ...options, sessionId: 'other' }), null);
      assert.equal(resolveReading(row, { ...options, frame: { time_s: 0 } }).value, null);
      const next = resolveReading(row, {
        ...options,
        frame: { ...frame, input_time_s: 171, time_s: 172, spark: 18.2 },
      });
      assert.equal(next.inputS, 171);
      if (index === 3 && chain.index === 0) assert.equal(next.value, 18.2);
    }
  }
});

test('applied automatic policy hides retained manual draft and makes no next-step promise', () => {
  const draft = [-8, 0, 0, 1, 1];
  assert.equal(editorPresentation('manual', false, false).showEditor, true);
  const automaticFrame = { ...frame, requested: [0, 0, 0, 1, 1] };
  assert.equal(commandChains(automaticFrame)[0].requested, 0);
  const auto = editorPresentation('preview', false, false);
  assert.equal(auto.showEditor, false);
  assert.match(auto.message, /محفوظة/);
  assert.match(auto.message, /غير مستخدمة/);
  assert.doesNotMatch(auto.message, /الخطوة التالية|−8|-8/);
  assert.equal(stepControls('preview', false, draft), undefined);
  assert.deepEqual(draft, [-8, 0, 0, 1, 1]);
  assert.equal(editorPresentation('manual', false, false).disabled, false);
  assert.deepEqual(stepControls('manual', false, draft).trims, draft);
  assert.equal(editorPresentation('manual', true, false).disabled, true);
  assert.equal(editorPresentation('manual', false, true).disabled, true);
});
