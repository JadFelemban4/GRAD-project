"""Read-only graphics inventory; write acceptance evidence under app only."""
from pathlib import Path
import json
from app.results_graphics import build_graphics
from app.record_api import discover_records

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
OUT = APP / 'verification'
graphics = build_graphics(ROOT)
rows = []

def capture(source, panel, reader):
    rows.append({key: panel.get(key) for key in
                 ('id', 'state', 'kind', 'reason', 'source_files', 'caveats')} |
                {'source': source, 'reader': reader,
                 'channels': [{'id': c['id'], 'kind': c.get('kind'), 'label': c.get('label')}
                              for c in panel.get('channels', [])]})

for panel in graphics['reference_panels']:
    capture('published-reference', panel, 'results_comparisons.read_reference_panels')
for source in graphics['agent_sets']:
    for panel in source['panels']:
        capture(source['relative_path'], panel, 'results_records.read_episode_panel' if panel['id'] == 'G11'
                else 'results_sets.read_agent_sets')
for source, panels in graphics['experiment_panels'].items():
    for panel in panels:
        capture(source, panel, 'results_sets.read_training_panels')
assert {row['id'] for row in rows} == {f'G{i:02}' for i in range(1, 26)}
records = discover_records(ROOT)
inventory = {'date': '2026-10-09', 'graphics': rows, 'real_record_count': len(records),
             'real_record_states': {state: sum(r['state'] == state for r in records)
                                    for state in sorted({r['state'] for r in records})},
             'records': [{key: r[key] for key in ('relative_path', 'expected_file', 'state', 'reason')}
                         for r in records]}
(OUT / 'astra-graphics-coverage.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
matrix = json.loads((OUT / 'astra-browser-matrix.json').read_text(encoding='utf-8'))
assert len(matrix) == 8
for case in matrix:
    for surface in ('result', 'record'):
        assert case[surface]['width'] == case['size']['width']
        assert case[surface]['lang'] == case['lang']
        assert case[surface]['theme'] == case['theme']
        assert not case[surface]['overflow']
    assert case['result']['tableRows'] == 11 and not case['result']['tableCursor']
    assert len(case['record']['comparison']) == 5

evidence = {
    'G01': 'Interval renderer regression; real overview browser; linked time cursor.',
    'G08': 'Real pointer selects seed 4; table selects seed 3; keyboard selects seed 1; linked G12. Pointer/touch regression.',
    'G11': 'Real missing-file state; numeric NPZ fixture sample 199 to 200, time 50 s; eight display cases; fallback.',
    'G12': 'Real G08 linked seed evidence; pair source isolation regression.',
    'G21': 'Boundary/outlier + real conservation tests; localized 12894/14318 included, 1424 excluded. Raw browser has 14318 marks.',
    'G22': 'Known histogram reference-coordinate regression; independent channel ownership; real comparison group.',
    'G25': '11 rows, no empty message, table visible before graph mounting; eight display cases.',
}
lines = ['# G01–G25 coverage and acceptance — 9 October 2026', '',
         'All 25 figure IDs are implemented. Runtime data remains source-dependent. This is UI/reader acceptance, not a scientific validation verdict.', '',
         'The exact files, omissions and per-source states are in `astra-graphics-coverage.json`. Real recordings: '
         + str(inventory['real_record_states']) + '. Playback acceptance uses a labelled numeric fixture served separately on loopback; it is never mounted by the production app.', '',
         '| Figure | Actual source / reader | Renderer | Runtime availability | Interaction / evidence |',
         '| --- | --- | --- | --- | --- |']
for i in range(1, 26):
    gid = f'G{i:02}'
    entries = [row for row in rows if row['id'] == gid]
    files = list(dict.fromkeys(file for row in entries for file in (row['source_files'] or [])))
    readers = ', '.join(dict.fromkeys(row['reader'] for row in entries))
    kinds = ', '.join(dict.fromkeys(row['kind'] for row in entries))
    runtime = '; '.join(row['source'] + ': ' + row['state'] for row in entries)
    source = (files[0] if files else 'missing source') + (f' + {len(files)-1} files (manifest)' if len(files) > 1 else '')
    interaction = evidence.get(gid, 'Generic renderer: exact table, keyboard/mark selection, series restore, channels/zoom where applicable. Reader contract + actual source/group inspection; shared renderer tests.')
    lines.append(f'| {gid} | {source}; `{readers}` | `results-graphics.mjs`: {kinds} | {runtime} | {interaction} |')
lines += ['', '## Browser matrix', '',
          'Arabic/English × dark/light × 1440×900/390×844: eight cases for published comparison results and eight for saved-record fixture playback. Actual DOM widths were checked, not inferred from screenshot names. No document horizontal overflow; G25 has 11 rows and no empty cursor. Record sample stays 200/time 50 s, with five numeric command/applied rows. Phone plots show one lane, switch to the other, and keep the same sample.', '',
          'Evidence: `astra-browser-matrix.json` and matching `astra-results-*.jpg` / `astra-record-fixture-*.jpg`. Additional checks: `astra-pair-linked-selection.json`, `astra-knock-raw.json`, `astra-record-fallback.json`, `astra-real-record-missing.json`. Touch handler coverage uses pointerType touch in the renderer regression; physical touch hardware was not exercised.', '',
          '## Remaining scientific inputs', '',
          '- All 86 expected real NPZ recordings are absent. Real policy playback was not verified.',
          '- Sep19 G09 lacks validated knock-margin evidence; legacy G13 lacks local raw curves. Those views remain unavailable.',
          '- Published generations, assumed turbine capacity, weak knock sampling, calibration/held-out boundaries and G25 limitations remain visible. Full R1b preregistered/posthoc analysis is not complete merely because summary graphics exist.',
          '- Torch/SB3 are absent here. No training, evaluation, inference or external model calls were used to fill these gaps.', '',
          '## Verification limits', '',
          '297 JavaScript tests pass. The relevant Python suite runs 232 tests with 3 skips. A broader 360-test app discovery run is not green: 17 failures, 1 error, 6 skips in historical agent tests that assume old scored-model compatibility/catalog shape or temporary files outside this repository. Those refusals and fixture assumptions were retained; see the implementation report.']
(OUT / 'astra-graphics-coverage.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('25 figure IDs inventoried; 8 exact-width browser cases checked;', inventory['real_record_states'])
