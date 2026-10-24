# Print Guide

Juno-1 is a single-piece frame designed to be printed on a hobby FDM printer in PETG. The settings below are the ones the [stress analysis](../fea/README.md) assumes.

## Files

| File | Use |
| --- | --- |
| [`stl/Juno-1-Wide-frame.stl`](../stl/Juno-1-Wide-frame.stl) | The full frame. Millimetres, watertight, 117.1 × 116.0 × 44.5 mm. |
| [`stl/test-arms/Juno-1-Wide-test-arm-front.stl`](../stl/test-arms/Juno-1-Wide-test-arm-front.stl) | Front motor pad and arm stub, for checking screw and motor fit before the full print. |
| [`stl/test-arms/Juno-1-Wide-test-arm-rear.stl`](../stl/test-arms/Juno-1-Wide-test-arm-rear.stl) | Rear motor pad and arm stub. |

If you change the design, export a new STL from [`cad/Juno-1-Wide.f3d`](../cad/Juno-1-Wide.f3d) or [`cad/Juno-1-Wide.step`](../cad/Juno-1-Wide.step). The material on the CAD body is still set to PA12 from an earlier MJF test, so ignore the mass Fusion reports.

## Slicer settings

| Setting | Value | Why |
| --- | --- | --- |
| Material | PETG | Tough, a little flexible, and forgiving in crashes |
| Walls | 4 | The arms and struts are thin enough that they print almost solid |
| Infill | 20% | Only the central body is thick enough to get infill |
| Layer height | 0.2 mm | |
| Nozzle temperature | 245–250 °C | Hotter prints bond the layers better |
| Part cooling | 30–50% | Less cooling, stronger layers |
| Supports | Tree supports, from the build plate where possible | About 3,200 mm² of overhang |
| Orientation | As modelled (Z up) | The analysis checks stress across the layers in this orientation |

Nothing on the frame sits flat on the bed: the belly is 7.5 mm lower than the motor pads. The motor faces print over supports, so they will be a little rough. Clean them up with a flat file if a motor rocks.

## Known print details

- **Motor holes.** The M2 holes are modelled at Ø2.1 mm and PETG usually prints them tight. If screws will not pass, run a 2.2–2.4 mm drill through by hand, or open the holes to Ø2.3–2.4 in CAD before slicing.
- **Unused rear holes.** The inboard hole on each rear pad sits under the arm and leaves a 0.24 mm sliver of plastic that a 0.4 mm nozzle cannot print. Expect a small gap there. It does not matter, because the motors mount with two screws (see the [build guide](build-guide.md)).
- **Axle bores.** Each pad has a Ø4.5 mm, 3 mm deep pocket for the motor shaft and circlip, capped by a 0.7 mm skin where the arm starts.
- **Camera mount.** 20.0 mm between the side plates for a 19 mm micro camera. It is a snug fit in PETG.

## Weak direction

FDM parts are weakest across the layer lines. The analysis checks that stress separately, and the highest values sit where the front arms meet the battery seat and the front stack-hole bosses. Print hot and slow there if your slicer lets you set per-region speeds.
