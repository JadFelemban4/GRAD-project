import tempfile
import unittest
from pathlib import Path
from app.artifact_catalog import ArtifactCatalog

TMP=Path(__file__).parent / '.superpowers' / 'training-linked-app' / 'tmp'
class RevisionTests(unittest.TestCase):
    def test_legacy_curve_updates_result_revision_without_checkpoint_dependency(self):
        with tempfile.TemporaryDirectory(dir=TMP) as name:
            root=Path(name);(root/'results').mkdir()
            folder=root/'runs_d2/sighted_seed0';folder.mkdir(parents=True)
            curve=folder/'curve.csv';curve.write_text('episode,return\n0,2\n',encoding='utf-8')
            now=[1.0];catalog=ArtifactCatalog(root,clock=lambda:now[0],running_pid=lambda _:None)
            def stable():
                catalog.scan();now[0]+=1.1;catalog.scan();now[0]+=1.1;return catalog.scan()
            before=stable()
            curve.write_text('episode,return\n0,2\n1,3\n',encoding='utf-8')
            after=stable()
            self.assertNotEqual(before['results_revision'],after['results_revision'])
            (folder/'checkpoint.zip').write_bytes(b'not evaluated')
            checkpoint=stable()
            self.assertEqual(after['results_revision'],checkpoint['results_revision'])
