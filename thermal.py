"""
Lumped-capacitance thermal network.

This is the piece the original plan was missing, and it is what makes
anticipation worth anything. Without accumulating thermal state, the optimal
policy is myopic and lookahead features carry no information.

Nodes:
  block   - iron/aluminium structure + coolant, the slow node (minutes)
  oil     - sump and galleries, coupled to the block (minutes)
  turbine - turbo housing and exhaust manifold, the fast node (tens of seconds)
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class ThermalParams:
    c_block: float = 105_000.0     # J/K, structure + coolant
    c_oil: float = 12_000.0        # J/K
    c_turb: float = 6_000.0        # J/K, manifold + turbine housing

    # The oil cooler is an oil-to-coolant exchanger, so oil temperature is tied to
    # coolant temperature, not to ambient. Heat leaving the oil enters the block.
    #
    # CALIBRATED 8 Sep 2026 against 80 minutes of logged oil and coolant across
    # three drives. The old 450 W/K let the oil node float 80 K above the block
    # under load, which this car never does.
    #
    #     measured oil minus coolant   median -1.2 K,  p95 +5.4 K,  max +12.0 K
    #     (pooled over the three drives used for the fit; -1.0 K / +5.5 K over
    #      all five drives that carry both channels)
    #
    # Sweeping the coupling against the logs:
    #
    #     W/K    oil RMSE   modelled p95 gap
    #     450      4.67 K       8.6 K     too loose, gap too wide
    #     800      4.08 K       5.6 K     <-- matches the measured gap
    #    1000      3.96 K       4.7 K
    #    6000      3.66 K       1.0 K     RMSE floor, but the gap collapses
    #
    # RMSE keeps falling all the way to 6000, but that is the wrong criterion on
    # its own: it is dominated by long idle and cruise stretches where oil and
    # coolant are equal whatever the coupling. The p95 gap is what carries the
    # information about the exchanger, and it picks 800.
    #
    # WHAT THIS VALUE DOES NOT COVER. At 800 W/K a sustained hard climb settles
    # the oil at 110 C, about 5 K under the 115-140 C band published for
    # sustained load. That band describes a harder duty cycle than any drive
    # recorded here -- the hottest oil in 168 minutes of logs is 107 C, on
    # 7475b5d7, which also peaked at 111 C after the filter. The value is set by
    # the measurement and the band is reported as a miss; do not raise the number
    # to close a gap the data does not support.
    #
    # NOTE: `Oil temperature after filter` runs +6.8 K hotter than `Oil
    # temperature` at oil above 100 C. If the published band refers to that
    # hotter point, 110.2 + 6.8 = 117 C is inside it. Not applied; see
    # logs/CHANNEL_CENSUS.md.
    #
    # Not cosmetic: oil is a protected component in the H/tau sweep, and this
    # moves its time constant from 25 s to 16 s. Re-run generality_test.py.
    ua_block_oil: float = 800.0    # W/K, oil cooler + conduction
    ua_block_amb: float = 45.0     # W/K, convection off the block itself
    ua_oil_amb: float = 60.0       # W/K, sump surface only
    ua_turb_amb: float = 18.0      # W/K
    ua_gas_turb: float = 0.90      # W/K per (g/s) of exhaust flow

    # NOT IDENTIFIABLE FROM THE LOGS, AND LEFT ALONE ON PURPOSE.
    # The thermostat is regulating for 88-99 % of every drive recorded so far
    # (coolant sits at 88-97 C throughout), so it absorbs any radiator sizing
    # error and the data cannot tell a 300 W/K radiator from a 3000 W/K one.
    # A least-squares fit does drive these to their lower bounds, but only by
    # trading against frac_fuel_to_coolant, which is the same unidentifiability
    # wearing a different hat. Fitting them anyway would be fitting noise.
    #
    # To identify them you need a drive that OVERWHELMS the cooling system --
    # sustained climb in traffic, high ambient, fan at full duty, coolant pushed
    # above the thermostat's fully-open point. That is a specific drive to plan,
    # not something a normal log contains.
    ua_rad_min: float = 300.0      # W/K, fan off, stationary
    ua_rad_ram: float = 60.0       # W/K per (m/s) of vehicle speed
    ua_rad_fan: float = 700.0      # W/K, fan at 100 %

    t_stat_open: float = 361.0     # K, thermostat cracks open (88 C)
    t_stat_span: float = 9.0       # K, fully open 9 K later

    frac_fuel_to_coolant: float = 0.26
    frac_fuel_to_oil: float = 0.050


class ThermalNetwork:
    def __init__(self, p: ThermalParams = None, t_amb=298.0):
        self.p = p or ThermalParams()
        self.t_block = t_amb
        self.t_oil = t_amb
        self.t_turb = t_amb

    def reset(self, t_amb=298.0, warm=True):
        self.t_block = 363.0 if warm else t_amb
        self.t_oil = 358.0 if warm else t_amb
        self.t_turb = 500.0 if warm else t_amb
        return self.state()

    def state(self):
        return np.array([self.t_block, self.t_oil, self.t_turb])

    def step(self, dt, mdot_fuel_gps, mdot_exh_gps, egt_k,
             t_amb, vehicle_mps, fan_duty, coolant_pump_duty=1.0):
        p = self.p
        q_fuel = mdot_fuel_gps * 1e-3 * 44.0e6                     # W

        # The thermostat is what makes coolant temperature a *regulated* variable
        # rather than a free one: below ~88 C the radiator is bypassed entirely.
        stat = float(np.clip((self.t_block - p.t_stat_open) / p.t_stat_span, 0.0, 1.0))
        ua_rad = stat * (p.ua_rad_min + p.ua_rad_ram * vehicle_mps
                         + p.ua_rad_fan * np.clip(fan_duty, 0.0, 1.0))
        ua_rad *= 0.35 + 0.65 * np.clip(coolant_pump_duty, 0.0, 1.0)
        self.thermostat = stat

        q_in_block = q_fuel * p.frac_fuel_to_coolant
        q_out_block = (ua_rad + p.ua_block_amb) * (self.t_block - t_amb) \
                      + p.ua_block_oil * (self.t_block - self.t_oil)

        q_in_oil = q_fuel * p.frac_fuel_to_oil \
                   + p.ua_block_oil * (self.t_block - self.t_oil)
        q_out_oil = p.ua_oil_amb * (self.t_oil - t_amb)

        ua_gt = p.ua_gas_turb * max(mdot_exh_gps, 0.5)
        q_in_turb = ua_gt * (egt_k - self.t_turb)
        q_out_turb = p.ua_turb_amb * (self.t_turb - t_amb)

        self.t_block += dt * (q_in_block - q_out_block) / p.c_block
        self.t_oil += dt * (q_in_oil - q_out_oil) / p.c_oil
        self.t_turb += dt * (q_in_turb - q_out_turb) / p.c_turb
        return self.state()


if __name__ == "__main__":
    tn = ThermalNetwork()
    tn.reset(t_amb=315.0)          # 42 C ambient
    print("Step from highway cruise into a sustained climb (42 C ambient).")
    print("  t [s] | coolant C | oil C | turbine C")
    t = 0.0
    for i in range(1801):
        climbing = t > 300.0
        # cruise: ~1.6 g/s fuel; climb: ~7.5 g/s
        mf = 7.5 if climbing else 1.6
        mex = mf * 15.0
        egt = 1150.0 if climbing else 950.0
        spd = 22.0 if climbing else 33.0
        fan = 1.0 if tn.t_block > 373.0 else 0.0
        tn.step(1.0, mf, mex, egt, 315.0, spd, fan)
        if i % 150 == 0:
            print(f"  {t:5.0f} |   {tn.t_block-273.15:6.1f}  | {tn.t_oil-273.15:5.1f} "
                  f"|  {tn.t_turb-273.15:6.1f}")
        t += 1.0
