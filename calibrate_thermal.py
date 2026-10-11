"""calibrate_thermal.py -- the block and oil nodes of thermal.py, fitted to the car.

    python calibrate_thermal.py            # a few minutes; writes results/thermal_calibration.json

WHY THIS EXISTS (28 September 2026)
-----------------------------------
Replayed over the car's own drives, thermal.py's oil spiked to 140 C on hard
pulls where the sump read 107 C, its coolant spiked to 102 C where the car's
barely moved, and at a four-minute idle on drive10 the model cooled 13 K while
the car held 93.5 C. validate.py rows 8, 9 and 11 all sat outside the car's own
bands. Every parameter behind that was ASSUMED except ua_block_oil (REFERENCES.md
section 4), and the logs carry oil, coolant, ambient, road speed, engine speed,
air mass and lambda on 7 drives -- enough to fit them.

THE DATA CHANGED THE OIL NODE'S STRUCTURE, NOT ONLY ITS NUMBERS
---------------------------------------------------------------
thermal.py heated the oil with a fixed 5 % of FUEL energy and cooled it to
ambient through a constant 60 W/K. The car says otherwise:

    drive10, minutes 1-14   3700-4800 rpm at 70-100 km/h, fuel 3-5 g/s   oil 11-15 K ABOVE coolant
    3aca2ec1, cruise        2600 rpm at 127-142 km/h, fuel 2-3 g/s       oil 2-3 K BELOW coolant

Oil heat follows ENGINE SPEED (bearing friction, piston-ring friction, windage
and churning all rise steeply with rpm), and the sump is cooled by ROAD SPEED
(it sits in the airstream under the car). A fuel share cannot produce the first
row without spiking on every short pull, which is exactly the 140 C artefact.
Four structures were fitted with the block pinned to measured coolant and scored
on drive10 held out; engine-speed heating with road-speed cooling won (RMSE
2.78 K against 3.30 K for the fuel share with the same cooling, and 7.55 K for
thermal.py as it was). The oil node is now

    c_oil dT/dt = frac_fuel_to_oil * q_fuel + k_oil_rpm * (rpm/3000)^n_oil_rpm
                  + ua_block_oil * (T_block - T) - (ua_oil_amb + ua_oil_ram * v) * (T - T_amb)

WHAT IS FITTED, IN THREE STAGES
-------------------------------
  1. OIL, with the block PINNED to the measured coolant, so the unidentifiable
     radiator drops out:  c_oil, frac_fuel_to_oil, k_oil_rpm, n_oil_rpm,
     ua_block_oil, ua_oil_amb, ua_oil_ram.
  2. BLOCK, with the oil PINNED to the measured oil and ua_block_oil from stage
     1:  c_block, frac_fuel_to_coolant, ua_block_amb, t_stat_open, t_stat_span.
  3. BOTH FREE-RUNNING, as car_thermal.thermal_replay and the environment run
     them -- the check, not a fit.

HELD, because the logs cannot identify them (thermal.py, logs/CHANNEL_CENSUS.md):
ua_rad_min / ua_rad_ram / ua_rad_fan -- no coolant-flow or fan signal exists on
this car. c_block and the regulation point are therefore relative to that
assumed radiator. The turbine node is not touched: no channel measures it.

WHAT THE DATA IDENTIFIES. Divided through by its capacity, each node has only
ratios (heat input over capacity, conductance over capacity). c_oil is pinned
only weakly, through ua_block_oil's appearance in the block equation. Quote the
time constants and the heat splits; quote a capacity on its own only with that
caveat.

INPUTS ARE MEASURED. Fuel = air mass / (14.7 x lambda) from two logged channels
(car_thermal.measured_fuel_gps); engine speed, road speed and ambient are logged
channels. Drive B (28 Sep) is excluded: it logged no ambient temperature, and no
oil. Drives are read from logs/raw/ (car_thermal.raw_grid), so the warm-up in
683640a0 -- the one stretch where the radiator is shut -- is in the fit.

HOW HONEST THE ROWS ARE AFTERWARDS. The final parameters are fitted on ALL seven
drives, including drive10, because drive10 is the only drive with sustained high
engine speed at low road speed -- the region where the oil structure is decided.
validate.py rows 8 and 11 score drive10, so after this they are IN-SAMPLE. This
script therefore also refits with each drive left out in turn and reports that
drive's held-out score, including drive10's rows 8 and 11 as a genuine
prediction. Quote both.

THE METHOD. Output error, free-running from the first real reading; objective is
the mean over drives of each drive's RMSE, so a long drive does not outvote a
short one. Search is a cross-entropy method over a population simulated in
parallel (numpy, no scipy), log-scaled for every positive parameter.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import car_thermal as CT                      # noqa: E402

# WHICH DRIVES, DECIDED BY THE DATA, NOT BY A LIST. Every raw log that carries
# coolant, oil and ambient temperature for at least MIN_MINUTES qualifies, so a
# drive that arrives with those channels joins the fit the next time
# derive_params.py runs, and one that lacks them (drive B, pull01) is left out
# for a stated reason. On 28 September this selects 7 drives.
MIN_MINUTES = 5.0


def usable_drives():
    """(qualifying drives, {excluded drive: reason}) from logs/raw/."""
    import glob
    keep, why = [], {}
    for path in sorted(glob.glob(os.path.join(HERE, "logs", "raw", "*.csv"))):
        src = os.path.basename(path)
        g = CT.raw_grid(src)
        miss = [n for n, c in (("coolant", "ect_c"), ("oil", "oil_c"), ("ambient", "t_amb"))
                if not np.isfinite(g[c]).any()]
        if miss:
            why[src] = "no " + " / ".join(miss) + " channel"
        elif len(g) < MIN_MINUTES * 60:
            why[src] = f"{len(g) / 60:.1f} min, shorter than {MIN_MINUTES:.0f}"
        else:
            keep.append(src)
    return tuple(keep), why

# The radiator group, held at thermal.py's reasoned values (unidentifiable).
UA_RAD_MIN, UA_RAD_RAM, UA_RAD_FAN = 300.0, 60.0, 700.0

# name, low, high, log-space?
OIL_SPACE = (
    ("c_oil", 3e3, 600e3, True),
    ("frac_fuel_to_oil", 1e-5, 0.10, True),
    ("k_oil_rpm", 10.0, 20000.0, True),
    ("n_oil_rpm", 0.5, 5.0, False),
    ("ua_block_oil", 20.0, 4000.0, True),
    ("ua_oil_amb", 0.1, 200.0, True),
    ("ua_oil_ram", 0.01, 60.0, True),
)
BLOCK_SPACE = (
    ("c_block", 20e3, 600e3, True),
    ("frac_fuel_to_coolant", 0.05, 0.50, True),
    ("ua_block_amb", 0.5, 200.0, True),
    ("t_stat_open", 350.0, 372.0, False),
    ("t_stat_span", 0.5, 25.0, True),
    # One multiplier on the whole radiator group (min, ram, fan). The three terms
    # cannot be told apart -- no coolant-flow or fan signal exists -- but their
    # overall size CAN be: wherever the car's coolant climbs above its regulated
    # point (drive10's sustained 4000+ rpm stretch, 97-99 C), the radiator is
    # fully open and its capacity is what sets the temperature.
    ("ua_rad_scale", 0.05, 4.0, True),
)


def load_drive(src):
    """Per-second measured inputs and temperatures for one drive, from the raw log."""
    g = CT.raw_grid(src)
    amb = g.t_amb.ffill().bfill()
    if not np.isfinite(amb).any():
        return None
    rpm = g.rpm.fillna(0.0).to_numpy()
    ect = g.ect_c.to_numpy() + 273.15
    oil = g.oil_c.to_numpy() + 273.15
    if not np.isfinite(oil).any():
        return None
    i0 = int(np.argmax(np.isfinite(ect) & np.isfinite(oil)))
    sl = slice(i0, None)
    fuel = CT.measured_fuel_gps(g.air_gps.to_numpy(), g.lam.to_numpy(), rpm)
    d = dict(src=src, fuel=fuel[sl], rpm=rpm[sl], amb=amb.to_numpy()[sl] + 273.15,
             v=g.v_kmh.fillna(0.0).to_numpy()[sl] / 3.6, ect=ect[sl], oil=oil[sl])
    d["ect_filled"] = pd.Series(d["ect"]).ffill().bfill().to_numpy()
    d["oil_filled"] = pd.Series(d["oil"]).ffill().bfill().to_numpy()
    return d


def _oil_step(to, tb, i, d, P):
    q = d["fuel"][i] * 44.0e3
    r = d["rpm"][i] / 3000.0 if d["rpm"][i] > 400.0 else 0.0
    q_in = P["frac_fuel_to_oil"] * q + P["k_oil_rpm"] * r ** P["n_oil_rpm"]
    ua_amb = P["ua_oil_amb"] + P["ua_oil_ram"] * d["v"][i]
    return to + (q_in + P["ua_block_oil"] * (tb - to) - ua_amb * (to - d["amb"][i])) / P["c_oil"]


def _block_step(tb, to, i, d, P):
    q = d["fuel"][i] * 44.0e3
    running = d["rpm"][i] > 400.0
    stat = np.clip((tb - P["t_stat_open"]) / P["t_stat_span"], 0.0, 1.0)
    fan = np.where(tb > 372.0, 1.0, np.where(tb > 367.0, 0.4, 0.0)) * running
    ua_rad = P["ua_rad_scale"] * stat * (UA_RAD_MIN + UA_RAD_RAM * d["v"][i] + UA_RAD_FAN * fan)
    return tb + (P["frac_fuel_to_coolant"] * q - (ua_rad + P["ua_block_amb"]) * (tb - d["amb"][i])
                 - P["ua_block_oil"] * (tb - to)) / P["c_block"]


def simulate(d, P, mode):
    """mode: 'oil' (block pinned), 'block' (oil pinned), 'free' (both free).
    Returns RMSE coolant, RMSE oil (NaN where not simulated) and, for a single
    member, the traces.

    ONE EXPLICIT-EULER STEP PER 1 s SAMPLE, NOT SUB-STEPPED (found 9 October
    2026). Since 8 October thermal.ThermalNetwork splits every step into
    sub-steps of at most thermal.DT_SUB_MAX (0.1 s); this fit does not, so the
    derived block and oil constants are fitted with a different integrator
    from the one the plant runs them in. Re-fitted with ten sub-steps per
    sample (substep_fit_check.py, a diagnostic, not shipped): the oil constants move under 2 %, the
    coolant constants a lot (ua_rad_scale +61 %, ua_block_amb -42 %,
    t_stat_span -13 %, c_block +13 %), the fit's coolant RMSE 2.96 -> 3.00 K,
    and the locked climb's baseline 848.1 -> 845.6 with current-grade's cut
    +0.01 points. Sub-stepping here changes derived_sha, which refuses every
    agent trained on the present constants: do it with the next plant change,
    and re-train, as for a new drive."""
    n = len(np.atleast_1d(P["c_oil"] if "c_oil" in P else P["c_block"]))
    tb = np.full(n, d["ect"][0])
    to = np.full(n, d["oil"][0])
    se_b, se_o, nb, no = np.zeros(n), np.zeros(n), 0, 0
    tr_b, tr_o = [], []
    for i in range(len(d["fuel"])):
        tb_now = d["ect_filled"][i] if mode == "oil" else tb
        to_now = d["oil_filled"][i] if mode == "block" else to
        if mode in ("oil", "free"):
            to = _oil_step(to, tb_now, i, d, P)
        if mode in ("block", "free"):
            tb = _block_step(tb, to_now, i, d, P)
        if mode != "oil" and np.isfinite(d["ect"][i]):
            se_b += (tb - d["ect"][i]) ** 2; nb += 1
        if mode != "block" and np.isfinite(d["oil"][i]):
            se_o += (to - d["oil"][i]) ** 2; no += 1
        if n == 1:
            tr_b.append(float(np.atleast_1d(tb)[0])); tr_o.append(float(np.atleast_1d(to)[0]))
    rb = np.sqrt(se_b / nb) if nb else np.full(n, np.nan)
    ro = np.sqrt(se_o / no) if no else np.full(n, np.nan)
    return rb, ro, (np.array(tr_b), np.array(tr_o))


def _decode(z, space):
    out = {}
    for k, (name, lo, hi, lg) in enumerate(space):
        x = np.clip(z[:, k], 0.0, 1.0)
        out[name] = np.exp(np.log(lo) + x * (np.log(hi) - np.log(lo))) if lg else lo + x * (hi - lo)
    return out


def _search(drives, space, mode, fixed, pop=1500, iters=22, seed=0):
    """Cross-entropy search; `fixed` holds the other node's parameters."""
    rng = np.random.default_rng(seed)
    dim = len(space)
    mu, sd = np.full(dim, 0.5), np.full(dim, 0.35)
    best = (np.inf, None)
    for _ in range(iters):
        z = np.clip(mu + sd * rng.standard_normal((pop, dim)), 0.0, 1.0)
        if best[1] is not None:
            z[0] = best[1]
        P = _decode(z, space)
        P.update({k: np.full(pop, v) for k, v in fixed.items()})
        j = np.mean([simulate(d, P, mode)[1 if mode == "oil" else 0] for d in drives], axis=0)
        o = np.argsort(j)
        if j[o[0]] < best[0]:
            best = (float(j[o[0]]), z[o[0]].copy())
        el = z[o[:max(4, pop // 25)]]
        mu = 0.7 * el.mean(axis=0) + 0.3 * mu
        sd = np.maximum(0.7 * el.std(axis=0) + 0.15 * sd, 0.003)
    p = {k: float(v[0]) for k, v in _decode(best[1][None, :], space).items()}
    return p, best[0]


def fit(drives, seed=0, pop=1500, iters=22):
    """Stage 1 (oil, block pinned) then stage 2 (block, oil pinned)."""
    oil, j_oil = _search(drives, OIL_SPACE, "oil", {}, pop, iters, seed)
    blk, j_blk = _search(drives, BLOCK_SPACE, "block",
                         {"ua_block_oil": oil["ua_block_oil"]}, pop, iters, seed + 100)
    return {**oil, **blk}, j_oil, j_blk


def one(p):
    return {k: np.array([v]) for k, v in p.items()}


def tau_oil(p, v_mps=0.0):
    return p["c_oil"] / (p["ua_block_oil"] + p["ua_oil_amb"] + p["ua_oil_ram"] * v_mps)


def shipped_params():
    """thermal.py as it stood before this calibration, in this file's terms."""
    return dict(c_oil=12000.0, frac_fuel_to_oil=0.05, k_oil_rpm=0.0, n_oil_rpm=1.0,
                ua_block_oil=800.0, ua_oil_amb=60.0, ua_oil_ram=0.0,
                c_block=105000.0, frac_fuel_to_coolant=0.26, ua_block_amb=45.0,
                t_stat_open=361.0, t_stat_span=9.0, ua_rad_scale=1.0)


def main():
    t0 = time.time()
    names, excluded = usable_drives()
    drives = [d for d in (load_drive(s) for s in names) if d is not None]
    print(f"drives: {', '.join(d['src'][:8] for d in drives)}")
    for src, why in excluded.items():
        print(f"   excluded {src[:8]}: {why}")

    ship = shipped_params()
    print("\nfitting on all drives (stage 1 oil, block pinned; stage 2 block, oil pinned)")
    best, j_oil, j_blk = fit(drives)
    print(f"   stage 1 oil RMSE (mean over drives) {j_oil:.2f} K;  stage 2 coolant RMSE {j_blk:.2f} K")

    print("\nleave-one-drive-out: each drive scored FREE-RUNNING by parameters fitted without it")
    loo = []
    for k, d in enumerate(drives):
        p, _, _ = fit(drives[:k] + drives[k + 1:], seed=k + 1, pop=1000, iters=16)
        rb, ro, _ = simulate(d, one(p), "free")
        loo.append(dict(drive=d["src"], rmse_coolant=float(rb[0]), rmse_oil=float(ro[0]), params=p))
        print(f"   {d['src'][:8]}  coolant {rb[0]:5.2f} K  oil {ro[0]:5.2f} K   "
              f"oil tau {tau_oil(p):4.0f} s   stat open {p['t_stat_open'] - 273.15:5.1f} C")

    rows = []
    print(f"\n{'drive':<10}{'ship ect':>10}{'fit ect':>9}{'LOO ect':>9}{'ship oil':>10}{'fit oil':>9}{'LOO oil':>9}"
          "   (free-running RMSE, K)")
    for d, lo in zip(drives, loo):
        sb, so, _ = simulate(d, one(ship), "free")
        fb, fo, _ = simulate(d, one(best), "free")
        rows.append(dict(drive=d["src"], shipped=dict(coolant=float(sb[0]), oil=float(so[0])),
                         fitted=dict(coolant=float(fb[0]), oil=float(fo[0])),
                         held_out=dict(coolant=lo["rmse_coolant"], oil=lo["rmse_oil"])))
        print(f"{d['src'][:8]:<10}{sb[0]:10.2f}{fb[0]:9.2f}{lo['rmse_coolant']:9.2f}"
              f"{so[0]:10.2f}{fo[0]:9.2f}{lo['rmse_oil']:9.2f}")

    print("\nparameter                 before        fitted")
    for k in list(ship):
        print(f"  {k:<22}{ship[k]:>11.4g}  {best[k]:>11.4g}")
    print(f"  oil tau at rest, s     {tau_oil(ship):>11.1f}  {tau_oil(best):>11.1f}")
    print(f"  oil tau at 130 km/h, s {tau_oil(ship, 36.1):>11.1f}  {tau_oil(best, 36.1):>11.1f}")

    out = dict(drives=[d["src"] for d in drives], before=ship, fitted=best,
               stage1_oil_rmse=j_oil, stage2_coolant_rmse=j_blk, per_drive=rows,
               leave_one_out=loo, held_constant=dict(ua_rad_min=UA_RAD_MIN, ua_rad_ram=UA_RAD_RAM,
                                                     ua_rad_fan=UA_RAD_FAN),
               excluded=excluded)
    path = os.path.join(HERE, "results", "thermal_calibration.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nwrote {os.path.relpath(path, HERE)}   ({(time.time() - t0) / 60:.1f} min)")


if __name__ == "__main__":
    main()
