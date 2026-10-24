# Build Guide

> Work in progress: the frame has been designed and analysed, and the first one is being printed and built now. Build photos and flight notes will be added here once it flies.

## Layout

Juno-1 is a **pusher** quad: the motors bolt to the underside of the pads with the props underneath, and the battery straps under the belly. The camera faces +X (front) and the two antenna tubes point back and up.

| | |
| --- | --- |
| **Props** | 2.5" (63.5 mm), mounted under the motors |
| **Wheelbase** | 129 mm motor to motor, diagonally (motors at ±39, ±51.5 mm) |
| **Motor mount** | 9 mm M2 pattern, Ø4.5 mm shaft pocket |
| **Stack** | 25.5 × 25.5 mm whoop-style AIO pattern (also at 45°) |
| **Camera** | 19 mm micro camera, M2 side screws |
| **Battery** | 4S, strapped under the belly on two rails, lying front to back |
| **Antennas** | Two Ø3.1 mm bore tubes at the rear |

## Parts

| Part | What I'm using | Notes |
| --- | --- | --- |
| Frame | Juno-1 Wide, printed in PETG | See the [print guide](print-guide.md) |
| Battery | GNB 4S 650 mAh or 850 mAh | Must lie front to back. Packs up to 64 × 30 mm clear the props by about 5.4 mm |
| Props | 2.5" | Pusher layout: the props sit under the motors |
| Motors | 1404-class | The analysis assumes about 11 g per motor and prop |
| Flight controller | 25.5 mm AIO | |
| Camera | 19 mm micro | |
| Motor screws | 8 × M2 × 5 | Two per motor, see below |
| Battery strap | 10 mm wide | Through the side windows, across the battery's 30 mm width |

## Motor mounting

Each pad has four M2 holes, but the two inboard holes sit under the arm, so each motor is held with the **two outboard screws**. That is enough for a pusher layout: thrust pushes the motor up into the pad, so the plastic takes the thrust and landing loads in compression, and the screws only hold the motor's weight, vibration and side loads.

- Use threadlocker.
- Check screw length against your motor. The pad is 3 mm thick, so M2 × 5 leaves about 2 mm of thread in the motor. A longer screw can bottom out on the stator windings and short them.
- Button-head screws (Ø3.5 mm head) seat flatter than socket caps on the outboard holes.
- The two usable holes sit next to each other rather than diagonally, so check for motor wobble after crashes.

## Battery

- Lay the pack front to back. Mounted sideways it would reach the props.
- Put a thin foam pad under it. The front corners of the battery seat carry the arm loads in hard crashes, and the pad spreads them out.
- Run the strap across the pack's width so it stays inside the battery footprint, well clear of the props.

## Flight setup

The arms are longer and springier than a carbon frame's. The [vibration analysis](../fea/README.md#vibration) puts the arms' in-plane modes at 103–129 Hz and their flapping modes at 252 and 353 Hz, right around the motors' hover speed, so:

- Enable RPM filtering and the dynamic notch.
- Soft-mount the flight controller.
- Check a blackbox log on the first flights before tuning PIDs up.

## Build photos

_Coming once the first frame is built._
