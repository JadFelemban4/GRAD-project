"""Artifact polling must remain read-only, throttled and coherent."""
import threading
import time
import unittest
from pathlib import Path
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.artifact_api import ArtifactService, mount_artifacts
from app.results_api import mount_results


class Catalog:
    def __init__(self):
        self.count = 0
        self.version = 'a'
        self.pending = False

    def scan(self):
        self.count += 1
        return self.snapshot()

    def snapshot(self):
        return dict(schema_version=1, revision=self.version,
                    training_revision='t', results_revision=self.version,
                    plant_revision='p', items=[], issues=[], updating=self.pending)

    def revisions(self):
        return {k: v for k, v in self.snapshot().items() if k.endswith('revision')}


class ServiceTests(unittest.TestCase):
    def test_visible_clients_share_one_scan_every_two_seconds(self):
        now = [0.0]
        cat = Catalog()
        service = ArtifactService(cat, clock=lambda: now[0])
        service.refresh()
        now[0] = 1.99
        service.refresh()
        self.assertEqual(cat.count, 1)
        now[0] = 2.0
        service.refresh()
        self.assertEqual(cat.count, 2)

    def test_parallel_requests_coalesce_a_slow_scan(self):
        cat = Catalog()
        entered, release = threading.Event(), threading.Event()
        scan = cat.scan
        def slow():
            entered.set()
            release.wait(3)
            return scan()
        cat.scan = slow
        service = ArtifactService(cat)
        thread = threading.Thread(target=service.refresh)
        thread.start()
        self.assertTrue(entered.wait(2))
        started = time.monotonic()
        response = service.refresh()
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertTrue(response['updating'])
        release.set()
        thread.join(3)
        self.assertEqual(cat.count, 1)

    def test_status_uses_one_snapshot_without_calling_revisions(self):
        class CountingCatalog(Catalog):
            def __init__(self):
                super().__init__()
                self.snapshot_count = 0
                self.revision_count = 0

            def snapshot(self):
                self.snapshot_count += 1
                return super().snapshot()

            def revisions(self):
                self.revision_count += 1
                raise AssertionError('status must derive revisions from its snapshot')

        cat = CountingCatalog()
        status = ArtifactService(cat).status()
        self.assertEqual(cat.snapshot_count, 1)
        self.assertEqual(cat.revision_count, 0)
        self.assertEqual(status['revision'], 'a')
        self.assertEqual(status['results_revision'], 'a')

    def test_published_items_and_revisions_come_from_one_scan_snapshot(self):
        class BarrierCatalog(Catalog):
            def __init__(self):
                super().__init__()
                self.captured, self.release = threading.Event(), threading.Event()
                self.snapshots = 0

            def snapshot(self):
                version = self.version
                captured = dict(
                    schema_version=1, revision=version,
                    training_revision=f'training-{version}',
                    results_revision=f'results-{version}',
                    plant_revision=f'plant-{version}',
                    items=[{'relative_path': f'runs_{version}', 'revision': f'item-{version}'}],
                    issues=[], updating=version == 'b',
                    training_updating=version == 'b',
                    results_updating=version == 'b', plant_updating=version == 'b',
                    restart_needed=version == 'b')
                self.snapshots += 1
                # The first status is returned from refresh. Pause only while
                # published() captures its body, after copying the old value.
                if self.snapshots == 2:
                    self.captured.set()
                    self.release.wait(3)
                return captured

            def scan(self):
                self.count += 1
                self.version = 'b'
                return self.snapshot()

            def revisions(self):
                return {'revision': self.version, 'training_revision': 't',
                        'results_revision': self.version, 'plant_revision': 'p'}

        cat = BarrierCatalog()
        service = ArtifactService(cat)
        service._next_scan = time.monotonic() + 10  # keep refresh on the cached path
        outcome = []
        thread = threading.Thread(target=lambda: outcome.append(service.published()))
        thread.start()
        self.assertTrue(cat.captured.wait(2))
        cat.scan()
        cat.release.set()
        thread.join(3)
        self.assertFalse(thread.is_alive())
        body = outcome[0]
        self.assertEqual(cat.version, 'b')
        self.assertEqual(body['revision'], 'a')
        self.assertEqual(body['training_revision'], 'training-a')
        self.assertEqual(body['results_revision'], 'results-a')
        self.assertEqual(body['plant_revision'], 'plant-a')
        self.assertEqual(body['items'], [{'relative_path': 'runs_a', 'revision': 'item-a'}])
        self.assertFalse(body['updating'])
        self.assertFalse(body['training_updating'])
        self.assertFalse(body['results_updating'])
        self.assertFalse(body['plant_updating'])
        self.assertFalse(body['restart_needed'])

    def test_bad_host_is_refused_before_disk_work_and_every_answer_has_no_store(self):
        app, cat = FastAPI(), Catalog()
        service = ArtifactService(cat)
        mount_artifacts(app, service)
        client = TestClient(app, base_url='http://localhost:8000')
        for path in ['/api/artifacts', '/api/artifacts/revision']:
            refused = client.get(path, headers={'Host': 'evil.example:8000'})
            self.assertEqual(refused.status_code, 403)
            self.assertEqual(refused.headers['cache-control'], 'no-store')
        self.assertEqual(cat.count, 0)
        result = client.get('/api/artifacts')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['schema_version'], 1)
        rev = client.get('/api/artifacts/revision')
        self.assertEqual(rev.headers['cache-control'], 'no-store')
        self.assertIn('last_success_at', rev.json())
        self.assertIn('restart_needed', rev.json())

    def test_results_cache_rebuilds_only_for_its_own_stable_revision(self):
        now = [0.0]
        cat, app, builds = Catalog(), FastAPI(), []
        service = ArtifactService(cat, clock=lambda: now[0])
        def build():
            builds.append(cat.version)
            return {'sections': [{'id': cat.version}], 'warnings': []}
        mount_results(app, build=build, artifacts=service)
        client = TestClient(app, base_url='http://localhost:8000')
        self.assertEqual(client.get('/api/results').json()['source_revision'], 'a:p')
        client.get('/api/results')
        self.assertEqual(builds, ['a'])
        cat.version, cat.pending, now[0] = 'b', True, 2.0
        old = client.get('/api/results').json()
        self.assertTrue(old['updating'])
        self.assertEqual(old['sections'], [{'id': 'a'}])
        self.assertEqual(builds, ['a'])
        cat.pending, now[0] = False, 4.0
        new = client.get('/api/results').json()
        self.assertFalse(new['updating'])
        self.assertEqual(new['sections'], [{'id': 'b'}])
        self.assertEqual(builds, ['a', 'b'])
        self.assertEqual(new['artifacts']['results_revision'], 'b')

    def test_result_source_changed_during_build_is_never_published(self):
        now = [0.0]
        cat, app = Catalog(), FastAPI()
        service = ArtifactService(cat, clock=lambda: now[0])
        def build():
            cat.version = 'b'
            now[0] += 2
            return {'sections': [{'id': 'mixed'}]}
        mount_results(app, build=build, artifacts=service)
        client = TestClient(app, base_url='http://localhost:8000')
        body = client.get('/api/results').json()
        self.assertTrue(body['updating'])
        self.assertEqual(body['sections'], [])

    def test_provenance_write_inside_scan_throttle_rejects_candidate(self):
        scratch = Path(__file__).parent / '.superpowers' / 'training-linked-app' / 'tmp'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            cat, app = Catalog(), FastAPI()
            cat.root = Path(directory)
            source = cat.root / 'random_road.py'
            source.write_text('before')
            service = ArtifactService(cat, clock=lambda: 0.0)
            def build():
                source.write_text('changed while reading')
                return {'sections': [{'id': 'mixed'}]}
            mount_results(app, build=build, artifacts=service)
            body = TestClient(app, base_url='http://localhost').get('/api/results').json()
            self.assertTrue(body['updating'])
            self.assertEqual(body['sections'], [])

    def test_failed_verification_scan_does_not_publish_candidate(self):
        now, cat, app = [0.0], Catalog(), FastAPI()
        service = ArtifactService(cat, clock=lambda: now[0])
        def build():
            now[0] = 2.0
            def failed():
                raise OSError('fixture scan failed')
            cat.scan = failed
            return {'sections': [{'id': 'unverified'}]}
        mount_results(app, build=build, artifacts=service)
        body = TestClient(app, base_url='http://localhost').get('/api/results').json()
        self.assertTrue(body['updating'])
        self.assertEqual(body['sections'], [])


if __name__ == '__main__':
    unittest.main()
