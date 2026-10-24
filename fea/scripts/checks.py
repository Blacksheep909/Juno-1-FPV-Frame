"""Printability and clearance checks on the frame STL.

- enclosed voids (powder/air traps), and features too thin for a 0.4 mm nozzle
- prop-tip clearance to the frame and to the battery (pusher props sit below the pads)
- how much of each prop disc the frame covers (a simple prop-wash blockage measure)

    python checks.py ../../stl/Juno-1-Wide-frame.stl
"""
import json
import os
import sys
import numpy as np
import trimesh
from scipy import ndimage as ndi
from common import MOTORS, PAD_UNDERSIDE_Z

HERE = os.path.dirname(os.path.abspath(__file__))
PROP_RADIUS = 63.5 / 2
BATTERIES = {"GNB 4S 650 (64 x 30 mm)": (64, 30), "GNB 4S 850 HV (63 x 30 mm)": (63, 30), "GNB 4S 850 long (73 x 32 mm)": (73, 32)}


def main():
    m = trimesh.load(sys.argv[1])
    if m.extents.max() < 30:        # exported in cm
        m.apply_scale(10)
    out = {"watertight": bool(m.is_watertight), "extents_mm": m.extents.round(1).tolist(), "volume_cm3": round(m.volume / 1000, 2)}

    pitch = 0.12
    grid = m.voxelized(pitch).fill()
    V, origin = grid.matrix, grid.transform[:3, 3]
    lab, n = ndi.label(~V)
    border = set(np.unique(np.r_[lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()]))
    out["enclosed_voids"] = sum(1 for i in range(1, n + 1) if i not in border)

    edt = ndi.distance_transform_edt(V) * pitch
    ridge = V & (edt >= ndi.maximum_filter(edt, size=3)) & (edt > 0)
    pts, thick = np.argwhere(ridge) * pitch + origin, 2 * edt[ridge]
    thin = thick < 0.8
    keys, inv, cnt = np.unique(np.round(pts[thin] / 5).astype(int), axis=0, return_inverse=True, return_counts=True)
    out["thin_features_under_0p8mm"] = [
        {"at_mm": pts[thin][inv.ravel() == k].mean(0).round(1).tolist(), "min_thickness_mm": round(float(thick[thin][inv.ravel() == k].min()), 2)}
        for k in np.argsort(cnt)[::-1] if cnt[k] >= 10]

    P = m.vertices
    below = P[:, 2] < PAD_UNDERSIDE_Z - 0.05
    out["prop_tip_to_frame_mm"] = {k: round(float(np.hypot(P[below, 0] - cx, P[below, 1] - cy).min() - PROP_RADIUS), 1) for k, (cx, cy) in MOTORS.items()}
    out["prop_tip_to_battery_corner_mm"] = {
        name: round(float(min(np.hypot(mx - np.clip(mx, -L / 2, L / 2), my - np.clip(my, -W / 2, W / 2)) for mx, my in MOTORS.values()) - PROP_RADIUS), 1)
        for name, (L, W) in BATTERIES.items()}

    top = V.any(axis=2)
    cover = {}
    for k, (cx, cy) in MOTORS.items():
        g = np.linspace(-PROP_RADIUS, PROP_RADIUS, 241)
        gx, gy = np.meshgrid(g, g)
        r = np.hypot(gx, gy)
        disc = (r < PROP_RADIUS) & (r > 9)          # outside the motor bell
        i = np.clip(((gx[disc] + cx - origin[0]) / pitch).round().astype(int), 0, top.shape[0] - 1)
        j = np.clip(((gy[disc] + cy - origin[1]) / pitch).round().astype(int), 0, top.shape[1] - 1)
        cover[k] = round(100 * float(top[i, j].mean()), 1)
    out["prop_disc_covered_percent"] = cover

    normals, areas, zc = m.face_normals, m.area_faces, m.triangles_center[:, 2]
    overhang = (normals[:, 2] < -np.cos(np.radians(45))) & (zc > zc.min() + 0.3)
    out["overhang_needing_support_mm2"] = round(float(areas[overhang].sum()))

    print(json.dumps(out, indent=1))
    with open(os.path.join(HERE, "..", "results", "checks.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
