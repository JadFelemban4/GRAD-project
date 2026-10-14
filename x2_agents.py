"""x2_agents.py -- what X2's agents did, measured: the numbers behind results/X2_AGENTS.md.

    python x2_agents.py                 -> results/x2_agents.json and a printed report (about 2 min)
    python x2_agents.py --trajectory    also scores each agent's checkpoints at 180 000, 360 000
                                        and 540 000 steps on check_x2_convergence's practice set,
                                        beside its own 720 000 / 900 000 / 1 080 000 (about 15 min)

Written 13 October 2026, AFTER X2's result: a description of what the agents
did, never a test, and nothing here changes PREREGISTRATION_X2.md's reading.
Each explanation in X2_AGENTS.md names quantities, and each is measured here
first (mistake 24 in CLAUDE.md: an explanation of an agent is measured on its
outputs, not read off its inputs).

Reads, all written before this script existed:
  runs/wideair_dt1/<tag>/train_record.npz   every training step (gitignored; the training laptop)
  runs/wideair_dt1/log_<tag>.txt            stable-baselines3's statistics, every 4 episodes
  results/agents/wideair_dt1/               index.json, each agent's eval_summary.json and
                                            eval_record.npz (every step of the 20 frozen episodes)
  results/logged_check_wideair_dt1.json     the logged-drive check, with the actuators applied
  results/x2_convergence.txt                the convergence check's three points

Definitions, fixed here before the numbers were looked at:
  binding episode   the parallel baseline car's housing passes 850 C (1123.15 K) in it
  scored-like       a binding episode at 38 C or more and 97 kPa or more: the air of the
                    scored climb (42 C, 101.3 kPa), give or take
  protection cut    100 x (1 - agent damage / the parallel baseline car's), per episode
  fuel overspend    100 x (agent fuel / the parallel baseline car's - 1), per episode
  thirds            training episodes 0-399, 400-799, 800-1200
  onset             the first step from 120 s on at which the applied lambda trim is at or
                    under -0.02 or the boost trim at or under -5 kPa
"""
import argparse
import glob
import json
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs", "wideair_dt1")
AG = os.path.join(HERE, "results", "agents", "wideair_dt1")
OUT = os.path.join(HERE, "results", "x2_agents.json")
TAGS = [f"{arm}_seed{s}" for s in range(5) for arm in ("sighted", "blind")]
TRIGGER_K = 1123.15
P_IDX = 10                                   # engine_env._obs: (p_baro - 101.3) / 8
THIRDS = ((0, 400), (400, 800), (800, 1201))


def r(x, n=2):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def episodes(tag):
    """One row per training episode, from the per-step record."""
    keep = ("episode", "t_amb_c", "t_turb_base", "damage_cum", "damage_base_cum", "fuel_cum",
            "fuel_base_cum", "weights", "grade", "v_kmh", "reward", "applied", "obs")
    z = np.load(os.path.join(RUNS, tag, "train_record.npz"))
    d = {k: z[k] for k in keep}
    ep = d["episode"]
    last = np.r_[np.nonzero(np.diff(ep))[0], len(ep) - 1]
    first = np.r_[0, last[:-1] + 1]
    p = d["obs"][:, P_IDX].astype(np.float64) * 8.0 + 101.3
    rows = []
    for a, b in zip(first, last):
        if b - a < 800:                      # the cut-off last episode of a run
            continue
        dmg, dmg_b = float(d["damage_cum"][b]), float(d["damage_base_cum"][b])
        fu, fu_b = float(d["fuel_cum"][b]), float(d["fuel_base_cum"][b])
        peak_b = float(np.max(d["t_turb_base"][a:b + 1]))
        app = d["applied"][a:b + 1]
        rows.append(dict(ep=int(ep[a]), t_amb=float(d["t_amb_c"][a]), p=float(np.median(p[a:b + 1])),
                         peak_b=peak_b, binding=peak_b > TRIGGER_K, dmg=dmg, dmg_b=dmg_b,
                         cut=100 * (1 - dmg / dmg_b) if dmg_b > 1.0 else None,
                         over=100 * (fu / fu_b - 1) if fu_b > 0 else None,
                         w_life=float(d["weights"][a][2]), ret=float(np.sum(d["reward"][a:b + 1])),
                         lam=float(np.median(app[:, 1])), boost=float(np.median(app[:, 2])),
                         spark=float(np.median(app[:, 0]))))
    return rows


def training(tag):
    E = episodes(tag)
    out = dict(episodes=len(E), binding=sum(e["binding"] for e in E),
               scored_like=sum(e["binding"] and e["t_amb"] >= 38.0 and e["p"] >= 97.0 for e in E),
               cold=sum(e["t_amb"] < 19.0 for e in E), thin=sum(e["p"] < 90.0 for e in E), thirds=[])
    for lo, hi in THIRDS:
        part = [e for e in E if lo <= e["ep"] < hi]
        hot = [e["cut"] for e in part if e["binding"] and e["cut"] is not None]
        cool = [e["over"] for e in part if not e["binding"] and e["over"] is not None]
        cold = [e["over"] for e in part if e["t_amb"] < 19.0 and e["over"] is not None]
        lam_cool = [e["lam"] for e in part if not e["binding"]]
        out["thirds"].append(dict(n=len(part), n_binding=len(hot),
                                  hot_cut=r(np.median(hot), 1) if hot else None,
                                  cool_over=r(np.median(cool), 2) if cool else None,
                                  cold_over=r(np.median(cold), 2) if cold else None,
                                  cool_lam=r(np.median(lam_cool), 3) if lam_cool else None))
    sl = [e["cut"] for e in E[-400:] if e["binding"] and e["t_amb"] >= 38.0 and e["p"] >= 97.0 and e["cut"] is not None]
    out["scored_like_cut_last_third"] = r(np.median(sl), 1) if sl else None
    out["scored_like_n_last_third"] = len(sl)
    return out


def sb3(tag):
    """ent_coef, critic and actor loss, and the mean episode return, as stable-baselines3 logged them."""
    with open(os.path.join(RUNS, f"log_{tag}.txt"), encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    series = {}
    for key in ("ent_coef", "critic_loss", "actor_loss", "ep_rew_mean"):
        series[key] = [float(v) for v in re.findall(rf"\|\s+{key}\s+\|\s+(-?[\d.e+-]+)\s+\|", txt)]
    n = min(len(v) for v in series.values())
    k = max(1, n // 10)
    # first / mid / last: the median over the first, middle and last tenth of the entries
    return {key: dict(first=r(np.median(v[:k]), 4), mid=r(np.median(v[n // 2 - k // 2:n // 2 + k // 2 + 1]), 4),
                      last=r(np.median(v[n - k:n]), 4)) for key, v in series.items()} | dict(
        entries=n, ent_coef_first_entry=r(series["ent_coef"][0], 4),
        critic_loss_min_entry=r(min(series["critic_loss"][:n]), 4), critic_loss_max_entry=r(max(series["critic_loss"][:n]), 4))


def scored(tag, base_eps):
    """What the agent did on the twenty frozen episodes of the locked climb."""
    z = np.load(os.path.join(AG, tag, "eval_record.npz"))
    app, w = z["applied"], z["weights"]
    onset = []
    for e in range(app.shape[0]):
        hit = np.nonzero((app[e, 120:, 1] <= -0.02) | (app[e, 120:, 2] <= -5.0))[0]
        onset.append(float(120 + hit[0]) if hit.size else None)
    pre = app[:, 150:180, :]
    climb = app[:, 190:, :]
    eps = json.load(open(os.path.join(AG, tag, "eval_summary.json"), encoding="utf-8"))["episodes"]
    worse = []
    for i, (e, b) in enumerate(zip(eps, base_eps)):
        if e["damage"] > b["damage"]:
            worse.append(dict(episode=i + 1, w_life=r(w[i][2], 3), damage=r(e["damage"], 1), base=r(b["damage"], 1),
                              fuel_over=r(100 * (z["fuel_cum"][i, -1] / z["fuel_base_cum"][i, -1] - 1), 2),
                              climb_spark=r(np.median(app[i, 190:, 0]), 2), climb_lam=r(np.median(app[i, 190:, 1]), 3),
                              climb_boost=r(np.median(app[i, 190:, 2]), 1)))
    on = [x for x in onset if x is not None]
    # Anticipation: how the applied lambda and boost trims change from 90-119 s to
    # 150-179 s, as the climb (ramped from 180 s) comes into the preview's 30 s.
    # A blinded agent cannot see it coming; any change of its own is drift.
    req, got = z["torque_req"], z["torque"]
    short = (got < 0.95 * req) & (req > 40.0)
    return dict(pre_dlam=r(app[:, 150:180, 1].mean() - app[:, 90:120, 1].mean(), 4),
                pre_dboost=r(app[:, 150:180, 2].mean() - app[:, 90:120, 2].mean(), 2),
                track_175_240=r(float((w[:, 0:1] * z["r_resp"])[:, 175:240].sum(axis=1).mean()), 3),
                life_175_240=r(float((w[:, 2:3] * z["r_life"])[:, 175:240].sum(axis=1).mean()), 3),
                short_175_240=r(float(short[:, 175:240].sum(axis=1).mean()), 1),
                onset_median=r(np.median(on), 0) if on else None, onset_none=sum(x is None for x in onset),
                pre_lam=r(np.mean(pre[:, :, 1]), 4), pre_boost=r(np.mean(pre[:, :, 2]), 2),
                climb_spark=r(np.median(climb[:, :, 0]), 2), climb_lam=r(np.median(climb[:, :, 1]), 3),
                climb_boost=r(np.median(climb[:, :, 2]), 1), climb_fan=r(np.median(climb[:, :, 3]), 2),
                worse=worse)


def logged(tag, L):
    rs = [x for x in L["runs"] if x["policy"] == tag]
    act = np.array([x["act_cold"] for x in rs], dtype=float)
    over = [100 * (x["fuel"] / x["fuel_base"] - 1) for x in rs]
    eps = L["cycles"]["episodes"]
    by_w = {k: [100 * (x["fuel"] / x["fuel_base"] - 1) for x in rs if x["episode"] == eps[k]]
            for k in ("life_most", "life_least")}
    return dict(runs=len(rs), T_fail=sum(not x["T"] for x in rs), F_fail=sum(not x["F"] for x in rs),
                fuel_over_median=r(np.median(over), 2),
                fuel_over_life_most=r(np.median(by_w["life_most"]), 2) if by_w["life_most"] else None,
                fuel_over_life_least=r(np.median(by_w["life_least"]), 2) if by_w["life_least"] else None,
                cold_spark=r(np.median(act[:, 0]), 2), cold_lam=r(np.median(act[:, 1]), 4),
                cold_boost=r(np.median(act[:, 2]), 2), cold_fan=r(np.median(act[:, 3]), 3))


# Where the reward's life term starts to count: r_life = (d_b - d_a) / (d_b + 0.05)
# (engine_env.SupervisoryTunerEnv.step), so damage avoided pays only once the
# baseline car's damage rate d_b is comparable with 0.05 a second. The turbine
# term exp((T - 1123) / 45) reaches 0.05 at 1123 + 45 ln 0.05 = 988 K, 715 C.
BANDS_C = ((-1e9, 500.0, "under 500 C"), (500.0, 715.0, "500-715 C"), (715.0, 1e9, "715 C and over"))


def logged_bands(tag):
    """The logged drives, step by step: where the agent's extra fuel went, by the
    parallel baseline car's housing temperature, what it applied there, and what
    the reward paid there (weighted fuel and life terms, per step)."""
    rows = {}
    for f in sorted(glob.glob(os.path.join(HERE, "results", "records", "logged", "wideair_dt1", f"{tag}__*.npz"))):
        z = np.load(f)
        ep = os.path.basename(f).rsplit("__", 1)[1].split(".")[0]
        tb = z["t_turb_base"][0]
        tb_c = tb - 273.15 if np.nanmax(tb) > 400 else tb
        extra = np.diff(np.r_[0.0, z["fuel_cum"][0]]) - np.diff(np.r_[0.0, z["fuel_base_cum"][0]])
        w = z["weights"][0]
        wf, wl = w[1] * z["r_fuel"][0], w[2] * z["r_life"][0]
        app = z["applied"][0]
        for lo, hi, name in BANDS_C:
            m = (tb_c >= lo) & (tb_c < hi)
            b = rows.setdefault((ep, name), dict(steps=0, extra=0.0, wf=0.0, wl=0.0, lam=[], spark=[], boost=[]))
            b["steps"] += int(m.sum())
            b["extra"] += float(extra[m].sum())
            b["wf"] += float(wf[m].sum())
            b["wl"] += float(wl[m].sum())
            b["lam"] += app[m, 1].tolist()
            b["spark"] += app[m, 0].tolist()
            b["boost"] += app[m, 2].tolist()
    out = {}
    for (ep, name), b in rows.items():
        tot = sum(v["extra"] for (e, _), v in rows.items() if e == ep)
        out.setdefault(ep, {})[name] = dict(
            steps=b["steps"], extra_share=r(100 * b["extra"] / tot, 1) if tot > 0 else None,
            wfuel_per_step=r(b["wf"] / b["steps"], 5) if b["steps"] else None,
            wlife_per_step=r(b["wl"] / b["steps"], 5) if b["steps"] else None,
            lam=r(np.median(b["lam"]), 4) if b["lam"] else None,
            spark=r(np.median(b["spark"]), 2) if b["spark"] else None,
            boost=r(np.median(b["boost"]), 2) if b["boost"] else None)
    return out


def reward_cool(tag):
    """Training, last third, episodes where the baseline car never passed 850 C:
    the weighted fuel and life terms per step, by the baseline car's housing band."""
    z = np.load(os.path.join(RUNS, tag, "train_record.npz"))
    ep, tb = z["episode"], z["t_turb_base"]
    tb_c = tb - 273.15 if np.nanmax(tb) > 400 else tb
    last = ep >= 800
    peak = {}
    for e in np.unique(ep[last]):
        peak[int(e)] = float(np.max(tb_c[ep == e]))
    cool = last & np.isin(ep, [e for e, pk in peak.items() if pk < 850.0])
    w = z["weights"]
    wf, wl = w[:, 1] * z["r_fuel"], w[:, 2] * z["r_life"]
    out = {}
    for lo, hi, name in BANDS_C:
        m = cool & (tb_c >= lo) & (tb_c < hi)
        out[name] = dict(steps=int(m.sum()), wfuel_per_step=r(float(wf[m].mean()), 5) if m.any() else None,
                         wlife_per_step=r(float(wl[m].mean()), 5) if m.any() else None)
    return out


def _terms(t_turb_k, t_oil_k):
    """engine_env.damage_rate's turbine and oil terms, per second."""
    return np.exp((t_turb_k - 1123.0) / 45.0), 0.4 * np.exp((t_oil_k - 408.0) / 12.0)


def _kelvin(x, floor):
    x = np.asarray(x, dtype=np.float64)
    return x if np.nanmax(x) > floor else x + 273.15


def damage_split(z, mask, step_damage_base):
    """Mean damage rate per second by term, the baseline car's and the agent's, on
    the masked steps. The agent's knock term is computed from its knock integral;
    the baseline car's knock integral is not recorded, so its knock term is what
    is left of its recorded damage rate after the turbine and oil terms."""
    tb, ob = _kelvin(z["t_turb_base"], 400), _kelvin(z["t_oil_base"], 300)
    ta, oa = _kelvin(z["t_turb"], 400), _kelvin(z["t_oil"], 300)
    tu_b, oi_b = _terms(tb, ob)
    tu_a, oi_a = _terms(ta, oa)
    kn_a = 40.0 * np.maximum(0.0, np.asarray(z["ki"], dtype=np.float64) - 0.85) ** 2
    kn_b = np.maximum(step_damage_base - tu_b - oi_b, 0.0)
    m = mask
    return dict(steps=int(m.sum()), turb_base=r(tu_b[m].mean(), 5), oil_base=r(oi_b[m].mean(), 5),
                knock_base=r(kn_b[m].mean(), 5), turb_agent=r(tu_a[m].mean(), 5), oil_agent=r(oi_a[m].mean(), 5),
                knock_agent=r(kn_a[m].mean(), 5))


def logged_damage_split(tag, ep="ep4"):
    """On the logged drives at one weighting, steps where the baseline car's housing
    is under 500 C: which damage term the agent avoided there."""
    acc = []
    for f in sorted(glob.glob(os.path.join(HERE, "results", "records", "logged", "wideair_dt1", f"{tag}__*__{ep}.npz"))):
        z = np.load(f)
        zz = {k: z[k][0] for k in ("t_turb_base", "t_oil_base", "t_turb", "t_oil", "ki", "damage_base_cum")}
        d_b = np.diff(np.r_[0.0, zz["damage_base_cum"]])
        m = (_kelvin(zz["t_turb_base"], 400) - 273.15) < 500.0
        acc.append(damage_split(zz, m, d_b))
    n = sum(a["steps"] for a in acc)
    return {k: (n if k == "steps" else r(sum(a[k] * a["steps"] for a in acc) / n, 5)) for k in acc[0]} if n else None


def training_damage_split(tag):
    """Training, last third, episodes where the baseline car never passed 850 C."""
    z = np.load(os.path.join(RUNS, tag, "train_record.npz"))
    ep = z["episode"]
    zz = {k: z[k] for k in ("t_turb_base", "t_oil_base", "t_turb", "t_oil", "ki", "damage_base_cum")}
    d_b = np.diff(np.r_[0.0, zz["damage_base_cum"]])
    start = np.r_[True, np.diff(ep) != 0]
    d_b[start] = zz["damage_base_cum"][start]               # each episode's total starts from zero
    tb_c = _kelvin(zz["t_turb_base"], 400) - 273.15
    last = ep >= 800
    hot = {int(e) for e in np.unique(ep[last]) if tb_c[ep == e].max() >= 850.0}
    m = last & ~np.isin(ep, list(hot))
    return damage_split(zz, m, d_b)


def training_knock_spikes(tag):
    """Training, last third: the baseline car's knock term per step (its recorded
    damage rate less the turbine and oil terms), how much of it sits on steps
    above 0.5 a second, the torque-request step into those steps, and what each
    of those steps coincides with.

    engine_env.step serves the acceleration (v[k+1] - v[k]) / dt, with v recorded
    at the step's start: a step's acceleration is the NEXT recorded speed less
    this one. The causes are exclusive, taken in this order:
      speed-up starts   the acceleration rises by more than 0.1 m/s^2, into a speed-up
      slow-down ends    the acceleration rises by more than 0.1 m/s^2, and the car is
                        not speeding up (a coast or a slowdown ends)
      gear shift        the gear changes and the acceleration does not rise
      grade ramp        the grade rises, and neither of the above
    A pair's twins drive the same roads beside the same baseline car, so both arms
    of a seed print the same numbers here."""
    z = np.load(os.path.join(RUNS, tag, "train_record.npz"))
    with open(os.path.join(RUNS, tag, "config.json"), encoding="utf-8") as fh:
        dt = float(json.load(fh)["dt"])
    ep, tq = z["episode"], z["torque_req"].astype(np.float64)
    tb, ob = _kelvin(z["t_turb_base"], 400), _kelvin(z["t_oil_base"], 300)
    d_b = np.diff(np.r_[0.0, z["damage_base_cum"]])
    st = np.r_[True, np.diff(ep) != 0]
    en = np.r_[np.diff(ep) != 0, True]
    d_b[st] = z["damage_base_cum"][st]
    tu, oi = _terms(tb, ob)
    kn = np.maximum(d_b - tu - oi, 0.0)
    dtq = np.r_[0.0, np.diff(tq)]
    dtq[st] = 0.0
    last = ep >= 800
    spk = last & (kn > 0.5)
    v = z["v_kmh"].astype(np.float64) / 3.6
    acc = np.r_[np.diff(v), 0.0] / dt
    acc[en] = 0.0
    dacc = np.r_[0.0, np.diff(acc)]
    dacc[st] = 0.0
    dg = np.r_[0.0, np.diff(z["grade"].astype(np.float64))]
    dg[st] = 0.0
    gear = z["gear"]
    shift = np.r_[False, gear[1:] != gear[:-1]]
    shift[st] = False
    on, rise = dacc > 0.1, dg > 1e-6
    causes = (("speed-up starts", on & (acc > 0.05)), ("slow-down ends", on & (acc <= 0.05)),
              ("gear shift", shift & ~on), ("grade ramp", rise & ~on & ~shift), ("none of these", ~on & ~shift & ~rise))
    tot = kn[last].sum()
    return dict(steps=int(last.sum()), spike_steps=int(spk.sum()), spike_share_of_steps=r(100 * spk.sum() / last.sum(), 2),
                spike_share_of_knock=r(100 * kn[spk].sum() / tot, 1) if tot > 0 else None,
                torque_step_median=r(np.median(dtq[spk]), 1) if spk.any() else None,
                on_rise_20=r(100 * (dtq[spk] >= 20).mean(), 1) if spk.any() else None,
                n_rise_20=int((dtq[spk] >= 20).sum()),
                causes={name: dict(spike_pct=r(100 * (spk & m).sum() / spk.sum(), 1) if spk.any() else None,
                                   knock_pct=r(100 * kn[spk & m].sum() / tot, 1) if tot > 0 else None)
                        for name, m in causes})


def ecu_knock_on_drives():
    """The baseline ECU's knock integral on the logged drives, in cold running,
    read from current-grade's records: it applies nothing there, and its knock term
    equals the baseline car's."""
    ki, cold, k1, c1, dtq, dmap, first = [], [], [], [], [], [], 0.0
    for f in sorted(glob.glob(os.path.join(HERE, "results", "records", "logged", "wideair_dt1", "current-grade__*__ep4.npz"))):
        z = np.load(f)
        k, cd = z["ki"][0], (_kelvin(z["t_turb_base"][0], 400) - 273.15) < 500.0
        ki.append(k)
        cold.append(cd)
        k1.append(k[1:])                                   # each step paired with the step into it
        c1.append(cd[1:])
        dtq.append(np.diff(z["torque_req"][0]))
        dmap.append(np.diff(z["map_kpa"][0]))
        first += 40.0 * max(0.0, float(k[0]) - 0.85) ** 2  # the replay's first step has no step into it
    k, c = np.concatenate(ki), np.concatenate(cold)
    kp, cp, t, m = (np.concatenate(x) for x in (k1, c1, dtq, dmap))
    term = 40.0 * np.maximum(0.0, k - 0.85) ** 2
    sp = cp & (kp > 0.85)
    term_sp = 40.0 * np.maximum(0.0, kp[sp] - 0.85) ** 2
    return dict(steps=int(c.sum()), ki_median=r(np.median(k[c]), 3), above_085_pct=r(100 * (k[c] > 0.85).mean(), 1),
                above_1_pct=r(100 * (k[c] > 1.0).mean(), 1), knock_term_mean=r(term[c].mean(), 4),
                share_above_15=r(100 * term[c & (k > 1.5)].sum() / term[c].sum(), 1),
                share_first_steps=r(100 * first / term[c].sum(), 1),
                share_spikes=r(100 * term_sp.sum() / term[c].sum(), 1), spikes=int(sp.sum()),
                spikes_on_rise_20=int((t[sp] >= 20).sum()), torque_step_median=r(np.median(t[sp]), 1),
                torque_step_typical=r(np.median(np.abs(t[cp])), 1), map_step_median=r(np.median(m[sp]), 1),
                ki_max=r(k[c].max(), 2))


def trajectory():
    """Checkpoints at 180k/360k/540k on the practice set, scored exactly as check_x2_convergence scores."""
    from multiprocessing import Pool
    import check_x2_convergence as C
    base = C.baseline_damage()
    jobs = [(t, os.path.join(RUNS, t, f"ckpt_{k}_steps.zip"), k) for t in TAGS for k in (180_000, 360_000, 540_000)]
    with Pool(max(1, min(18, (os.cpu_count() or 4) - 2))) as pool:
        out = pool.map(C.score, jobs)
    return {f"{t}@{k}": r(100 * (1 - d / base), 2) for t, k, d, _ in out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trajectory", action="store_true")
    a = ap.parse_args()
    idx = json.load(open(os.path.join(AG, "index.json"), encoding="utf-8"))
    base_eps = json.load(open(os.path.join(AG, "baseline_ECU", "eval_summary.json"), encoding="utf-8"))["episodes"]
    L = json.load(open(os.path.join(HERE, "results", "logged_check_wideair_dt1.json"), encoding="utf-8"))
    res = dict(grade_cut=idx["policies"]["current-grade"]["cut_pct"], agents={}, ecu_knock=ecu_knock_on_drives())
    for tag in TAGS:
        res["agents"][tag] = dict(cut=r(idx["policies"][tag]["cut_pct"], 2), training=training(tag),
                                  sb3=sb3(tag), scored=scored(tag, base_eps), logged=logged(tag, L),
                                  logged_bands=logged_bands(tag),
                                  logged_damage=dict(ep4=logged_damage_split(tag, "ep4"),
                                                     ep15=logged_damage_split(tag, "ep15")),
                                  training_cool=dict(reward=reward_cool(tag), damage=training_damage_split(tag),
                                                     knock_spikes=training_knock_spikes(tag)))
        print(f"done {tag}", flush=True)
    # The logged-drive check's fuel over all ten agents, at the two weightings it runs.
    eps = L["cycles"]["episodes"]
    res["logged_all"] = {}
    for key in ("life_most", "life_least"):
        o = [100 * (x["fuel"] / x["fuel_base"] - 1) for x in L["runs"] if x["policy"] in TAGS and x["episode"] == eps[key]]
        res["logged_all"][key] = dict(episode=eps[key], runs=len(o), over_1pct=sum(v > 1.0 for v in o),
                                      median=r(np.median(o), 2), worst=r(max(o), 2))
    if a.trajectory:
        res["trajectory"] = trajectory()
    elif os.path.isfile(OUT):
        prev = json.load(open(OUT, encoding="utf-8"))
        if "trajectory" in prev:
            res["trajectory"] = prev["trajectory"]
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
        fh.write("\n")
    g = res["grade_cut"]
    print(f"\ncurrent-grade cuts {g:.2f} % on the scored climb")
    print(f"{'agent':15s}{'cut':>7s}{'bind':>6s}{'sc-lk':>6s} {'hot cut by third':>22s} {'cool fuel over by third':>26s}"
          f"{'ent last':>9s}{'onset':>7s}{'pre lam':>9s}{'cold lam':>9s}{'cold spk':>9s}")
    for tag, x in res["agents"].items():
        t, s, sc, lg = x["training"], x["sb3"], x["scored"], x["logged"]
        hc = " ".join(f"{h['hot_cut'] if h['hot_cut'] is not None else float('nan'):6.1f}" for h in t["thirds"])
        co = " ".join(f"{h['cool_over'] if h['cool_over'] is not None else float('nan'):+7.2f}" for h in t["thirds"])
        print(f"{tag:15s}{x['cut']:7.1f}{t['binding']:6d}{t['scored_like']:6d} {hc:>22s} {co:>26s}"
              f"{s['ent_coef']['last']:9.4f}{(sc['onset_median'] or float('nan')):7.0f}{sc['pre_lam']:9.4f}"
              f"{lg['cold_lam']:9.4f}{lg['cold_spark']:9.2f}")
    print("\nWHERE THE EXTRA FUEL WENT on the logged drives, life weighted most (episode 4): share of the")
    print("agent's extra fuel by the baseline car's housing band, and the damage terms it avoided under 500 C")
    for tag, x in res["agents"].items():
        b, dm = x["logged_bands"].get("ep4", {}), x["logged_damage"]["ep4"]
        shares = "  ".join(f"{k}: {v['extra_share']}%" for k, v in b.items())
        print(f"  {tag:15s} {shares}   knock {dm['knock_base']:.4f} -> {dm['knock_agent']:.4f}, "
              f"oil {dm['oil_base']:.4f} -> {dm['oil_agent']:.4f}, turbine {dm['turb_base']:.5f} -> {dm['turb_agent']:.5f} /s")
    print("\nTRAINING, last third, episodes that never passed 850 C: damage terms per second, baseline -> agent")
    for tag, x in res["agents"].items():
        dm = x["training_cool"]["damage"]
        print(f"  {tag:15s} knock {dm['knock_base']:.4f} -> {dm['knock_agent']:.4f}   turbine {dm['turb_base']:.4f} -> "
              f"{dm['turb_agent']:.4f}   oil {dm['oil_base']:.4f} -> {dm['oil_agent']:.4f}")
    print("\nTRAINING, last third: the baseline car's knock spikes (its knock term over 0.5 a second), by what each falls on")
    for tag, x in res["agents"].items():
        ks = x["training_cool"]["knock_spikes"]
        cs = ", ".join(f"{k} {v['knock_pct']}" for k, v in ks["causes"].items())
        print(f"  {tag:15s} {ks['spike_steps']} steps ({ks['spike_share_of_steps']} %) carry {ks['spike_share_of_knock']} % "
              f"of its knock; {ks['n_rise_20']} on torque rises >= 20 Nm; % of its knock on: {cs}")
    e = res["ecu_knock"]
    print(f"\nTHE BASELINE ECU on the logged drives, cold running: knock integral median {e['ki_median']}, over 0.85 on "
          f"{e['above_085_pct']} % of steps; of its knock term {e['share_first_steps']} % on each replay's first step and "
          f"{e['share_spikes']} % on {e['spikes']} later steps, {e['spikes_on_rise_20']} of them torque rises >= 20 Nm")
    for key, v in res["logged_all"].items():
        print(f"  logged drives, {key} (frozen episode {v['episode']}): {v['over_1pct']} of {v['runs']} agent runs over 1 % "
              f"more fuel than the ECU, median {v['median']:+.2f} %, worst {v['worst']:+.2f} %")
    if "trajectory" in res:
        print("\nPRACTICE CUT ALONG TRAINING (180k, 360k, 540k from --trajectory; 720k, 900k, 1080k from x2_convergence.txt)")
        conv = {}
        cp = os.path.join(HERE, "results", "x2_convergence.txt")
        for ln in open(cp, encoding="utf-8").read().splitlines():
            m = re.match(r"^((?:sighted|blind)_seed\d+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s", ln)
            if m:
                conv[m[1]] = [float(m[2]), float(m[3]), float(m[4])]
        for tag in TAGS:
            pts = [res["trajectory"][f"{tag}@{k}"] for k in (180_000, 360_000, 540_000)] + conv.get(tag, [])
            res["agents"][tag]["practice_path"] = pts
            print(f"  {tag:15s} " + " ".join(f"{p:6.1f}" for p in pts) + f"   range {max(pts) - min(pts):5.1f}")
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
            fh.write("\n")
    print(f"\nwrote {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
