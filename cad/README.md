# CAD

| File | What it is |
| --- | --- |
| [`Juno-1-Wide.step`](Juno-1-Wide.step) | **Current frame.** Neutral STEP for any CAD package. |
| [`Juno-1-Wide.f3d`](Juno-1-Wide.f3d) | Current frame as a Fusion archive, with the editable timeline (arm split, move, strut lofts, notch removal). |
| [`previous/Juno-1-v1-116mm.step`](previous/Juno-1-v1-116mm.step) | v1, motors at ±43 mm. Superseded: in a pusher layout its props reach a bottom-mounted 4S battery. Kept for the design history. |
| [`previous/Juno-1-v1-116mm.f3d`](previous/Juno-1-v1-116mm.f3d) | v1 as a Fusion archive. |

Units are millimetres. The frame's origin is the centre of the stack, with +X towards the camera (front), +Z up, and the underside of the motor pads at z = −3 mm. Motors sit at (±39, ±51.5) mm.

The body's material is set to PA12 from an earlier MJF test. The frame is printed in PETG, so ignore the mass Fusion reports (the PETG print weighs about what the slicer says, not the modelled 26.9 cm³ solid).

See the [design notes](../docs/design-notes.md) for how v1 became Juno-1 Wide.
