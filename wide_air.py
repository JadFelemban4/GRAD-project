"""wide_air.py -- X2's training roads: X1's extremes design in wider air.

    python train.py --road wideair --steps 1080000 --seed 0 --keep-buffer --out runs/wideair_dt1
    python check_roads.py --road wideair
    python test_wide_air.py

Decided by Ghassan on 11 October 2026 (results/PREREGISTRATION_X2.md): the
extremes roads of decision 12 (engine_env.ExtremesTrainingEnv) with the air
widened. Per episode, from the same road stream, so a seed still fixes the
whole sequence:

    ambient     0-45 C          X1 drew 25-45 C
    pressure    80-101.3 kPa    X1 trained at 101.3 kPa only (80 kPa is about
                                1 950 m in a standard atmosphere, above Taif)

Everything else is X1's: the road families, the speed target redrawn every
60-180 s between 60 and 150 km/h, hills to 18 %, the housing's heat capacity
x0.75-1.33. 50 C, 76 kPa and hills of 18-22 % stay held out for the transfer
test (conditions_test.py). TRAINING ONLY: scoring stays on the locked climb at
42 C and 101.3 kPa (evaluate.py), where this design reduces to the plant.

HOW PRESSURE REACHES THE ENGINE: the conditions test's model, made per episode.
The plant reads the cycle's p_baro for drag and as one of the agent's inputs,
and nothing else. Here the compressor's inlet becomes p_baro x 99.3 / 101.3
(the 2 kPa filter loss the B58's sea-level inlet carries, plant.engine.boost.
inlet_sea_kpa), so the flow-dependent boost ceiling and the hard pressure cap
both fall with altitude, for the agent's car and the baseline car alike. NOT modelled, so altitude here
is MILDER than real, exactly as conditions_test.py states for its own test: the
hotter compressor outlet at the higher pressure ratio (plant.charge_temperature
has no pressure ratio in it), the fall in exhaust backpressure, and the colder
air of a real mountain. Ambient and pressure are drawn independently, so the
corners include hot, thin air that no real road has.

COLD AIR IS EXTRAPOLATION. The car's logs cover 19-45 C of ambient (data/
master_samples.csv), so below 19 C the derived thermal constants run outside
the air they were fitted in. Say so beside any result from these agents.

THE INLET IS THE ENVIRONMENT'S OWN (20 October 2026, the four-engine build).
Until then this module replaced engine_env's boost ceiling, in any process that
imported it, by one that asked the WideAirTrainingEnv then stepping for its
inlet pressure and fell back to the plant's 99.3 kPa when none was: a
monkeypatch, kept so that no hashed plant file changed and X1's and X2's agents
shared one plant certificate. The plant files change on GRA-test anyway, and
every SupervisoryTunerEnv now carries its compressor inlet, `inlet_kpa`, which
plant.boost_ceiling_kpa and MAP_CEIL_KPA both read; this environment sets its
own per episode, and no other environment in the process can see it. The
numbers are the monkeypatch's, to the bit (build step 1's identity harness, the
wideair jobs). At 101.3 kPa the design reduces to the plant exactly;
test_wide_air.py checks it to the bit.

THE TORQUE FLOOR FOLLOWS THE AIR (found 11 October by check_roads.py, before
any training). X1's roads never ask the engine for less than 15 Nm, because
this model has no fuel cut: with the throttle shut it still makes 12.0 Nm at
42 C, and a request below that cannot be met by any policy (engine_env's note
on the torque floor, EXTREME_T_FLOOR_NM until 20 October and the plant's
loop.torque_floor_nm since). In colder air the charge is denser and the
engine makes more with the throttle shut: 15.5 Nm at 25 C, 20.6 at 0 C
(closed_throttle_nm, the same measurement). The first draft of these roads kept
15 Nm, and five of its 40 roads, all at 0-7 C, failed: on descents the baseline
was asked for 15 Nm and made 17-19, so the tracking term fired for every
policy alike. The floor is now X1's rule at each episode's own air: 1.25 times
the most torque the engine makes there with the throttle shut (15 Nm over
12.0 at 42 C is X1's 1.25), and never under X1's 15 Nm.

THE GEARBOX KNOWS THE AIR TOO (found 11 October by test_reward.py's thin-air
corners, before any training). The box kicks down when the torque a gear is
asked for exceeds what the engine can deliver at that speed
(engine_env.Vehicle.shift_ceiling_nm), read from a table measured at sea level.
In thin air the engine delivers less: 252.8 Nm at 2000 rpm and 80 kPa against
316.3 at sea level. With the sea-level table the box held a gear the engine
could no longer pull, and on the 12 % climb at 45 C and 80 kPa the baseline
fell short of its torque on 80 of 899 steps (neutral -0.139 a step). A real
automatic kicks down when the pedal goes deeper. ThinAirVehicle scales the
table, per engine speed, by what the engine delivers at the episode's pressure
over what it delivers at sea level, measured with measure_deliverable_torque's
own loop at the table's own 42 C (deliverable_torque, once per process and
plant, at 80, 85, 90 and 95 kPa, interpolated between). At 101.3 kPa it is the
stored table itself.

THE PLANT IS PASSED (20 October 2026): WideAirTrainingEnv(plant=...), as every
environment; the inlet's sea-level value, the torque floor and the stored table
are that plant's.

The road builder's drag uses the episode's air density, and its floor the
episode's floor. At 101.3 kPa and a 15 Nm floor the two builders below return
what engine_env's return, to the bit (tested), and they are copies of those for
that reason alone.
"""
from dataclasses import replace

import numpy as np

import engine_env as EE

WIDE_T_AMB_C = (0.0, 45.0)            # drawn per episode; 50 C held out
WIDE_P_KPA = (80.0, 101.3)            # drawn per episode; 76 kPa held out
P_SEA = 101.3                         # the plant's sea level, kPa
FLOOR_MARGIN = 1.25                   # X1's: 15 Nm over the 12.0 Nm made with the throttle shut at 42 C
CLOSED_RPM = (1000.0, 1200.0)         # the lowest speeds the box holds, where that torque is largest
CLOSED_SETTLE = 12                    # closed_throttle_nm's steps: 12 returned what 30 did, to 4 decimals, 0-45 C (11 Oct)
P_TABLE = (80.0, 85.0, 90.0, 95.0)    # where the thin-air gearbox table is measured; 101.3 is the stored one
# The stored table's ambient, block and settling steps are the car's own
# (plant.car.table_*), read by deliverable_torque below; T_TABLE_K = 315.0 and
# the 365 K and 30-step defaults stood for them here until 21 October 2026.


def inlet_kpa(p_baro_kpa, *, engine):
    """The compressor inlet at this barometric pressure: the engine's sea-level
    inlet (99.3 kPa on the B58, engine.boost.inlet_sea_kpa) scaled with it."""
    return engine.boost.inlet_sea_kpa * (float(p_baro_kpa) / P_SEA)


def _rho(p_kpa, t_amb):
    return float(p_kpa) * 1e3 / (287.0 * t_amb)


def closed_throttle_nm(env, t_amb):
    """The most torque the engine makes with the throttle shut at this ambient.

    engine_env.measure_deliverable_torque's loop at a request of 0 instead of
    1000 Nm: the environment's own load loop, BaselineECU.step supplying spark
    and lambda, the largest torque over the second half of the settled window,
    at CLOSED_RPM. MEASURED 11 October, Nm at 1000 / 1200 / 1600 / 2100 / 2700
    / 3500 rpm:

        42 C   12.1  12.0  11.2   9.9   7.7   3.4    (the 15 Nm floor's 8 October row)
        25 C   15.5  15.4  14.7  13.5  11.3   6.9
         0 C   20.6  20.6  20.1  19.0  16.9  12.4

    Those rows settled for 30 steps, as measure_deliverable_torque does; a reset
    settles for CLOSED_SETTLE, 12, which returned the same values to four
    decimals at 0, 7, 15, 30 and 45 C (11 October) in 0.7 s instead of 1.8. The
    block is the one the car's table is measured at (plant.car.table_t_block,
    365 K on the Supra; a default here until 21 October 2026). `env` lends its
    load loop and its plant, and is not changed by it.

    THE INLET DOES NOT ENTER (20 October 2026). With the throttle shut the loop
    drives the manifold to its floor (25 kPa), under both ceilings at any inlet
    the roads draw, so the measurement is the same whichever inlet `env` holds:
    the monkeypatch this replaced measured at the sea-level flow ceiling and the
    previous episode's cap, and the identity harness compares the floors."""
    t_block, settle = env.plant.car.table_t_block, CLOSED_SETTLE
    iat = EE.charge_temperature(t_amb, t_block, engine=env.plant.engine)
    most = 0.0
    for rpm in CLOSED_RPM:
        ecu, state, mp, knock, hist = EE.BaselineECU(env.plant.engine.ecu), {}, 30.0, False, []
        for _ in range(settle):
            sp, lam, _ = ecu.step(rpm, mp, iat, t_block, knock, 1.0)
            r, mp = env._track_torque(0.0, rpm, iat, t_block, sp, lam, 0.0, state)
            knock = r["ki"] > ecu.cal.knock_detect_ki
            hist.append(r["torque"])
        most = max(most, max(hist[settle // 2:]))
    return float(most)


def deliverable_torque(p_kpa, rpms, *, plant):
    """engine_env.measure_deliverable_torque with the compressor inlet at this
    pressure: the same load loop at a 1000 Nm request, BaselineECU.step for spark
    and lambda, the worst torque over the second half of the settled window.
    {rpm: Nm}. MEASURED 11 October at 42 C, Nm at 1800 / 2000 / 2200 / 2600 / 3000
    rpm: 271.2 316.3 375.9 413.3 442.6 at 101.3 kPa (the stored table, to 0.02 %),
    221.1 252.8 313.0 342.5 364.2 at 80 kPa. 30 settle steps, not fewer: 16 moved
    a value by 2.9 Nm (the knock feedback and the enrichment dwell need them).
    The probe is a plain environment at this inlet (inlet_kpa), which both the
    flow ceiling and the hard cap read; `plant` is required. The ambient, the
    block and the settling steps are the stored table's own (plant.car.table_*),
    so a ratio to that table compares like with like; they were defaults here,
    the B58 table's, until 21 October 2026."""
    car = plant.car
    t_amb, t_block, settle = car.table_t_amb, car.table_t_block, car.table_settle
    sc = plant.scenario
    probe = EE.SupervisoryTunerEnv(EE.make_grade_climb(duration=60.0, dt=1.0, t_amb=t_amb, grade=sc.grade,
                                                       v_kmh=sc.v_kmh),
                                   plant=plant, dt=1.0, seed=0, inlet_kpa=inlet_kpa(p_kpa, engine=plant.engine))
    probe.reset(seed=0)
    iat = EE.charge_temperature(t_amb, t_block, engine=plant.engine)
    out = {}
    for rpm in rpms:
        ecu, state, mp, knock, hist = EE.BaselineECU(plant.engine.ecu), {}, 150.0, False, []
        for _ in range(settle):
            sp, lam, _ = ecu.step(rpm, mp, iat, t_block, knock, 1.0)
            r, mp = probe._track_torque(1000.0, rpm, iat, t_block, sp, lam, 0.0, state)
            knock = r["ki"] > ecu.cal.knock_detect_ki
            hist.append(r["torque"])
        out[rpm] = float(min(hist[settle // 2:]))
    return out


_RATIOS = {}


def thin_air_ratios(plant):
    """{pressure: {rpm: deliverable torque there / the stored sea-level table}} at
    P_TABLE, measured on first use in this process for this plant (about 110 s).

    Kept by the plant itself -- a frozen record, equal to another only when every
    value is -- not by plant.id: a dataclasses.replace variant keeps the id, and
    until 21 October 2026 it was served the plant's ratios it was made from (a
    bore 10 % smaller got 0.823 at 80 kPa and 3000 rpm for its own 0.642; the
    review of build step 1)."""
    if plant not in _RATIOS:
        stored = dict(plant.car.deliverable_torque)
        out = {}
        for p_kpa in P_TABLE:
            m = deliverable_torque(p_kpa, sorted(stored), plant=plant)
            out[p_kpa] = {r: m[r] / stored[r] for r in stored}
        _RATIOS[plant] = out
    return _RATIOS[plant]


class ThinAirVehicle(EE.Vehicle):
    """Vehicle whose deliverable-torque table, the one the kickdown reads, follows
    the pressure set for the episode. At 101.3 kPa it IS the stored table. Built
    from the whole plant (required): the thin-air table is measured through it."""

    _table = None

    def __init__(self, plant):
        super().__init__(plant.car)
        self.plant = plant

    def set_pressure(self, p_kpa):
        if p_kpa >= P_SEA:
            self._table = None
            return
        ratios, grid = thin_air_ratios(self.plant), list(P_TABLE) + [P_SEA]
        self._table = tuple(
            (r, t * float(np.interp(p_kpa, grid, [ratios[p][r] for p in P_TABLE] + [1.0])))
            for r, t in EE.Vehicle.DELIVERABLE_TORQUE.fget(self))

    @property
    def DELIVERABLE_TORQUE(self):
        return self._table if self._table is not None else EE.Vehicle.DELIVERABLE_TORQUE.fget(self)


def torque_floor_nm(env, t_amb):
    """The least torque a road may ask for in this air: X1's rule at this ambient,
    never under the plant's own floor (X1's 15 Nm on the B58)."""
    return max(env.plant.engine.loop.torque_floor_nm, FLOOR_MARGIN * closed_throttle_nm(env, t_amb))


# engine_env.min_tractive_force takes the floor since 20 October 2026, so the
# copy that lived here for that reason alone is gone (mistake 10: one helper).
min_tractive_force = EE.min_tractive_force


def grade_floor(v_mps, t_amb, p_kpa, dt, veh, floor_nm):
    """engine_env.grade_floor with drag at this pressure's air density and this
    floor. `veh` and `floor_nm` are required (they were the B58's Vehicle() and
    15 Nm by default)."""
    rho = _rho(p_kpa, t_amb)
    m, g0 = veh.mass, 9.81
    v = np.asarray(v_mps, dtype=float)
    a = np.diff(v, append=v[-1]) / dt
    f_min = np.array([min_tractive_force(veh, x, floor_nm) for x in v])
    s = (f_min - m * a - 0.5 * rho * veh.cd_a * v ** 2 - veh.crr * m * g0) / (m * g0)
    return np.tan(np.arcsin(np.clip(s, -0.5, 0.5)))


def speed_profile(rng, n, dt, grade, t_amb, p_kpa, veh, floor_nm):
    """engine_env.extreme_speed_profile with drag at this pressure's air density
    and this floor; `veh` and `floor_nm` required, as in grade_floor."""
    rho = _rho(p_kpa, t_amb)
    m, g0 = veh.mass, 9.81
    v = np.empty(n)
    launch = int(20 / dt)
    target = rng.uniform(*EE.EXTREME_V_KMH) / 3.6
    v[:launch] = np.linspace(0.0, target, launch)
    nxt = launch + int(rng.uniform(*EE.EXTREME_HOLD_S) / dt)
    for i in range(launch, n):
        if i >= nxt:
            target = rng.uniform(*EE.EXTREME_V_KMH) / 3.6
            nxt = i + int(rng.uniform(*EE.EXTREME_HOLD_S) / dt)
        th = np.arctan(float(grade[i - 1]))
        road = (0.5 * rho * veh.cd_a * v[i - 1] ** 2 + veh.crr * m * g0 * np.cos(th) + m * g0 * np.sin(th))
        coast = max(0.0, (road - min_tractive_force(veh, v[i - 1], floor_nm)) / m)
        v[i] = v[i - 1] + float(np.clip(target - v[i - 1], -min(coast, EE.EXTREME_ACCEL) * dt,
                                        EE.EXTREME_ACCEL * dt))
    return v


class WideAirTrainingEnv(EE.ExtremesTrainingEnv):
    """ExtremesTrainingEnv with ambient 0-45 C and pressure 80-101.3 kPa drawn per
    episode, the compressor inlet and the gearbox's kickdown table following the
    pressure, and the torque floor following the ambient. TRAINING ONLY.

    reset(options={"t_amb_c": .., "p_kpa": ..}) sets the air of that episode
    after the draws are made, so the road stream is the same as without it;
    test_reward.py and test_wide_air.py use it to drive the corners.

    The episode's compressor inlet is the environment's own `inlet_kpa`
    (SupervisoryTunerEnv), which the flow ceiling and the hard cap both read;
    it starts at the plant's sea-level inlet and the floor at the plant's."""

    def __init__(self, duration=900.0, dt=1.0, seed=None, *, plant, **kw):
        super().__init__(duration=duration, dt=dt, seed=seed, plant=plant, **kw)
        self.veh = ThinAirVehicle(plant)

    def reset(self, *, seed=None, options=None):
        if seed is not None:
            self._road_rng = self._make_road_rng(seed)
        rng, opt = self._road_rng, (options or {})
        t_amb = 273.15 + rng.uniform(*WIDE_T_AMB_C)
        p = float(rng.uniform(*WIDE_P_KPA))
        if "t_amb_c" in opt:
            t_amb = 273.15 + float(opt["t_amb_c"])
        if "p_kpa" in opt:
            p = float(opt["p_kpa"])
        self.floor_nm = torque_floor_nm(self, t_amb)
        self.veh.set_pressure(p)
        c = EE.make_terrain(rng, duration=self.duration, dt=self.dt, v_kmh=self.v_kmh, t_amb=t_amb,
                            family=opt.get("family"), families=self.families,
                            weights=self.weights, grade_max=EE.EXTREME_GRADE_MAX, plant=self.plant)
        v = speed_profile(rng, len(c["t"]), self.dt, c["grade"], t_amb, p, self.veh, self.floor_nm)
        c["grade"] = np.maximum(c["grade"], grade_floor(v, t_amb, p, self.dt, self.veh, self.floor_nm))
        c["v_mps"], c["t_amb"], c["p_baro"] = v, t_amb, p
        c["elev_m"] = np.cumsum(v * self.dt * c["grade"])
        lo, hi = np.log(EE.EXTREME_C_TURB[0]), np.log(EE.EXTREME_C_TURB[1])
        self.c_turb_scale = float(np.exp(rng.uniform(lo, hi)))
        self.cycle = c
        self.inlet_kpa = inlet_kpa(p, engine=self.plant.engine)
        self.road_log.append(f"{c['family']} {t_amb - 273.15:.1f}C {p:.1f}kPa")
        obs, info = EE.SupervisoryTunerEnv.reset(self, seed=seed, options=options)
        # a new housing record per episode, never a change to the plant's (frozen)
        for tn in (self.thermal, self.thermal_base):
            tn.p = replace(tn.p, c_turb=self._c_turb0 * self.c_turb_scale)
        return obs, info
