import sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root),str(root.parent)]
from backend.server import api_thermal,ThermalRequest
from backend.simulation import create_session,reset_frame,step_session
from thermal import ThermalNetwork
from plant import predict,charge_temperature
class ThermalDiagnostics(unittest.TestCase):
 def test_api_exports_source_and_cooling_phase(self):
  r=api_thermal(ThermalRequest(rpm=3000,map_kpa=180,heat_s=1,cool_s=1,ambient_c=42,fan=.2,pump=.4))
  self.assertIsNone(r['frames'][0]['thermostat'])
  net=ThermalNetwork();net.reset(t_amb=315.15,warm=False)
  engine=predict(3000,180,charge_temperature(315.15),315.15,10,1.0)
  for phase in ['heating','cooling']:
   fuel=engine['mdot_fuel_gps'] if phase=='heating' else 0
   exhaust=engine['mdot_air_gps']+fuel if phase=='heating' else 0
   gas=engine['egt_c']+273.15 if phase=='heating' else 315.15
   for _ in range(10):net.step(.1,fuel,exhaust,gas,315.15,0,.2,.4,rpm=3000 if phase=='heating' else 800)
   exported=next(f for f in r['frames'] if f['phase']==phase)
   for key in ['t_block','t_oil','t_turb','thermostat']:self.assertAlmostEqual(exported[key],getattr(net,key),places=10)
  f=r['frames'][-1]
  self.assertEqual(f['rpm'],800);self.assertEqual(f['mdot_fuel'],0);self.assertEqual(f['mdot_exh'],0)
  self.assertEqual(f['ambient_c'],42);self.assertEqual(f['command'][3:],[.2,.4]);self.assertEqual(f['exhaust_boundary_c'],42)
 def test_road_exports_actual_source_attributes(self):
  s=create_session(scenario='locked',preview=True,policy='manual',seed=0)
  self.assertIsNone(reset_frame(s)['thermostat'])
  f=step_session(s,steps=1)['frames'][0]
  self.assertEqual(f['ambient_c'],s.env.cycle['t_amb']-273.15)
  self.assertEqual(f['thermostat'],s.env.thermal.thermostat)
if __name__=='__main__':unittest.main()


