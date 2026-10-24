"""Mesh the frame STEP into quadratic-ready tetrahedra.

The frame is mirror-symmetric about y = 0, so only the +Y half is meshed and then mirrored.
That keeps the mesh perfectly symmetric and sidesteps one dense spline face on the -Y side
that gmsh struggles with. Near-zero-volume sliver tets (from tiny CAD sliver faces) are
removed afterwards because they wreck solver convergence without carrying any load.

    python mesh.py ../../cad/Juno-1-Wide.step frame_1p5.msh --size 1.5
"""
import argparse
import numpy as np
import gmsh
import meshio
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def mesh_half(step, size):
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    vol = gmsh.model.occ.importShapes(step)
    box = gmsh.model.occ.addBox(-200, 0, -100, 400, 200, 200)
    gmsh.model.occ.intersect(vol, [(3, box)])
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", size)
    gmsh.option.setNumber("Mesh.MeshSizeMin", size / 4)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
    gmsh.model.mesh.generate(3)
    _, coords, _ = gmsh.model.mesh.getNodes()
    tags, conn = gmsh.model.mesh.getElementsByType(4)
    node_tags, _, _ = gmsh.model.mesh.getNodes()
    gmsh.finalize()
    P = coords.reshape(-1, 3)
    lookup = {int(t): i for i, t in enumerate(node_tags)}
    T = np.vectorize(lookup.get)(conn.reshape(-1, 4).astype(int))
    used = np.unique(T)
    remap = -np.ones(len(P), int)
    remap[used] = np.arange(len(used))
    return P[used], remap[T]


def mirror(P, T, tol=1e-6):
    on = np.abs(P[:, 1]) < tol
    P[on, 1] = 0.0
    newid = np.empty(len(P), int)
    newid[on] = np.where(on)[0]
    newid[~on] = len(P) + np.arange((~on).sum())
    Pm = P[~on].copy()
    Pm[:, 1] *= -1
    Tm = newid[T][:, [0, 2, 1, 3]]          # flip orientation
    return np.vstack([P, Pm]), np.vstack([T, Tm])


def remove_slivers(P, T, qmin=0.02):
    a, b, c, d = (P[T[:, i]] for i in range(4))
    vol = np.abs(np.einsum("ij,ij->i", np.cross(b - a, c - a), d - a)) / 6
    edges = np.stack([np.linalg.norm(x - y, axis=1) for x, y in ((a, b), (a, c), (a, d), (b, c), (b, d), (c, d))], 1)
    q = 6 * np.sqrt(2) * vol / edges.max(1) ** 3        # 1 = regular tet
    T2 = T[q >= qmin]
    faces = np.vstack([T2[:, [0, 1, 2]], T2[:, [0, 1, 3]], T2[:, [0, 2, 3]], T2[:, [1, 2, 3]]])
    owner = np.tile(np.arange(len(T2)), 4)
    key = np.sort(faces, 1)
    order = np.lexsort(key.T[::-1])
    same = np.all(key[order][1:] == key[order][:-1], 1)
    i, j = owner[order][:-1][same], owner[order][1:][same]
    _, lab = connected_components(coo_matrix((np.ones(len(i)), (i, j)), shape=(len(T2),) * 2), directed=False)
    keep = lab == np.argmax(np.bincount(lab))
    return T2[keep], int((q < qmin).sum()), float(vol[q < qmin].sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step")
    ap.add_argument("out")
    ap.add_argument("--size", type=float, default=1.5, help="max element size, mm")
    a = ap.parse_args()
    P, T = mesh_half(a.step, a.size)
    P, T = mirror(P, T)
    T, n_bad, v_bad = remove_slivers(P, T)
    meshio.write(a.out, meshio.Mesh(P, [("tetra", T)]), file_format="gmsh22", binary=True)
    print(f"{a.out}: {len(T)} tets, removed {n_bad} slivers ({v_bad:.3f} mm^3)")


if __name__ == "__main__":
    main()
