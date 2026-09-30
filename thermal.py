"""
Lumped-capacitance thermal network.

This is the piece the original plan was missing, and it is what makes
anticipation worth anything. Without accumulating thermal state, the optimal
policy is myopic and lookahead features carry no information.

Nodes:
  block   - iron/aluminium structure + coolant, the slow node (minutes)
  oil     - sump and galleries, coupled to the block (minutes)
  turbine - turbo housing and exhaust manifold, the fast node (tens of seconds)

PARAMETER PROVENANCE. Read REFERENCES.md section 4 before quoting any number
below. Every field of ThermalParams carries one of three labels:

  DERIVED         computed from the car's own logs by derive_params.py and read
                  from data/derived_params.json (derived.py) -- NOT typed here.
                  Recomputed whenever a drive arrives. Since 28 September 2026
                  that is the whole block and oil nodes, and the radiator's
                  overall size (not its split, below).
  ASSUMED         an engineering estimate nobody has verified. Declare it as
                  such in the thesis; never present it as a literature value.
  UNIDENTIFIABLE  cannot be determined from any drive this car can produce.

Two kinds of number appear. C is a heat capacity: how much heat it takes to
warm that lump by one degree, in J/K. UA is a heat-transfer rate: how fast
heat moves in or out of it, in W/K. Their ratio C/UA is the lump's time
constant, the time it takes to cover 63 % of a step change in temperature,
and for the turbine node that ratio is the tau in H/tau, the project's
central quantity. c_turb is therefore ASSUMED and load-bearing at once;
generality_test.py sweeps it from 800 to 60 000 J/K for exactly that reason,
because the claim is about the ratio, not about one engine's heat capacity.
"""

import numpy as np
from dataclasses import dataclass, field

import derived


def _d(key):
    """A DERIVED field: read from data/derived_params.json when a ThermalParams
    is made, so a re-derivation takes effect without touching this file."""
    return field(default_factory=lambda: float(derived.get("thermal", key)))


@dataclass
class ThermalParams:
    # ======================================================================
    # THE BLOCK AND OIL NODES ARE DERIVED FROM THE CAR, 28 SEPTEMBER 2026.
    # calibrate_thermal.py does the estimating, derive_params.py runs it on
    # every drive that carries coolant, oil and ambient, and the values live in
    # data/derived_params.json. Before and after, per drive and held out:
    # results/thermal_calibration.json and results/figures/fig20.
    #
    # WHY. With the old ASSUMED values, replayed over the car's drives, the oil
    # spiked to 140 C on hard pulls where the sump read 107 C (time constant
    # 14 s against the car's 70-100 s), the coolant spiked on every pull, and
    # at a four-minute idle on drive10 the block cooled 13 K where the car held
    # 93.5 C. validate.py rows 8, 9 and 11 were outside the car's own bands.
    #
    # THE OIL NODE'S STRUCTURE CHANGED, because the data rejected it. It was
    # heated by 5 % of FUEL energy and cooled through a constant 60 W/K. The car
    # runs its oil 11-15 K ABOVE coolant at 3700-4800 rpm and 70-100 km/h on
    # moderate fuel (drive10), and 2-3 K BELOW coolant cruising at 2600 rpm and
    # 130-140 km/h (3aca2ec1): oil heat follows ENGINE SPEED (friction,
    # windage, churning) and the sump is cooled by ROAD SPEED. Four structures
    # were fitted with the block pinned to measured coolant and scored on
    # drive10 held out; engine-speed heating with road-speed cooling won. An
    # oil-SENSOR lag was also tried and the data did not support it.
    #
    # CORRECTED 30 September 2026 (the merge review, conflict.md section 2a;
    # accepted by Ghassan). "Engine speed, NOT fuel" does not hold: in every
    # rpm bin the car's oil-minus-coolant gap ALSO rises with fuel, +1.5 to
    # +2.8 K per g/s, and the logs do not identify the fuel share -- the fit's
    # objective is flat from 0.05 % to 5 % of fuel (1.741-1.800 K), so 5 %
    # fits as well once the other oil constants refit. What the data rejected
    # was the old COMBINATION (5 %, 800 W/K, 12 kJ/K, tau 14 s). This node fits
    # the logs better on average; at sustained load it reads LOW (drive10's
    # 117 C peak: -16.9 K; the old node -4.1 K).
    #
    # WHAT THE DATA PINS AND WHAT IT DOES NOT. Each node's equation divided by
    # its capacity has only RATIOS. c_block is identified by the one warm-up in
    # the logs (683640a0, radiator shut); left out, that drive is predicted
    # ~14 K wrong, so c_block and frac_fuel_to_coolant are fixed as a ratio,
    # not separately. c_oil is pinned only weakly. Quote time constants and
    # heat splits; quote a capacity alone only with that caveat.
    #
    # NOT REPRODUCED, AND STATED. (1) On the two hottest-afternoon drives
    # (41-45 C ambient) the car's heat-management valve runs the coolant ~9 K
    # lower (82-84 C) after load; on drive10's sustained 4000+ rpm stretch it
    # lets it rise to 97-99 C. A fixed stand-in setpoint does neither, and two
    # regimes on a handful of drives are not enough to fit the valve's control
    # law. (2) validate.py row 8 (drive10's hottest ten minutes of oil) stays
    # below the car's band even with drive10 in the fit: the model's oil runs
    # ~6 K over coolant at sustained 4300 rpm where the car's runs 12-15 K.
    # Drive A of logs/DRIVE_PLAN.md is the data that would settle both.
    # ======================================================================
    c_block: float = _d("c_block")                 # DERIVED* J/K. *As a ratio with
                                                    # frac_fuel_to_coolant; set by 683640a0's warm-up.
                                                    # Was an ASSUMED 105 000
    c_oil: float = _d("c_oil")                     # DERIVED* J/K. *Weakly; the time constant
                                                    # is the robust figure. Was an ASSUMED 12 000
    c_turb: float = 6_000.0        # ASSUMED   J/K, manifold + turbine housing. LOAD-BEARING: sets
                                   #           tau and so H/tau; swept 800-60 000 in generality_test.py.
                                   #           No channel on this car measures the turbine.

    # The oil cooler is an oil-to-coolant exchanger (BMW ST1505 section 4.1), so
    # oil temperature is tied to coolant temperature. Heat leaving the oil enters
    # the block. Until 28 September this was 800 W/K, chosen on 8 September by
    # the p95 oil-minus-coolant gap with frac_fuel_to_oil ASSUMED at 5 %; with
    # the oil's heat input and sump cooling estimated alongside it, the data
    # gives a looser coupling.
    # The 8 September reasoning, kept from JMF-2340550-sep17 (tag
    # sep17-before-merge): RMSE alone keeps falling all the way to 6000 W/K,
    # because long idle and cruise stretches dominate it; the p95 gap (+5.4 K
    # over the three fitted drives) is what carries the exchanger, and it
    # picked 800. On that node a sustained climb settled the oil at 110 C.
    ua_block_oil: float = _d("ua_block_oil")       # DERIVED  W/K
    ua_block_amb: float = _d("ua_block_amb")       # DERIVED  W/K, block to ambient with the radiator
                                                    # shut. Was an ASSUMED 45; the car holds its
                                                    # coolant at idle on ~1.7 kW of fuel heat, so
                                                    # standing losses are near zero
    ua_oil_amb: float = _d("ua_oil_amb")           # DERIVED  W/K, sump to ambient at a standstill.
                                                    # Was an ASSUMED 60
    ua_oil_ram: float = _d("ua_oil_ram")           # DERIVED  W/K per (m/s) of road speed: the sump
                                                    # sits in the airstream. NEW 28 September
    ua_turb_amb: float = 18.0      # ASSUMED   W/K
    ua_gas_turb: float = 0.90      # ASSUMED   W/K per (g/s) of exhaust flow

    # THE RADIATOR: ITS SIZE IS DERIVED, ITS SPLIT IS NOT. No coolant-flow or fan
    # signal exists on this car (every water-pump and fan-actual channel reads
    # zero, logs/CHANNEL_CENSUS.md), so the three terms cannot be told apart.
    # Their overall size can: wherever the coolant climbs above its regulated
    # point, the radiator is open and its capacity sets the temperature.
    # derive_params.py scales the reasoned 300 / 60 / 700 split by one factor
    # the data sets (`_ua_rad_scale` in data/derived_params.json); the SPLIT
    # between them stays UNIDENTIFIABLE.
    ua_rad_min: float = _d("ua_rad_min")           # DERIVED size, UNIDENTIFIABLE split. W/K, fan off
    ua_rad_ram: float = _d("ua_rad_ram")           # same. W/K per (m/s) of vehicle speed
    ua_rad_fan: float = _d("ua_rad_fan")           # same. W/K, fan at 100 %

    # The stand-in thermostat. MODELLING EQUIVALENT: the real B58 has no
    # thermostat but a DME-driven rotary valve ("heat management module", BMW
    # training document ST1505, 2015). Both numbers come from the logged
    # coolant; never cite them to BMW. REFERENCES.md section 2. Until 28 Sep
    # they were 88 C and 9 K, which let the block drift 4-13 K below the car at
    # light load and spike on every pull; the car's valve regulates tightly.
    t_stat_open: float = _d("t_stat_open")         # DERIVED  K, cracks open
    t_stat_span: float = _d("t_stat_span")         # DERIVED  K, fully open this much later

    frac_fuel_to_coolant: float = _d("frac_fuel_to_coolant")  # DERIVED* share of fuel energy to the
                                                               # coolant, *as a ratio with c_block.
                                                               # Was an ASSUMED 0.26
    frac_fuel_to_oil: float = _d("frac_fuel_to_oil")          # DERIVED  same, for the oil. Was an
                                                               # ASSUMED 0.050 -- the pull spikes
    # The oil's main heat input: friction, windage and churning, which rise with
    # ENGINE SPEED -- beside frac_fuel_to_oil, whose value the logs do not pin
    # (see the 30 September correction above).  q = k_oil_rpm * (rpm / 3000) ** n_oil_rpm, W.
    # NEW 28 September 2026. The exponent comes out near 4, steep, and it is what
    # separates drive10's sustained 4000+ rpm (oil 11-15 K over coolant) from
    # 2600 rpm cruising (oil below coolant).
    k_oil_rpm: float = _d("k_oil_rpm")             # DERIVED  W at 3000 rpm
    n_oil_rpm: float = _d("n_oil_rpm")             # DERIVED  exponent


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
             t_amb, vehicle_mps, fan_duty, coolant_pump_duty=1.0, *, rpm):
        """Advance the three nodes by dt seconds.

        `rpm` is REQUIRED and keyword-only, on purpose: since 28 September the
        oil's main heat input is engine speed (k_oil_rpm), and a default of zero
        would let a caller that forgot it run the oil 10-15 K cold under load
        without a word -- the same shape as mistake 1's silent default geometry.

        NUMERICALLY STIFF ABOVE dt ~1.1 s, and NOT YET FIXED (30 September 2026,
        the merge review; conflict.md decision 1, agreed by Jad and Ghassan).
        With the derived constants the explicit-Euler factor of a block-node
        perturbation at the locked climb is -0.78 at dt 1.0, -1.67 at 1.5 and
        -2.56 at 2.0 (the pre-derivation constants: +0.84 to +0.67). At dt 1.0
        the coolant zig-zags about 2 K on every step of the climb (Ghassan's
        re-check: 91.6-93.8 C, sign flips on 100 % of steps in the last 30 %);
        at dt 2.0 -- where generality_test.py runs -- it swings 85-95 C and
        never settles. Agreed fix, before ANY retrain: sub-step this network
        (e.g. 0.1 s inside each env step) or integrate it implicitly, then
        re-run generality_test.py. Until then no H/tau output is quotable.
        """
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

        r = max(float(rpm), 0.0) / 3000.0 if rpm > 400.0 else 0.0
        q_in_oil = q_fuel * p.frac_fuel_to_oil \
                   + p.k_oil_rpm * r ** p.n_oil_rpm \
                   + p.ua_block_oil * (self.t_block - self.t_oil)
        q_out_oil = (p.ua_oil_amb + p.ua_oil_ram * vehicle_mps) * (self.t_oil - t_amb)

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
        tn.step(1.0, mf, mex, egt, 315.0, spd, fan, rpm=3000.0 if climbing else 2200.0)
        if i % 150 == 0:
            print(f"  {t:5.0f} |   {tn.t_block-273.15:6.1f}  | {tn.t_oil-273.15:5.1f} "
                  f"|  {tn.t_turb-273.15:6.1f}")
        t += 1.0
