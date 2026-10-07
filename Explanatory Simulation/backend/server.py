"""127.0.0.1-only HTTP bridge for the local GRAD explainer."""
from __future__ import annotations

import math
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from pathlib import Path

from . import simulation


app = FastAPI(title="GRAD explainer bridge", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SessionRequest(StrictModel):
    scenario: str = "locked"
    preview: bool = True
    policy: str = "manual"
    seed: int = Field(default=0, ge=0, le=2**32 - 1)


class StepRequest(StrictModel):
    steps: int = Field(default=1, ge=1, le=simulation.MAX_STEPS_PER_CALL)
    controls: dict[str, Any] | None = None


class PlantRequest(StrictModel):
    rpm: float = Field(ge=800, le=7000)
    map_kpa: float = Field(ge=25, le=300)
    ambient_c: float = Field(default=25, ge=-20, le=60)
    ect_c: float = Field(default=90, ge=-20, le=150)
    spark: float = Field(default=10, ge=-20, le=50)
    lam: float = Field(default=1.0, ge=0.6, le=1.5)


class ThermalRequest(StrictModel):
    rpm: float = Field(ge=800, le=7000)
    map_kpa: float = Field(ge=25, le=300)
    ambient_c: float = Field(default=25, ge=-20, le=60)
    spark: float = Field(default=10, ge=-20, le=50)
    lam: float = Field(default=1.0, ge=0.6, le=1.5)
    fan: float = Field(default=1.0, ge=0, le=1)
    pump: float = Field(default=1.0, ge=0.3, le=1)
    heat_s: float = Field(default=30, ge=0, le=300)
    cool_s: float = Field(default=60, ge=0, le=300)


class ReplayRequest(StrictModel):
    trip_id: str = Field(min_length=1, max_length=100)
    preempt: bool = False


def _catalog_call(name, *args):
    try:
        from . import catalog
        fn = getattr(catalog, name)
    except (ImportError, AttributeError) as exc:
        raise HTTPException(status_code=503, detail=f"catalog is not ready: {exc}") from None
    try:
        return fn(*args)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@app.get("/api/meta")
def api_meta(locale: str = Query(default="en", pattern="^(en|ar)$")):
    data = dict(_catalog_call("metadata", locale))
    data["bridge"] = {
        "host": "127.0.0.1", "port": 8765, "dt": simulation.SIM_DT,
        "scenarios": ["locked", "flat", "terrain"],
        "policies": ["baseline", "current-grade", "reactive", "predictive", "manual"]
                     + [f"{arm}_seed{i}" for arm in ("sighted", "blind") for i in range(10)],
        "max_steps_per_call": simulation.MAX_STEPS_PER_CALL,
        "simulation_only": True,
    }
    return data


@app.get("/api/results")
def api_results():
    return _catalog_call("results")


@app.get("/api/source")
def api_source(file: str = Query(min_length=1, max_length=200), line: int = Query(default=1, ge=1)):
    return _catalog_call("source", file, line)


def _road_payload(session):
    cycle = session.env.cycle
    return dict(session.road,
                time_s=cycle["t"].astype(float).tolist(),
                grade_pct=(cycle["grade"] * 100.0).astype(float).tolist(),
                speed_kmh=(cycle["v_mps"] * 3.6).astype(float).tolist())


@app.post("/api/session")
def api_create_session(body: SessionRequest):
    try:
        session = simulation.create_session(scenario=body.scenario, preview=body.preview,
                                            policy=body.policy, seed=body.seed)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return {"id": session.id, "frame": simulation.reset_frame(session), "road": _road_payload(session),
            "policy": session.policy, "preview": session.preview,
            "provenance": session.provenance}


@app.post("/api/session/{session_id}/step")
def api_step(session_id: str, body: StepRequest):
    try:
        session = simulation.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    try:
        result = simulation.step_session(session, steps=body.steps, controls=body.controls)
        if body.controls and ("speed_kmh" in body.controls or "grade_pct" in body.controls):
            result["road"] = _road_payload(session)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@app.delete("/api/session/{session_id}")
def api_delete_session(session_id: str):
    with simulation._LOCK:
        if session_id not in simulation._SESSIONS:
            raise HTTPException(status_code=404, detail="unknown or expired session")
        del simulation._SESSIONS[session_id]
    return {"deleted": True}


@app.post("/api/plant")
def api_plant(body: PlantRequest):
    from plant import boost_ceiling_kpa, charge_temperature, predict

    iat_k = float(charge_temperature(body.ambient_c + 273.15))
    out = predict(body.rpm, body.map_kpa, iat_k,
                  body.ect_c + 273.15, body.spark, body.lam)
    nonfinite = [k for k, v in out.items()
                 if isinstance(v, (int, float)) and not math.isfinite(float(v))]
    values = {k: float(v) for k, v in out.items()
              if isinstance(v, (int, float)) and math.isfinite(float(v))}
    ceiling = float(boost_ceiling_kpa(values["mdot_air_gps"], body.ambient_c + 273.15))
    warnings = []
    if not 30.0 <= body.map_kpa <= 75.0:
        warnings.append(
            "This MAP is outside the 30–75 kPa range of the documented 26-point "
            "air-filling/air-mass residual comparison; that check does not establish accuracy here."
        )
    excess = max(0.0, float(body.map_kpa) - ceiling)
    if excess > 1e-6:
        warnings.append(
            "Requested MAP exceeds the log-derived vehicle operating ceiling at this model-predicted airflow; "
            "this direct engine-lab point is not vehicle-feasible."
        )
    elif ceiling - body.map_kpa <= max(2.0, 0.03 * ceiling):
        warnings.append(
            "Requested MAP is near the log-derived vehicle operating ceiling at this model-predicted airflow."
        )
    if nonfinite:
        warnings.append("The source plant returned non-finite diagnostics: " + ", ".join(nonfinite))
    values["iat_k"] = iat_k
    values["charge_temp_c"] = iat_k - 273.15
    values["charge_temp_source"] = "plant.charge_temperature(ambient_k) default (+12 K; no block-temperature input)"
    values["observed_ceiling_kpa"] = ceiling
    values["map_over_ceiling_kpa"] = excess
    values["warnings"] = warnings
    return values


@app.post("/api/thermal")
def api_thermal(body: ThermalRequest):
    from plant import charge_temperature, predict
    from thermal import ThermalNetwork

    t_amb = body.ambient_c + 273.15
    engine = predict(body.rpm, body.map_kpa, charge_temperature(t_amb), t_amb,
                      body.spark, body.lam)
    net = ThermalNetwork()
    net.reset(t_amb=t_amb, warm=False)
    dt = 0.1
    frames = [{"time_s": 0.0, "phase": "start", "t_turb": net.t_turb,
               "t_oil": net.t_oil, "t_block": net.t_block, "egt_c": None,
               "exhaust_boundary_c": body.ambient_c, "ambient_c": body.ambient_c,
               "thermostat": None, "rpm": None, "mdot_fuel": None, "mdot_exh": None,
               "command": [None, None, None, body.fan, body.pump]}]
    time_s = 0.0
    phases = ((float(body.heat_s), "heating", float(engine["mdot_fuel_gps"]),
               float(engine["mdot_air_gps"] + engine["mdot_fuel_gps"]),
               float(engine["egt_c"] + 273.15), float(body.rpm)),
              (float(body.cool_s), "cooling", 0.0, 0.0, t_amb, 800.0))
    # Integrate at 0.1 s; return one-second samples plus each phase endpoint.
    for duration, phase, fuel, exhaust, egt, rpm in phases:
        n = int(math.ceil(duration / dt))
        for i in range(n):
            h = min(dt, duration - i * dt)
            if h <= 0:
                break
            net.step(h, fuel, exhaust, egt, t_amb, 0.0, body.fan, body.pump, rpm=rpm)
            time_s += h
            if abs(time_s - round(time_s)) < 1e-9 or i == n - 1:
                frames.append({"time_s": round(time_s, 3), "phase": phase,
                               "t_turb": float(net.t_turb), "t_oil": float(net.t_oil),
                               "t_block": float(net.t_block),
                               "ambient_c": body.ambient_c, "thermostat": float(net.thermostat),
                               "rpm": rpm, "mdot_fuel": fuel, "mdot_exh": exhaust,
                               "command": [None, None, None, body.fan, body.pump],
                               "egt_c": float(egt - 273.15) if phase == "heating" else None,
                               "exhaust_boundary_c": (None if phase == "heating"
                                                      else float(t_amb - 273.15))})
    return {"frames": frames,
            "method": ("Cold-start teaching experiment: all thermal nodes begin at ambient; "
                       "the engine point uses ECT=ambient and plant.charge_temperature(ambient_k) "
                       "default (+12 K; no block input); heating uses plant.predict output, then "
                       "cooling removes exhaust and fuel heat. ThermalNetwork integrates at 0.1 s."),
            "initial_state": "cold_start_at_ambient",
            "teaching_experiment": True}


@app.get("/api/logs")
def api_logs():
    try:
        from app.replay import trip_catalog, vehicle_metadata, PREVIEW_S
        return {"trips": trip_catalog(), "vehicle": vehicle_metadata(),
                "preview_s": list(PREVIEW_S)}
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"replay support is unavailable: {exc}") from None


@app.post("/api/replay")
def api_replay(body: ReplayRequest):
    try:
        from app.replay import store
        return store.request(body.trip_id, preempt=body.preempt)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown recording") from None


# The launcher can serve the already-built UI and the API on one loopback
# origin. During frontend development, absence of dist leaves the API alone.
_DIST = Path(__file__).resolve().parents[1] / "dist"
if (_DIST / "index.html").is_file():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="explainer-ui")


def main():
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
