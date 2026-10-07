import sys
import unittest
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root), str(root.parent)]
from fastapi.testclient import TestClient
from backend.server import app
from plant import charge_temperature, predict
from thermal import ThermalNetwork

class ControlledThermalComparison(unittest.TestCase):
    def test_controlled_fan_then_pump_use_actual_source_and_same_initial_time(self):
        request = dict(rpm=3000, map_kpa=180, ambient_c=42, spark=8, lam=.92,
                       fan=1, pump=1, heat_s=120, cool_s=90)
        client = TestClient(app)
        runs = []
        for changes in ({}, {'fan':0}, {'pump':.3}):
            inputs = dict(request, **changes)
            response = client.post('/api/thermal', json=inputs)
            self.assertEqual(response.status_code, 200, response.text)
            result = response.json()
            runs.append(result)
            engine = predict(3000,180,charge_temperature(315.15),315.15,8,.92)
            net = ThermalNetwork()
            net.reset(t_amb=315.15,warm=False)
            index = 1
            for phase, duration in [('heating',120),('cooling',90)]:
                for second in range(duration):
                    for _ in range(10):
                        net.step(.1,engine['mdot_fuel_gps'] if phase=='heating' else 0,
                                 engine['mdot_air_gps']+engine['mdot_fuel_gps'] if phase=='heating' else 0,
                                 engine['egt_c']+273.15 if phase=='heating' else 315.15,
                                 315.15,0,inputs['fan'],inputs['pump'],rpm=3000 if phase=='heating' else 800)
                    frame = result['frames'][index]
                    for node in ['t_block','t_oil','t_turb']:
                        self.assertAlmostEqual(frame[node],getattr(net,node),places=8)
                    index += 1
            self.assertEqual(result['initial_state'],'cold_start_at_ambient')
        base = runs[0]
        self.assertGreater(max(f['thermostat'] or 0 for f in base['frames']),0)
        for changed in runs[1:]:
            self.assertEqual(base['method'],changed['method'])
            self.assertEqual(base['initial_state'],changed['initial_state'])
            self.assertEqual([f['time_s'] for f in base['frames']],[f['time_s'] for f in changed['frames']])
            for node in ['t_block','t_oil','t_turb']:
                self.assertEqual(base['frames'][0][node],changed['frames'][0][node])
            for a,b in zip(base['frames'],changed['frames']):
                for key in ['phase','rpm','mdot_fuel','mdot_exh','ambient_c','egt_c','exhaust_boundary_c','t_turb']:
                    self.assertEqual(a[key],b[key],key)
            # Source replay establishes actual effect without claiming a universal monotonic law.
            self.assertNotEqual(base['frames'][120]['t_block'],changed['frames'][120]['t_block'])
        self.assertEqual(runs[1]['frames'][1]['command'][3:],[0,1])
        self.assertEqual(runs[2]['frames'][1]['command'][3:],[1,.3])

if __name__ == '__main__':
    unittest.main()
