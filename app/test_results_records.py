import json
import tempfile
import unittest
from pathlib import Path
from app.results_records import read_episode_panel

TMP=Path(__file__).parent / '.superpowers' / 'training-linked-app' / 'tmp'
class EpisodeTests(unittest.TestCase):
    def test_valid_extract_keeps_recorded_units_time_and_missing_channels(self):
        with tempfile.TemporaryDirectory(dir=TMP) as name:
            root=Path(name); folder=root/'results/agents/fixture';folder.mkdir(parents=True)
            record={'schema_version':1,'provenance':{'policy':'sighted_seed0','protocol':'d2',
                'source_revision':'record-hash','kind':'evaluation','time_unit':'s'},
                'episodes':[{'id':0,'time':[0,1,2],'channels':[
                    {'id':'applied_spark','label':'applied_spark','unit':'deg','values':[0,2,None]},
                    {'id':'reward','label':'reward','unit':'reward','values':[-1,-2,-3]}]}]}
            (folder/'episode_trace.json').write_text(json.dumps(record),encoding='utf-8')
            panel=read_episode_panel(root,'results/agents/fixture')
            self.assertEqual(panel['state'],'available')
            self.assertEqual(panel['provenance_status'],'unknown')
            self.assertIn('provenance_not_verified_by_sidecar',panel['caveats'])
            self.assertEqual(panel['channels'][0]['series'][0]['points'][1],{'x':1,'y':2,'source_index':1,'episode':0})
            self.assertIsNone(panel['channels'][0]['series'][0]['points'][2]['y'])
            self.assertIn('command_channels_missing',panel['caveats'])
    def test_missing_or_misaligned_extract_is_unavailable(self):
        with tempfile.TemporaryDirectory(dir=TMP) as name:
            root=Path(name);folder=root/'results/agents/fixture';folder.mkdir(parents=True)
            self.assertEqual(read_episode_panel(root,'results/agents/fixture')['state'],'unavailable')
            record={'schema_version':1,'provenance':{'policy':'x','protocol':'d2','source_revision':'a','kind':'evaluation','time_unit':'s'},
                'episodes':[{'id':0,'time':[0,1],'channels':[{'id':'reward','unit':'reward','values':[1]}]}]}
            (folder/'episode_trace.json').write_text(json.dumps(record),encoding='utf-8')
            self.assertEqual(read_episode_panel(root,'results/agents/fixture')['state'],'unavailable')
            self.assertEqual(read_episode_panel(root,'../escape')['state'],'withheld')

    def test_extract_provenance_must_match_available_sidecar(self):
        with tempfile.TemporaryDirectory(dir=TMP) as name:
            root=Path(name);folder=root/'results/agents/fixture';folder.mkdir(parents=True)
            (root/'results/agents/index.json').write_text(json.dumps({'policies':{'sighted_seed0':{}}}),encoding='utf-8')
            (folder/'eval_summary.json').write_text(json.dumps({'policy':'sighted_seed0','protocol':'authoritative protocol'}),encoding='utf-8')
            record={'schema_version':1,'provenance':{'policy':'sighted_seed0','protocol':'invented protocol',
                'source_revision':'claimed-revision','kind':'evaluation','time_unit':'s'},
                'episodes':[{'id':0,'time':[0,1],'channels':[{'id':'reward','unit':'reward','values':[1,2]}]}]}
            (folder/'episode_trace.json').write_text(json.dumps(record),encoding='utf-8')
            panel=read_episode_panel(root,'results/agents/fixture')
            self.assertEqual(panel['state'],'unavailable')
            self.assertEqual(panel['reason'],'episode_provenance_mismatch')
