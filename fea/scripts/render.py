"""Render the static results as six-panel stress maps (four full views + two close-ups).

    python render.py frame_1p5.msh
"""
import json
import os
import sys
import numpy as np
import meshio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")
SCALE = {"full_throttle": 3, "flat_drop": 10, "nose_down": 15, "sideways_tumble": 10, "yaw_spin": 15, "diagonal_twist": 10}

FULL = dict(x=(-74, 54), y=(-60, 60), z=(-14, 36), zoom=1.42)
PANELS = [
    ("Top", 89, -90, FULL, None),
    ("Bottom (battery side)", -89, -90, FULL, None),
    ("Iso front-right", 30, -50, FULL, None),
    ("Iso rear-left, from below", -25, 130, FULL, None),
    ("Close-up: front arm root + camera brace", 35, -40, dict(x=(0, 42), y=(-2, 40), z=(-12, 26), zoom=1.0), (0, 42, -2, 40, -12, 26)),
    ("Close-up: battery seat, from below", -40, -60, dict(x=(-28, 28), y=(-26, 26), z=(-12, 8), zoom=1.0), (-28, 28, -26, 26, -12, 8)),
]


def surface(path):
    m = meshio.read(path)
    P, T = m.points, m.cells_dict["tetra"]
    faces = np.vstack([T[:, [0, 1, 2]], T[:, [0, 1, 3]], T[:, [0, 2, 3]], T[:, [1, 2, 3]]])
    owner = np.tile(np.arange(len(T)), 4)
    _, inv, cnt = np.unique(np.sort(faces, 1), axis=0, return_inverse=True, return_counts=True)
    b = cnt[inv.ravel()] == 1
    tri = P[faces[b]]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    return tri, owner[b], n


def main():
    tri, owner, normals = surface(sys.argv[1])
    centres = tri.mean(1)
    static = json.load(open(os.path.join(RESULTS, "static.json")))
    os.makedirs(os.path.join(RESULTS, "images"), exist_ok=True)
    for key, case in static["cases"].items():
        vm = np.load(os.path.join(RESULTS, "arrays", f"{key}.npz"))["von_mises"]
        vmax = SCALE.get(key, 15)
        colours = plt.cm.turbo(np.clip(vm[owner] / vmax, 0, 1))
        fig = plt.figure(figsize=(22, 14))
        for k, (name, el, az, lim, box) in enumerate(PANELS):
            ax = fig.add_subplot(2, 3, k + 1, projection="3d")
            sel = np.ones(len(tri), bool) if box is None else (
                (centres[:, 0] > box[0]) & (centres[:, 0] < box[1]) & (centres[:, 1] > box[2]) &
                (centres[:, 1] < box[3]) & (centres[:, 2] > box[4]) & (centres[:, 2] < box[5]))
            e, a = np.radians(el), np.radians(az)
            view = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
            c = colours[sel].copy()
            c[:, :3] *= (0.5 + 0.5 * np.abs(normals[sel] @ view))[:, None]
            ax.add_collection3d(Poly3DCollection(tri[sel], facecolors=c, edgecolor="none"))
            ax.set_xlim(*lim["x"]); ax.set_ylim(*lim["y"]); ax.set_zlim(*lim["z"])
            ax.set_box_aspect((np.ptp(lim["x"]), np.ptp(lim["y"]), np.ptp(lim["z"])), zoom=lim["zoom"])
            ax.view_init(el, az)
            ax.set_axis_off()
            ax.set_title(name, fontsize=14)
        sm = plt.cm.ScalarMappable(cmap="turbo", norm=plt.Normalize(0, vmax))
        fig.colorbar(sm, cax=fig.add_axes([0.945, 0.2, 0.012, 0.6])).set_label(
            f"von Mises stress, MPa (scale 0-{vmax})   PETG: ~40-45 along layers, ~20-30 across", fontsize=12)
        fig.suptitle(f"Juno-1 Wide, whole frame  |  {case['title']}  |  realistic peak "
                     f"{case['von_mises_realistic_peak_mpa']:.0f} MPa, motor moves {case['max_motor_displacement_mm']:.1f} mm", fontsize=16)
        plt.subplots_adjust(wspace=0, hspace=0.05, left=0, right=0.93, top=0.93, bottom=0)
        path = os.path.join(RESULTS, "images", f"{key}.png")
        plt.savefig(path, dpi=80)
        plt.close()
        print("saved", path)


if __name__ == "__main__":
    main()
