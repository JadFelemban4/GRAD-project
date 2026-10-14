"""Graphics integration does not borrow another experiment's sources."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.results_graphics import build_graphics

TMP = Path(__file__).parent / '.superpowers' / 'training-linked-app' / 'tmp'
class GraphicsTests(unittest.TestCase):
    def test_reference_and_per_experiment_panels_stay_separate(self):
        with tempfile.TemporaryDirectory(dir=TMP) as name:
            root=Path(name)
            for folder in ('runs','runs_d2','runs_c4'):(root/folder).mkdir()
            with patch('app.results_graphics.read_reference_panels',return_value=[{'id':'G01'}]), \
                 patch('app.results_graphics.read_agent_sets',return_value=[]), \
                 patch('app.results_graphics.read_training_panels',side_effect=lambda run,root:[{'source_files':[run.name+'/curve.csv']} ]):
                payload=build_graphics(root)
            self.assertEqual(payload['experiment_panels']['d2'][0]['source_files'],['runs_d2/curve.csv'])
            self.assertEqual(payload['experiment_panels']['c4'][0]['source_files'],['runs_c4/curve.csv'])
            self.assertEqual(payload['reference_panels'],[{'id':'G01'}])
