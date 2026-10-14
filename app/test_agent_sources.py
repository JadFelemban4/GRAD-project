"""Issued IDs resolve nested runs without bypassing existing scientific gates."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from app import agent_catalog as C
from app.artifact_catalog import ArtifactCatalog


class SourceTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).parent / '.superpowers' / 'training-linked-app' / 'tmp'
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for arm in C.ARMS:
            directory = self.root / 'runs' / 'fixture' / f'{arm}_seed0'
            directory.mkdir(parents=True)
            meta = copy.deepcopy(C.live_fingerprint('d2'))
            meta['use_preview'] = arm == 'sighted'
            (directory / 'meta.json').write_text(json.dumps(meta), encoding='utf-8')
            with zipfile.ZipFile(directory / 'final.zip', 'w') as archive:
                archive.writestr('data', json.dumps({'num_timesteps': 10, '_total_timesteps': 10}))
        now = [0.0]
        self.registry = ArtifactCatalog(self.root, clock=lambda: now[0], running_pid=lambda p: None)
        self.registry.scan()
        now[0] = 2.0
        item = next(x for x in self.registry.scan()['items'] if x['kind'] == 'run_pair')
        self.identifier = item['id']
        C.register_artifacts(self.registry)

    def write_evaluation(self, prefix='fixture', *, group='runs/fixture', sha=None, other_group=None):
        results = self.root / 'results'
        results.mkdir(exist_ok=True)
        lines = []
        for arm in C.ARMS:
            recorded = sha or C.read_agent(self.identifier, f'{arm}_seed0', self.root)['zip_sha']
            parent = other_group if other_group and arm == 'blind' else group
            lines.append(f'model {parent}/{arm}_seed0: trained 10 steps of 10 requested, '
                         f'from step 0, buffer 10, zip sha {recorded}')
        path = results / f'{prefix}_seed0.txt'
        path.write_text('\n'.join(lines), encoding='utf-8')
        return path

    def test_nested_pair_refuses_model_that_differs_from_its_default_evaluation(self):
        self.write_evaluation(sha='0' * 16)
        with self.assertRaises(C.Refused) as refused:
            C.find_pair(self.identifier, 0, self.root)
        self.assertIn('not the scored artefact', str(refused.exception))
        pair = C.check_pair(self.identifier, 0, self.root)
        self.assertEqual(pair['prefix'], 'fixture')
        self.assertTrue(pair['result_file'])
        self.assertEqual([a['scored'] for a in pair['agents']], ['mismatch', 'mismatch'])

    def test_nested_evaluation_arrival_and_replacement_invalidate_replay(self):
        key = (self.identifier, 0, 1)
        before = C.replay_generation(key, root=self.root)
        self.write_evaluation()
        published = C.replay_generation(key, root=self.root)
        self.assertNotEqual(before, published)
        self.write_evaluation(sha='0' * 16)
        self.assertNotEqual(published, C.replay_generation(key, root=self.root))

    def test_catalog_pair_source_revision_tracks_matching_evaluation_only(self):
        def pair_revision(snapshot, runs):
            experiments = C.discover_registered(snapshot, self.root)
            experiment = next(item for item in experiments if item['runs'] == runs)
            return next(pair['source_revision'] for pair in experiment['pairs'] if pair['seed'] == 0)

        unrelated = self.root / 'runs' / 'other'
        for arm in C.ARMS:
            directory = unrelated / f'{arm}_seed0'
            directory.mkdir(parents=True)
            meta = copy.deepcopy(C.live_fingerprint('d2'))
            meta['use_preview'] = arm == 'sighted'
            (directory / 'meta.json').write_text(json.dumps(meta), encoding='utf-8')
            with zipfile.ZipFile(directory / 'final.zip', 'w') as archive:
                archive.writestr('data', json.dumps({'num_timesteps': 10, '_total_timesteps': 10}))
        now = [0.0]
        registry = ArtifactCatalog(self.root, clock=lambda: now[0], running_pid=lambda p: None)
        registry.scan()
        now[0] = 2.0
        snapshot = registry.scan()
        C.register_artifacts(registry)

        initial = pair_revision(snapshot, self.identifier)
        self.write_evaluation()
        arrived = pair_revision(snapshot, self.identifier)
        self.assertNotEqual(initial, arrived, 'a matching evaluation arrival changes this pair identity')

        evaluation = self.root / 'results' / 'fixture_seed0.txt'
        replacement = evaluation.with_suffix('.replacement')
        replacement.write_text(evaluation.read_text(encoding='utf-8').replace('buffer 10', 'buffer 11'),
                               encoding='utf-8')
        replacement.replace(evaluation)
        replaced = pair_revision(snapshot, self.identifier)
        self.assertNotEqual(arrived, replaced, 'a matching evaluation replacement changes this pair identity')

        before_unrelated = pair_revision(snapshot, self.identifier)
        other = self.root / 'results' / 'other_eval_seed0.txt'
        lines = []
        for arm in C.ARMS:
            recorded = C.read_agent(self.identifier, f'{arm}_seed0', self.root)['zip_sha']
            lines.append(f'model runs/other/{arm}_seed0: trained 10 steps of 10 requested, '
                         f'from step 0, buffer 10, zip sha {recorded}')
        other.parent.mkdir(exist_ok=True)
        other.write_text('\n'.join(lines), encoding='utf-8')
        self.assertEqual(before_unrelated, pair_revision(snapshot, self.identifier),
                         'an unrelated pair evaluation must not change the selected pair identity')

    def test_evaluation_paths_accept_windows_separators(self):
        self.write_evaluation(group='runs\\fixture')
        pair = C.find_pair(self.identifier, 0, self.root)
        self.assertTrue(pair['result_file'])
        self.assertEqual([a['scored'] for a in pair['agents']], ['match', 'match'])

    def test_explicit_producer_prefix_is_found_from_full_model_paths(self):
        key = (self.identifier, 0, 1)
        before = C.replay_generation(key, root=self.root)
        self.write_evaluation(prefix='custom_eval', sha='0' * 16)
        self.assertNotEqual(before, C.replay_generation(key, root=self.root))
        pair = C.check_pair(self.identifier, 0, self.root)
        self.assertTrue(pair['result_file'])
        self.assertEqual(pair['prefix'], 'custom_eval')
        self.assertIn('not the scored artefact', ' '.join(pair['problems']))

    def test_flat_legacy_evaluation_without_budget_lines_remains_available(self):
        target = self.root / 'runs_fixture'
        (self.root / 'runs' / 'fixture').rename(target)
        results = self.root / 'results'
        results.mkdir()
        (results / 'fixture_seed0.txt').write_text('legacy evaluation without model budget lines')
        with patch.object(C, 'run_directory', return_value=target):
            pair = C.find_pair('runs_fixture', 0, self.root)
        self.assertTrue(pair['result_file'])
        self.assertEqual([a['scored'] for a in pair['agents']], ['not recorded', 'not recorded'])

    def test_same_basename_does_not_borrow_other_nested_groups_evaluation(self):
        self.write_evaluation(group='runs/other/fixture')
        pair = C.check_pair(self.identifier, 0, self.root)
        self.assertFalse(pair['result_file'])
        self.assertTrue(pair['problems'])
        self.assertIn('different model paths', ' '.join(pair['problems']))
        # A separate producer prefix can identify this group without borrowing
        # the same-basename file belonging to the other group.
        self.write_evaluation(prefix='this_group')
        pair = C.find_pair(self.identifier, 0, self.root)
        self.assertEqual(pair['prefix'], 'this_group')
        self.assertEqual([a['scored'] for a in pair['agents']], ['match', 'match'])

    def test_evaluation_cannot_mix_two_nested_groups(self):
        self.write_evaluation(other_group='runs/other/fixture')
        with self.assertRaises(C.Refused) as refused:
            C.find_pair(self.identifier, 0, self.root)
        self.assertIn('different model paths', str(refused.exception))

    def test_conflicting_duplicate_budget_lines_cannot_hide_a_sha_mismatch(self):
        path = self.write_evaluation(sha='0' * 16)
        bad_lines = path.read_text()
        self.write_evaluation()
        path.write_text(bad_lines + '\n' + path.read_text())
        with self.assertRaises(C.Refused):
            C.find_pair(self.identifier, 0, self.root)

    def test_nested_c4_basename_does_not_inherit_closed_experiment_verdict(self):
        target = self.root / 'runs' / 'runs_c4'
        (self.root / 'runs' / 'fixture').rename(target)
        with patch.object(C, 'run_directory', return_value=target):
            experiments = C.discover_registered(self.registry.snapshot(), self.root)
        self.assertEqual(experiments[0]['verdict']['state'], 'none')

    def test_nested_id_keeps_protocol_and_all_existing_guards(self):
        pair = C.find_pair(self.identifier, 0, self.root)
        self.assertEqual(pair['protocol'], 'd2')
        self.assertEqual(C.run_directory(self.identifier, self.root), self.root / 'runs' / 'fixture')
        meta_path = self.root / 'runs' / 'fixture' / 'blind_seed0' / 'meta.json'
        meta = json.loads(meta_path.read_text())
        meta['plant_sha'] = 'wrong'
        meta_path.write_text(json.dumps(meta))
        with self.assertRaises(C.Refused) as refused:
            C.find_pair(self.identifier, 0, self.root)
        self.assertIn('plant mismatch', str(refused.exception))

    def test_unknown_and_arbitrary_nested_addresses_are_rejected(self):
        for address in ('art_' + 'f' * 24, 'runs/fixture', '../runs', 'runs_C4'):
            with self.subTest(address=address), self.assertRaises(KeyError):
                C.run_directory(address, self.root)

    def test_loaded_code_change_requires_restart_before_replay(self):
        self.registry._loaded_modules_identity = lambda: [('plant', 'fixture', 'changed')]
        with self.assertRaises(C.Refused):
            C.replay_generation((self.identifier, 0, 1), root=self.root)

    def test_nested_name_cannot_hide_evaluators_arm_rule_behind_an_opaque_id(self):
        directory = self.root / 'runs' / 'fixture'
        target = directory.with_name('blind_group')
        directory.rename(target)
        with patch.object(C, 'run_directory', return_value=target):
            agent = C.read_agent(self.identifier, 'sighted_seed0', self.root)
        self.assertEqual(agent['status'], 'incompatible')
        self.assertIn('other arm', agent['reason'])

    def test_replay_identity_changes_on_model_and_metadata_replacement(self):
        key = (self.identifier, 0, 1)
        before = C.replay_generation(key, root=self.root)
        path = self.root / 'runs' / 'fixture' / 'sighted_seed0' / 'final.zip'
        with zipfile.ZipFile(path, 'a') as archive:
            archive.writestr('new_weights', 'new')
        after = C.replay_generation(key, root=self.root)
        self.assertNotEqual(before, after)
        meta_path = path.parent / 'meta.json'
        meta = json.loads(meta_path.read_text())
        meta['train_dt'] = 0.5
        meta_path.write_text(json.dumps(meta))
        self.assertNotEqual(after, C.replay_generation(key, root=self.root))
        unrelated = self.root / 'runs_other'
        unrelated.mkdir()
        current = C.replay_generation(key, root=self.root)
        self.assertEqual(current, C.replay_generation(key, root=self.root))


if __name__ == '__main__':
    unittest.main()
