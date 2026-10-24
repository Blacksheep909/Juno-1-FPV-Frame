"""Whole-frame static load cases for Juno-1.

The frame is held where the battery is strapped on (pusher layout, battery underneath),
and every case loads all four motors at once. Results go to ../results/static.json, and the
per-element stress fields to ../results/arrays/ for render.py.

    python solve.py frame_1p5.msh
"""
import json
import os
import sys
import time
import numpy as np
import pyamg
from common import (Model, MOTORS, BATTERY_SEAT_Z, UTS_ALONG_LAYERS, UTS_ACROSS_LAYERS)

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")


def tangential(cx, cy):
    v = np.array([-cy, cx, 0.0])
    return v / np.linalg.norm(v)


CASES = {
    "full_throttle":   ("Full throttle, 4 N up on every motor",              lambda k, cx, cy: [0, 0, 4.0]),
    "flat_drop":       ("Flat drop, 20 N on every motor",                    lambda k, cx, cy: [0, 0, 20.0]),
    "nose_down":       ("Nose-down landing, 30 N on each front motor",       lambda k, cx, cy: [0, 0, 30.0] if cx > 0 else [0, 0, 0]),
    "sideways_tumble": ("Sideways tumble, 10 N sideways on every motor",     lambda k, cx, cy: [0, 10.0, 0]),
    "yaw_spin":        ("Yaw spin crash, 10 N twisting at every motor",      lambda k, cx, cy: 10 * tangential(cx, cy)),
    "diagonal_twist":  ("Diagonal twist, +/-15 N on opposite corners",       lambda k, cx, cy: [0, 0, 15.0 if k in ("FL", "RR") else -15.0]),
}


def main():
    t0 = time.time()
    model = Model(sys.argv[1])
    print(f"{model.mesh.t.shape[1]} tets, {model.N} DOF", flush=True)
    K = model.K
    fixed = model.facets(lambda x: x[2] < BATTERY_SEAT_Z)
    D = model.basis.get_dofs(fixed).all()
    I = np.setdiff1d(np.arange(model.N), D)
    A = K[I][:, I].tocsr()
    amg = pyamg.smoothed_aggregation_solver(A, B=model.rigid_body_modes(I), symmetry="hermitian", max_coarse=3000)
    os.makedirs(os.path.join(RESULTS, "arrays"), exist_ok=True)
    out = {"material": "PETG (FDM, 4 walls, 20% infill)", "uts_along_layers_mpa": UTS_ALONG_LAYERS,
           "uts_across_layers_mpa": UTS_ACROSS_LAYERS, "support": "battery seat (z < %.1f mm)" % BATTERY_SEAT_Z,
           "motors_mm": MOTORS, "cases": {}}
    for key, (title, load) in CASES.items():
        f = sum(model.traction(model.pad_underside(cx, cy), load(k, cx, cy)) for k, (cx, cy) in MOTORS.items())
        u = np.zeros(model.N)
        res = []
        u[I] = amg.solve(f[I], tol=1e-8, accel="cg", maxiter=8000, residuals=res)
        rel = np.linalg.norm(A @ u[I] - f[I]) / np.linalg.norm(f[I])
        vm, szz = model.element_stress(u)
        disp = {k: model.mean_displacement(u, cx, cy).round(3).tolist() for k, (cx, cy) in MOTORS.items()}
        worst = max(disp, key=lambda k: np.linalg.norm(disp[k]))
        out["cases"][key] = {
            "title": title,
            "von_mises_realistic_peak_mpa": round(model.realistic_peak(vm), 1),
            "von_mises_raw_peak_mpa": round(float(vm.max()), 1),
            "layer_tension_realistic_peak_mpa": round(model.realistic_peak(szz), 1),
            "layer_tension_raw_peak_mpa": round(float(szz.max()), 1),
            "raw_peak_location_mm": model.centroids[:, int(np.argmax(vm))].round(1).tolist(),
            "max_motor_displacement_mm": round(float(np.linalg.norm(disp[worst])), 3),
            "motor_displacement_mm": disp,
            "solver_relative_residual": float(f"{rel:.1e}"),
            "solver_iterations": len(res),
        }
        np.savez_compressed(os.path.join(RESULTS, "arrays", f"{key}.npz"), von_mises=vm, layer_tension=szz)
        c = out["cases"][key]
        print(f"{title:52s} vm {c['von_mises_realistic_peak_mpa']:5.1f} (raw {c['von_mises_raw_peak_mpa']:5.1f}) | "
              f"layer {c['layer_tension_realistic_peak_mpa']:5.1f} (raw {c['layer_tension_raw_peak_mpa']:5.1f}) MPa | "
              f"motor {c['max_motor_displacement_mm']:.2f} mm | residual {rel:.0e}", flush=True)
    with open(os.path.join(RESULTS, "static.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
