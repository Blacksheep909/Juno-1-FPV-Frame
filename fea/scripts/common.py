"""Shared setup for the Juno-1 FEA scripts.

Units throughout: mm, N, MPa, tonne (so density is t/mm^3 and frequencies come out in Hz).
"""
import numpy as np
import meshio
import skfem as fem
from skfem.helpers import ddot, sym_grad, trace, dot

# FDM PETG, 4 walls / 20% infill. The arms and struts are thin enough that they print
# almost entirely as perimeters, so near-solid properties are used.
E = 1900.0          # MPa
NU = 0.38
RHO = 1.27e-9       # t/mm^3
LAM = E * NU / ((1 + NU) * (1 - 2 * NU))
MU = E / (2 * (1 + NU))

# Strength reference values for PETG printed on a hobby FDM printer (typical, not measured).
UTS_ALONG_LAYERS = (40.0, 45.0)    # MPa
UTS_ACROSS_LAYERS = (20.0, 30.0)   # MPa, layer adhesion

# Juno-1 Wide geometry (frame coordinates: +X = front/camera, +Z = up, pads' underside at z = -3)
MOTOR_X, MOTOR_Y = 39.0, 51.5
MOTORS = {"FL": (MOTOR_X, MOTOR_Y), "FR": (MOTOR_X, -MOTOR_Y),
          "RL": (-MOTOR_X, MOTOR_Y), "RR": (-MOTOR_X, -MOTOR_Y)}
PAD_UNDERSIDE_Z = -3.0
BATTERY_SEAT_Z = -9.8       # everything below this is the battery rails / belly the pack is strapped to
STACK_HOLES = [(sx, sy) for sx in (-12.7, 12.7) for sy in (-12.7, 12.7)]


def load_mesh(path):
    """Read a gmsh tet mesh and return a scikit-fem MeshTet (unused nodes dropped)."""
    m = meshio.read(path)
    tets = m.cells_dict["tetra"]
    used = np.unique(tets)
    remap = -np.ones(len(m.points), int)
    remap[used] = np.arange(len(used))
    return fem.MeshTet(m.points[used].T.copy(), remap[tets].T.copy())


@fem.BilinearForm
def stiffness(u, v, w):
    eu, ev = sym_grad(u), sym_grad(v)
    return 2 * MU * ddot(eu, ev) + LAM * trace(eu) * trace(ev)


@fem.BilinearForm
def mass(u, v, w):
    return RHO * dot(u, v)


class Model:
    """Quadratic-tet elasticity model of the frame."""

    def __init__(self, mesh_path):
        self.mesh = load_mesh(mesh_path)
        self.element = fem.ElementVector(fem.ElementTetP2())
        self.basis = fem.Basis(self.mesh, self.element, intorder=2)
        self.N = self.basis.N
        self.X = self.basis.doflocs
        self.comp = np.zeros(self.N, int)
        for c, idx in enumerate(self.basis.split_indices()):
            self.comp[idx] = c
        p, t = self.mesh.p, self.mesh.t
        self.centroids = p[:, t].mean(axis=1)
        a, b, c, d = (p[:, t[i]] for i in range(4))
        self.volumes = np.abs(np.einsum("ij,ij->j", np.cross((b - a).T, (c - a).T).T, d - a)) / 6
        self._K = None

    @property
    def K(self):
        if self._K is None:
            self._K = stiffness.assemble(self.basis).tocsr()
        return self._K

    def rigid_body_modes(self, idx=None):
        B = np.zeros((self.N, 6))
        x, y, z = self.X
        c = self.comp
        for k in range(3):
            B[c == k, k] = 1
        B[c == 0, 3], B[c == 1, 3] = -y[c == 0], x[c == 1]
        B[c == 1, 4], B[c == 2, 4] = -z[c == 1], y[c == 2]
        B[c == 2, 5], B[c == 0, 5] = -x[c == 2], z[c == 0]
        return B if idx is None else B[idx]

    def facets(self, test):
        return self.mesh.facets_satisfying(test, boundaries_only=True)

    def pad_underside(self, cx, cy, r=8.5):
        """Facets where a motor bolts on (pusher layout: motor hangs under the pad)."""
        return self.facets(lambda x: (np.abs(x[2] - PAD_UNDERSIDE_Z) < 0.05) & (np.hypot(x[0] - cx, x[1] - cy) < r))

    def traction(self, facets, force):
        """Spread a total force (N) evenly over a set of boundary facets."""
        fb = fem.FacetBasis(self.mesh, self.element, facets=facets, intorder=3)
        area = fem.Functional(lambda w: 1.0 + 0 * w.x[0]).assemble(fb)
        t = np.asarray(force, float) / area
        return fem.LinearForm(lambda v, w: t[0] * v[0] + t[1] * v[1] + t[2] * v[2]).assemble(fb)

    def element_stress(self, u):
        """Per-element max von Mises and max tensile stress normal to the print layers (sigma_zz)."""
        G = self.basis.interpolate(u).grad
        eps = 0.5 * (G + np.swapaxes(G, 0, 1))
        tr = eps[0, 0] + eps[1, 1] + eps[2, 2]
        s = 2 * MU * eps
        for i in range(3):
            s[i, i] += LAM * tr
        vm = np.sqrt(0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2)
                     + 3 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[2, 0] ** 2))
        return vm.max(axis=1), s[2, 2].max(axis=1)

    def mean_displacement(self, u, cx, cy, r=3.0):
        sel = (np.hypot(self.X[0] - cx, self.X[1] - cy) < r) & (np.abs(self.X[2] - PAD_UNDERSIDE_Z) < 0.3)
        return np.array([u[sel & (self.comp == k)].mean() for k in range(3)])

    def realistic_peak(self, values, fraction=0.0005):
        """Peak after discarding the hottest `fraction` of volume.

        Point loads and rigid supports create a few elements of artificial stress spike; this
        trims them so the number reflects the material ~1 mm away from those spots.
        """
        order = np.argsort(values)[::-1]
        cum = np.cumsum(self.volumes[order])
        return float(values[order][np.searchsorted(cum, fraction * self.volumes.sum())])
