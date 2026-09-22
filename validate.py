"""validate.py — regenerates the plant validation table.

Every number quoted in Chapter 3 comes out of this file. Nothing in the thesis
should cite a validation figure that this script does not print.

Run:  python validate.py

Gate B rule: after any edit to plant.py or thermal.py, re-run this and commit
the output alongside the change.

WHERE THE BANDS COME FROM. The eleven "published" bands this file scores
against are documented row by row in REFERENCES.md, section 3, with the
source each one should be checked against and whether anyone has actually
opened that source (CONFIRMED) or not (UNVERIFIED). Until 12 September the
only citation behind any of them was the word "Heywood" in a comment in this
file. Do not change a band here without changing its row there, and do not
quote a band in the thesis as "published" unless its REFERENCES.md row says
CONFIRMED with a page number. The `source` string on each row below names
the matching REFERENCES.md row: it is a pointer, not a citation.
"""
import numpy as np

from plant import Operating, run_cycle, b58, Geometry

GEO = b58()          # the one engine; never rely on run_cycle's default
from thermal import ThermalNetwork

IDX = {"block": 0, "oil": 1, "turb": 2}


def _row(name, value, unit, lo, hi, source):
    inside = (lo <= value <= hi)
    return dict(name=name, value=value, unit=unit, lo=lo, hi=hi,
                ok=inside, source=source)


# ---------------------------------------------------------------- geometry
def check_displacement():
    g = b58()
    disp_cc = np.pi / 4 * g.bore ** 2 * g.stroke * g.n_cyl * 1e6
    return _row("Displacement", disp_cc, "cc", 2990, 3000,
                "REFERENCES.md sec. 3 row 1 (B58 factory figure; see sec. 2)")


# ---------------------------------------------------------------- combustion
def check_mfb50():
    """MFB50 at MBT timing -- the crank angle at which half the fuel mass has
    burned, at the spark timing that gives maximum brake torque. Published SI
    engines burn so that this lands 8-10 deg after TDC at best torque.
    Band: REFERENCES.md section 3, row 2 (general engine physics; the book
    to open is Heywood, listed in section 1, and nobody has yet)."""
    best = None
    for s in range(8, 46):
        r = run_cycle(Operating(rpm=2500, map_kpa=60, spark_btdc=s, lam=1.0), geo=GEO)
        if best is None or r.torque_nm > best[1]:
            best = (s, r.torque_nm, r.mfb50_deg)
    return _row("MFB50 at MBT (2500 rpm, 60 kPa)", best[2], "deg aTDC", 8.0, 10.0,
                "REFERENCES.md sec. 3 row 2"), best[0]


def check_bsfc():
    """Best BSFC (brake specific fuel consumption: fuel used per unit of work
    delivered) anywhere on the knock-feasible, stoichiometric map.
    Modern turbo SI: 235-260 g/kWh island.
    Band: REFERENCES.md section 3, row 3 (general engine physics)."""
    best = None
    for n in (1500, 2000, 2500, 3000, 3500, 4000, 4500):
        for m in (60, 80, 100, 120, 140, 160, 180):
            for s in range(6, 42, 2):
                r = run_cycle(Operating(rpm=n, map_kpa=m, spark_btdc=s, lam=1.0,
                                        p_exh_kpa=max(105, m * 1.15)), geo=GEO)
                if r.knock_integral < 1.0 and r.torque_nm > 0:
                    if best is None or r.bsfc_gpkwh < best[0]:
                        best = (r.bsfc_gpkwh, n, m, s)
    return _row("Best BSFC (knock-feasible, lambda 1)", best[0], "g/kWh", 235, 260,
                "REFERENCES.md sec. 3 row 3"), best[1:]


def check_knock_limit():
    """Knock-limited spark at 200 kPa MAP, 3000 rpm, lambda 0.85 -- the most
    the spark can be advanced before knock (uncontrolled detonation) starts.
    Production turbo SI runs 8-14 deg BTDC there.
    Band: REFERENCES.md section 3, row 4. NOTHING SUPPORTS THIS BAND YET:
    Douaud & Eyzat supply the knock model, not this number. Weakest row."""
    limit = None
    for s in range(2, 30):
        r = run_cycle(Operating(rpm=3000, map_kpa=200, spark_btdc=s, lam=0.85,
                                p_exh_kpa=230), geo=GEO)
        if r.knock_integral >= 1.0:
            limit = s - 1
            break
    return _row("Knock-limited spark (3000 rpm, 200 kPa)", float(limit), "deg BTDC",
                8, 14, "REFERENCES.md sec. 3 row 4 (unsupported)")


def check_egt():
    """EGT (exhaust gas temperature) at moderate cruise. Port-exit gas
    600-750 C is the normal band.
    Band: REFERENCES.md section 3, rows 5 and 6 (general engine physics)."""
    vals = [run_cycle(Operating(rpm=n, map_kpa=m, spark_btdc=22, lam=1.0), geo=GEO).egt_c
            for n, m in ((2000, 70), (2200, 75), (2500, 80), (2500, 100))]
    return (_row("EGT, cruise band (min)", min(vals), "C", 600, 750, "REFERENCES.md sec. 3 row 5"),
            _row("EGT, cruise band (max)", max(vals), "C", 600, 750, "REFERENCES.md sec. 3 row 6"))


# ---------------------------------------------------------------- thermal
def _step_response(key, horizon_s, dt=0.25):
    """Sustained hard climb, held long enough to reach steady state.

    THE CONDITION CHANGED ON 8 SEPTEMBER, AND THE REASON MATTERS.

    This used to be 4000 rpm at 190 kPa with lambda 0.85 — wide-open throttle.
    On the 2.0 L four-cylinder the file used to default to, that was 121 kW and
    the resulting temperatures looked plausible. On the real 3.0 L six it is
    **186 kW held for 83 minutes**, which no road car does and no published
    "sustained climb" figure describes. Oil came out at 182 C: the model was
    right, the test was absurd.

    The condition is now a hard sustained climb — 3000 rpm, 140 kPa,
    stoichiometric, 108 kW, 7.6 g/s of fuel. One anchor holds it there: it is
    the load `thermal.py`'s own worked example uses.

    THE SECOND ANCHOR NO LONGER HOLDS, AND SAY SO RATHER THAN QUIETLY KEEPING
    IT.  RETIRED-OK: 6.5, 7 -- the ceiling quoted in the next sentence is the
    one, kept because the point of the paragraph is that it moved.
    This docstring used to add that the condition "sits above the hardest
    sustained load actually recorded on the car", on a ceiling of 6.5 g/s
    measured over the seven drives that existed then. Across the dataset's own
    samples -- ten drives, 295.0 minutes, seven carrying samples -- the hardest
    60-second mean fuel flow is **8.7 g/s**, on 7475b5d7, the averaging window
    sized from each drive's own rate. The test condition is therefore BELOW what
    the car has actually done for a minute, not above it, by about 13 %.

    Nothing here is changed to chase that: the condition is still the one the
    published bands describe, and the time constants it reports are a property
    of the network rather than of the load. But a tau measured at 7.6 g/s is not
    evidence about 8.7 g/s, and the thesis should quote the condition with the
    figure — "48.0 s at 3000 rpm, 140 kPa, 108 kW" — rather than implying the
    test bounds the vehicle.

    The published bands describe this condition. Match the condition to the
    band, not the band to the model.
    """
    tn = ThermalNetwork()
    tn.reset(t_amb=315.0, warm=True)
    r = run_cycle(Operating(rpm=3000, map_kpa=140, spark_btdc=14, lam=1.0,
                            p_exh_kpa=161), geo=GEO)
    mf = r.mdot_fuel_gps
    egt_k = r.egt_c + 273.15
    me = mf * (1.0 + 14.7 * 1.0)      # lambda must match the Operating above
    x = []
    for _ in range(int(horizon_s / dt)):
        # 25 m/s and full fan: climbing, not cruising. Ram air scales with road
        # speed, so a climb rejects less heat than a motorway cruise at the same
        # power, which is exactly why sustained climbs are the limiting case.
        tn.step(dt, mf, me, egt_k, t_amb=315.0, vehicle_mps=25.0, fan_duty=1.0)
        x.append(tn.state()[IDX[key]] - 273.15)
    x = np.array(x)
    t = np.arange(len(x)) * dt
    x0, xf = x[0], x[-1]
    target = x0 + 0.632 * (xf - x0)
    hit = np.nonzero(x >= target)[0] if xf > x0 else np.nonzero(x <= target)[0]
    tau = float(t[hit[0]]) if len(hit) else float("nan")
    return x0, xf, tau


def check_time_constants():
    """The five thermal rows. A time constant is the time a lump of metal (or
    oil, or coolant) takes to cover 63 % of a step change in temperature.
    Bands: REFERENCES.md section 3, rows 7-11, all B58-specific. Row 7, the
    turbine housing, is the tau in H/tau and is the highest-priority row in
    that file: if its band is wrong, every point on the H/tau curve moves.
    """
    out = []
    t0, tf, tau_t = _step_response("turb", 1500)
    out.append(_row("Turbine housing time constant", tau_t, "s", 40, 120,
                    "REFERENCES.md sec. 3 row 7 (HIGHEST PRIORITY)"))
    o0, of_, tau_o = _step_response("oil", 5000)
    out.append(_row("Oil temperature, sustained climb", of_, "C", 115, 140,
                    "REFERENCES.md sec. 3 row 8"))
    out.append(_row("Oil time constant", tau_o, "s", 20, 400,
                    "REFERENCES.md sec. 3 row 9 (no tight published band)"))
    b0, bf, tau_b = _step_response("block", 5000)
    out.append(_row("Coolant, thermostat-regulated", bf, "C", 88, 108,
                    "REFERENCES.md sec. 3 row 10"))
    # AUDIT.md L10: this row is labelled a "time constant" but measures the
    # time to cover 63 % of a 4.5 K change from a WARM start, with the stand-in
    # thermostat actively regulating -- against a band of 1-600 s that almost
    # nothing could fail. It counts toward "8 of 11" and should not be read as
    # evidence about the cooling system. Relabelled rather than dropped, so the
    # count stays comparable with earlier versions of the table.
    out.append(_row("Coolant regulation response (NOT a free time constant)",
                    tau_b, "s", 1, 600,
                    "REFERENCES.md sec. 3 row 11 (band too wide to assert much)"))
    return out, dict(turb=(t0, tf, tau_t), oil=(o0, of_, tau_o), block=(b0, bf, tau_b))


# ---------------------------------------------------------------- report
def rows():
    """The validation rows, as data. AUDIT.md H2.

    `main()` computed these and printed them, so nothing could check them
    without re-implementing them. `verify_docs.py` imports this instead, which
    is what closes the gap that let tau and "8 of 11" drift unseen.
    """
    out = [check_displacement()]
    mfb_row, _ = check_mfb50()
    out.append(mfb_row)
    bsfc_row, _ = check_bsfc()
    out.append(bsfc_row)
    out.append(check_knock_limit())
    out.extend(check_egt())
    thermal_rows, _ = check_time_constants()
    out.extend(thermal_rows)
    return [dict(name=r["name"], model=r["value"], inside=r["ok"]) for r in out]


def main():
    rows = [check_displacement()]
    mfb_row, mbt_spark = check_mfb50()
    rows.append(mfb_row)
    bsfc_row, bsfc_where = check_bsfc()
    rows.append(bsfc_row)
    rows.append(check_knock_limit())
    rows.extend(check_egt())
    thermal_rows, detail = check_time_constants()
    rows.extend(thermal_rows)

    w = max(len(r["name"]) for r in rows)
    print("=" * (w + 46))
    print("PLANT VALIDATION TABLE — regenerated from code")
    print("=" * (w + 46))
    print(f"{'quantity'.ljust(w)}  {'model':>9}  {'published':>13}   status")
    print("-" * (w + 46))
    for r in rows:
        band = f"{r['lo']:g}-{r['hi']:g}"
        status = "inside" if r["ok"] else "OUTSIDE"
        print(f"{r['name'].ljust(w)}  {r['value']:9.1f}  {band:>13}   {status}")
    print("-" * (w + 46))
    n_ok = sum(r["ok"] for r in rows)
    print(f"{n_ok} of {len(rows)} quantities inside the published band")

    print("\nConditions behind the headline numbers")
    print(f"  MBT spark at 2500 rpm / 60 kPa   : {mbt_spark} deg BTDC")
    print(f"  Best BSFC found at               : {bsfc_where[0]} rpm, "
          f"{bsfc_where[1]} kPa, {bsfc_where[2]} deg BTDC")
    for k, (a, b, t) in detail.items():
        print(f"  {k:6s} step {a:7.1f} -> {b:7.1f} C   tau = {t:6.1f} s")

    print("\nKnown limitation, state it in Chapter 3")
    print("  MAP is an INPUT to this model. There is no compressor flow ceiling,")
    print("  so peak power is not a model prediction — it is whatever boost is")
    print("  commanded. Full-load points are therefore not validated here.")


def test_convergence(tol_egt_k=12.0, tol_torque_pct=0.6):
    """AUDIT.md H1: halving the crank-angle step must not move a headline more
    than the precision that headline is quoted to.

    The cycle integration is explicit Euler and therefore first order, so this
    cannot pass by accident -- if the step is too coarse the error roughly
    doubles and this fails. It is the regression the audit asked for, and it is
    the reason DTHETA_DEG is a studied number rather than a round one.
    """
    from plant import Operating, run_cycle, b58, DTHETA_DEG
    geo = b58()
    pts = [dict(rpm=2500, map_kpa=60, spark_btdc=30),
           dict(rpm=2465, map_kpa=150, spark_btdc=8),
           dict(rpm=3000, map_kpa=200, spark_btdc=12)]
    print("\nCRANK-ANGLE CONVERGENCE  (AUDIT.md H1)")
    ok = True
    for kw in pts:
        op = Operating(iat_k=320.0, ect_k=363.0, lam=1.0,
                       p_exh_kpa=max(105.0, kw["map_kpa"] * 1.15), **kw)
        a = run_cycle(op, geo=geo, dtheta=DTHETA_DEG)
        b = run_cycle(op, geo=geo, dtheta=DTHETA_DEG / 2.0)
        d_egt = abs(b.egt_c - a.egt_c)
        d_trq = abs(b.torque_nm - a.torque_nm) / max(a.torque_nm, 1e-9) * 100.0
        good = d_egt <= tol_egt_k and d_trq <= tol_torque_pct
        ok &= good
        print(f"  {'ok  ' if good else 'WRONG'}  {kw['rpm']:>5} rpm / "
              f"{kw['map_kpa']:>3} kPa   halving the step moves EGT "
              f"{d_egt:5.1f} K (<= {tol_egt_k}), torque {d_trq:5.2f} % "
              f"(<= {tol_torque_pct})")
    print(f"  dtheta = {DTHETA_DEG} deg. Residual error against a much finer step "
          f"is ~7 K of EGT; quote figures accordingly.")
    return ok


if __name__ == "__main__":
    main()
