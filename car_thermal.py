"""car_thermal.py -- thermal.py driven over the car's own logs. ONE definition.

Imported by validate.py (the four thermal rows scored against the car) and by
model_vs_data.py (the comparisons and the figures), so the validation table and
the results page can never quote two different replays of the same drive.

WHAT IS FED IN, AND WHY FUEL IS MEASURED RATHER THAN MODELLED
-------------------------------------------------------------
Every input is a logged channel on a 1 s grid: engine speed, air mass flow,
lambda, coolant, oil, ambient, road speed. The fuel the engine burned is formed
from two MEASURED channels, air mass flow over (14.7 x lambda). Until
28 September the replays took fuel from the combustion model instead, and the
two differ where it matters: on overrun the car cuts fuel and its lambda channel
reads ~16, so measured fuel goes to zero, while the model path fell back to
lambda 1 and kept burning. On drive10 the modelled oil came out 1.7 K warmer that
way. Measured fuel is also some fifty times faster -- no combustion cycles --
which is what lets validate.py, and so verify_docs.py, run these rows every time.

One known bias, stated: the MAF channel pins at 1020 kg/h (mistake 7), so the
few seconds at the top of a wide-open pull under-report fuel.

The turbine node is not driven here. No channel on the car measures it, so there
is nothing to compare it with, and the block and oil nodes do not depend on it.
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "data", "master_samples.csv")

# The drive the sustained-load rows use, chosen on its merits before any row was
# scored: the only drive whose oil reaches the published 115-140 C band, the
# longest (two hours), and logged with ten channels, so oil and coolant are each
# read every couple of seconds.
SUSTAINED_DRIVE = "drive10-20260918_233912.csv"

# Every drive carrying both oil and coolant. The oil time constant is identified
# on each separately.
OIL_DRIVES = ("cb67b01f-20260908_084142.csv", "3aca2ec1-20260907_072817.csv",
              "683640a0-20260907_070212.csv", "7475b5d7-20260908_142743.csv",
              "drive10-20260918_233912.csv")

# Candidate time constants, in seconds. Wide enough that a drive with too little
# excitation shows its best fit at an EDGE of the grid, which is how such a
# drive is recognised and left out.
TAU_GRID_S = (2, 5, 8, 11, 14, 18, 25, 35, 50, 70, 100, 140, 200, 280, 400, 560, 800)

_CACHE = {}


def samples():
    if "S" not in _CACHE:
        _CACHE["S"] = pd.read_csv(SAMPLES)
    return _CACHE["S"]


def log_grid(source):
    """One drive on a 1 s grid (the latest reading at or before each second).

    AUDIT.md M8: BimmerLink writes exact zeros into a column until the car first
    answers for that channel, so an exact 0 C coolant, oil or ambient is a
    placeholder and is removed.
    """
    S = samples()
    d = S[S.source == source].sort_values("t").reset_index(drop=True)
    for col in ("ect_c", "oil_c", "t_amb"):
        d.loc[d[col] == 0.0, col] = np.nan
    t = d.t.to_numpy() - d.t.iloc[0]
    grid = np.arange(0.0, t[-1], 1.0)
    idx = np.clip(np.searchsorted(t, grid, side="right") - 1, 0, len(d) - 1)
    g = d.iloc[idx].reset_index(drop=True)
    g["tr"] = grid
    return g


def measured_fuel_gps(air_gps, lam, rpm):
    """Fuel burned, g/s: MEASURED air mass flow over (14.7 x MEASURED lambda)."""
    from plant import AFR_STOICH
    air = np.where(np.isfinite(air_gps) & (np.nan_to_num(rpm) > 400.0), air_gps, 0.0)
    lam = np.where(np.isfinite(lam) & (lam > 0.5), lam, 1.0)
    return air / (AFR_STOICH * lam)


def thermal_replay(source, params=None, pin_block=False):
    """Block and oil nodes of thermal.py, driven over one logged drive.

    FREE-RUNNING by default: nothing is reset to a measurement after the seed,
    which is taken from the first real coolant and oil readings (mistake 15). With
    pin_block=True the block node is set to the measured coolant every second,
    so the radiator -- unidentifiable from these logs, thermal.py -- drops out and
    the oil node is tested on its own.

    The fan duty comes from BaselineECU.step, the one definition of the fan rule.
    """
    from thermal import ThermalNetwork
    from engine_env import BaselineECU
    from plant import charge_temperature
    d = log_grid(source)
    fuel = measured_fuel_gps(d.air_gps.to_numpy(), d.lam.to_numpy(), d.rpm.to_numpy())
    amb = d.t_amb.ffill().bfill().fillna(30.0).to_numpy() + 273.15
    ect = d.ect_c.to_numpy() + 273.15
    oil = d.oil_c.to_numpy() + 273.15
    v = d.v_kmh.fillna(0.0).to_numpy() / 3.6
    rpm = d.rpm.fillna(0.0).to_numpy()
    mp = d.map_kpa.fillna(40.0).to_numpy()

    tn, ecu = ThermalNetwork(params), BaselineECU()
    tn.reset(t_amb=float(amb[0]), warm=True)
    tn.t_block = float(ect[np.isfinite(ect)][0])
    tn.t_oil = float(oil[np.isfinite(oil)][0])
    n = len(d)
    oil_m, blk_m = np.empty(n), np.empty(n)
    for i in range(n):
        if pin_block and np.isfinite(ect[i]):
            tn.t_block = ect[i]
        if rpm[i] > 400.0:
            _, _, fan = ecu.step(rpm[i], mp[i], charge_temperature(amb[i], tn.t_block),
                                 tn.t_block, False, 1.0)
        else:
            fan = 0.0
        tn.step(1.0, fuel[i], fuel[i] * 15.0, tn.t_turb, amb[i], v[i], fan)
        oil_m[i], blk_m[i] = tn.t_oil, tn.t_block
    return dict(t=d.tr.to_numpy(), fuel=fuel, t_amb=amb, ect_car=ect, oil_car=oil,
                ect_model=blk_m, oil_model=oil_m)


def _lowpass(x, tau):
    a = 1.0 / (1.0 + tau)                     # dt = 1 s, backward Euler
    y = np.empty_like(x)
    y[0] = x[0]
    for i in range(1, len(x)):
        y[i] = y[i - 1] + a * (x[i] - y[i - 1])
    return y


def identify_tau(fuel, t_block, t_amb, t_node, taus=TAU_GRID_S):
    """The first-order time constant that best explains a node's temperature.

    Fits  T ~ lowpass_tau(a*T_block + b*fuel + c*T_amb) + d  for each candidate
    tau and keeps the best. Returns (tau, rmse, interior): `interior` is False
    when the best fit sits at an edge of the grid, which means the drive did not
    excite the node enough to say.

    CHECKED ON THE MODEL FIRST. Applied to the model's own oil, with the block
    pinned to measured coolant, it recovers the analytic c_oil/(ua_block_oil +
    ua_oil_amb) = 14 s on four of five drives and 11 s on the fifth. A method
    that could not recover a known answer would not be trusted on the car.
    """
    ok = np.isfinite(t_node)
    tb = np.where(np.isfinite(t_block), t_block, np.nanmedian(t_block))
    best, k_best = None, 0
    for k, tau in enumerate(taus):
        X = np.column_stack([_lowpass(tb, tau), _lowpass(fuel, tau),
                             _lowpass(t_amb, tau), np.ones(len(fuel))])
        coef, *_ = np.linalg.lstsq(X[ok], t_node[ok], rcond=None)
        rmse = float(np.sqrt(np.mean((t_node[ok] - X[ok] @ coef) ** 2)))
        if best is None or rmse < best[1]:
            best, k_best = (float(tau), rmse), k
    return best[0], best[1], 0 < k_best < len(taus) - 1


def oil_time_constants(drives=OIL_DRIVES):
    """Apparent oil time constant per drive: identified from the car's oil, and
    from the model's oil by the same method with the block pinned to coolant."""
    out = []
    for src in drives:
        r = thermal_replay(src, pin_block=True)
        tau_c, rmse_c, interior = identify_tau(r["fuel"], r["ect_car"], r["t_amb"], r["oil_car"])
        tau_m, _, _ = identify_tau(r["fuel"], r["ect_car"], r["t_amb"], r["oil_model"])
        out.append(dict(drive=src, tau_car=tau_c, tau_model=tau_m, rmse_car=rmse_c,
                        identifiable=bool(interior)))
    return out


def hottest_window(values, window_s=600):
    """Index slice of the window_s-second stretch where a signal's rolling
    median is highest -- the drive's most sustained load, by the car's own
    measure rather than by anything the model says."""
    roll = pd.Series(values).rolling(window_s, min_periods=window_s // 2).median().to_numpy()
    end = int(np.nanargmax(roll))
    return slice(max(0, end - window_s + 1), end + 1)
