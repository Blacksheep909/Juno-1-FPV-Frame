"""Free-free vibration modes of the frame with the flying components lumped on.

    python modal.py frame_2p5.msh
"""
import json
import os
import sys
import numpy as np
import pyamg
import scipy.sparse as sp
from scipy.sparse.linalg import lobpcg
from common import Model, mass, MOTORS, BATTERY_SEAT_Z, STACK_HOLES, PAD_UNDERSIDE_Z
import skfem as fem

HERE = os.path.dirname(os.path.abspath(__file__))

# Component masses, grams
MOTOR_AND_PROP = 11.0     # 1404-class motor + 2.5" prop, hangs under each pad
BATTERY = 75.0            # GNB 4S 650 mAh, strapped under the belly
STACK = 10.0              # AIO / VTX / receiver
CAMERA = 5.0              # micro camera


def main():
    model = Model(sys.argv[1])
    X, comp, N = model.X, model.comp, model.N
    M = mass.assemble(fem.Basis(model.mesh, model.element, intorder=4)).tocsr()

    def lump(sel, grams):
        d = np.zeros(N)
        for k in range(3):
            idx = np.where(sel & (comp == k))[0]
            d[idx] += grams * 1e-6 / len(idx)
        return d

    extra = np.zeros(N)
    for cx, cy in MOTORS.values():
        extra += lump((np.hypot(X[0] - cx, X[1] - cy) < 8) & (np.abs(X[2] - PAD_UNDERSIDE_Z) < 0.3), MOTOR_AND_PROP)
    extra += lump(X[2] < BATTERY_SEAT_Z, BATTERY)
    stack = np.zeros(N, bool)
    for sx, sy in STACK_HOLES:
        stack |= np.hypot(X[0] - sx, X[1] - sy) < 3
    extra += lump(stack, STACK)
    extra += lump((X[0] > 24) & (np.abs(X[1]) > 9.8) & (X[2] > 3), CAMERA)
    M = M + sp.diags(extra)

    shift = (2 * np.pi * 40) ** 2           # makes the free-free system positive definite
    Ks = (model.K + shift * M).tocsr()
    amg = pyamg.smoothed_aggregation_solver(Ks, B=model.rigid_body_modes(), symmetry="hermitian", max_coarse=3000)
    n = 14
    w, V = lobpcg(Ks, np.random.default_rng(1).standard_normal((N, n)), B=M, M=amg.aspreconditioner(),
                  largest=False, tol=1e-5, maxiter=400)
    order = np.argsort(w)
    freqs = np.sqrt(np.clip(w[order] - shift, 0, None)) / (2 * np.pi)
    V = V[:, order]

    regions = {k: (np.hypot(X[0] - cx, X[1] - cy) < 4) & (np.abs(X[2] - PAD_UNDERSIDE_Z) < 0.5) for k, (cx, cy) in MOTORS.items()}
    regions["antennas"] = (X[0] < -69) & (np.abs(X[1]) > 22)
    modes = []
    for k in range(6, n):
        v = V[:, k]
        amp = {r: np.array([v[s & (comp == j)].mean() for j in range(3)]) for r, s in regions.items()}
        ref = max(np.linalg.norm(a) for a in amp.values())
        modes.append({"mode": k + 1, "frequency_hz": round(float(freqs[k]), 1),
                      "relative_motion": {r: {"amplitude": round(float(np.linalg.norm(a) / ref), 2),
                                              "main_axis": "xyz"[int(np.argmax(np.abs(a)))]} for r, a in amp.items()}})
        desc = " ".join(f"{r}:{m['amplitude']:.2f}{m['main_axis']}" for r, m in modes[-1]["relative_motion"].items())
        print(f"mode {k + 1:2d}  {freqs[k]:6.0f} Hz  {desc}")
    out = {"rigid_body_modes_hz": [round(float(f), 2) for f in freqs[:6]], "elastic_modes": modes,
           "lumped_masses_g": {"motor_and_prop_each": MOTOR_AND_PROP, "battery": BATTERY, "stack": STACK, "camera": CAMERA}}
    with open(os.path.join(HERE, "..", "results", "modal.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
