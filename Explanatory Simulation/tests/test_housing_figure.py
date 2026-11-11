"""The housing-lag figure draws the project's numbers, and the lab's own.

figures/housing-lag/params.json is written by export_params.py from plant.py and
thermal.py. These tests fail when the plant moves and the file did not, the way
test_catalog.py pins the plant's figures; the fix is to re-run the script and
rebuild the figure (`npm run figures`), never to edit the file.
"""
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root), str(root.parent)]
from fastapi.testclient import TestClient  # noqa: E402
from backend.server import app  # noqa: E402

FIGURE = root / "figures" / "housing-lag"
spec = importlib.util.spec_from_file_location("export_params", FIGURE / "export_params.py")
export_params = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_params)


def same(test, ours, live, path=""):
    if isinstance(live, dict):
        test.assertEqual(set(ours), set(live), path)
        for key in live:
            same(test, ours[key], live[key], f"{path}.{key}")
    elif isinstance(live, list):
        test.assertEqual(len(ours), len(live), path)
        for index, (a, b) in enumerate(zip(ours, live)):
            same(test, a, b, f"{path}[{index}]")
    elif isinstance(live, float):
        test.assertAlmostEqual(ours, live, places=9, msg=path)
    else:
        test.assertEqual(ours, live, path)


class HousingLagFigure(unittest.TestCase):
    def setUp(self):
        self.params = json.loads((FIGURE / "params.json").read_text(encoding="utf-8"))

    def test_params_match_the_live_plant(self):
        live = export_params.export()
        # plant_sha depends on the Python minor version; the physics must not.
        live.pop("provenance")
        ours = dict(self.params)
        ours.pop("provenance")
        same(self, ours, live)

    def test_point_is_the_lab_thermal_experiment(self):
        source = (root / "src" / "ThermalLab.tsx").read_text(encoding="utf-8")
        initial = re.search(r"const initial:ThermalRequest = \{([^}]*)\}", source).group(1)
        values = dict((k.strip(), float(v)) for k, v in (pair.split(":") for pair in initial.split(",")))
        for key, value in self.params["point"].items():
            self.assertEqual(values[key], value, key)

    def test_the_figure_agrees_with_the_lab_thermal_endpoint(self):
        point = self.params["point"]
        body = dict(point, fan=1, pump=1, heat_s=30, cool_s=0)
        response = TestClient(app).post("/api/thermal", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        frame = next(f for f in response.json()["frames"] if f["time_s"] == 30)
        self.assertAlmostEqual(frame["t_turb"], self.params["reference"]["t_turb_k"][30], places=8)
        self.assertAlmostEqual(frame["egt_c"], self.params["engine"]["egt_c"], places=8)

    def test_c_turb_is_labelled_assumed(self):
        self.assertEqual(self.params["turbine"]["evidence"]["c_turb"], "ASSUMED")


if __name__ == "__main__":
    unittest.main()
