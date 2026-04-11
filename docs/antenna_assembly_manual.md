# Helix Antenna Build Manual

> **Spaceflight Rocketry Giessen e.V.** — Ground Station Telemetry Antenna  
> This document describes how we built our helical antenna for receiving telemetry from our rockets.  
> Repository: [Spaceflight-Rocketry-Giessen-e-V/Telemetry](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry)

---

## Table of Contents

- [Helix Antenna Build Manual](#helix-antenna-build-manual)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Bill of Materials](#bill-of-materials)
    - [3D-Printed Design Files](#3d-printed-design-files)
  - [Build Process](#build-process)
    - [Phase 1 — Pacifier Preparation](#phase-1--pacifier-preparation)
    - [Phase 2 — Rod Preparation \& Pacifier Placement](#phase-2--rod-preparation--pacifier-placement)
    - [Phase 3 — Epoxy Application](#phase-3--epoxy-application)
    - [Phase 4 — Winding the Helix Coil](#phase-4--winding-the-helix-coil)
    - [Phase 5 — Inserting the Coil](#phase-5--inserting-the-coil)
    - [Phase 6 — Base Plate \& Final Assembly](#phase-6--base-plate--final-assembly)
  - [Build Checklist](#build-checklist)
    - [Phase 1 — Pacifier Preparation](#phase-1--pacifier-preparation-1)
    - [Phase 2 — Rod Preparation \& Pacifier Placement](#phase-2--rod-preparation--pacifier-placement-1)
    - [Phase 3 — Epoxy Application](#phase-3--epoxy-application-1)
    - [Phase 4 — Winding the Helix Coil](#phase-4--winding-the-helix-coil-1)
    - [Phase 5 — Inserting the Coil](#phase-5--inserting-the-coil-1)
    - [Phase 6 — Base Plate \& Final Assembly](#phase-6--base-plate--final-assembly-1)
  - [Contributing \& Contact](#contributing--contact)

---

## Overview

A helical antenna is an excellent choice for rocket telemetry: it provides circular polarization, high gain, and a relatively narrow beam — ideal for tracking a rocket that spins during flight.

| Render (Side View)                                                       | Render (Base Detail)                                                       |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| ![Side View](../groundstation/antenna/GroundstationAntenna_render_2.png) | ![Base Detail](../groundstation/antenna/GroundstationAntenna_render_1.png) |

---

## Bill of Materials

| Item                                                                                                                                                                | Specification                                         | Est. Cost (€) |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | :-----------: |
| Fiberglass rod                                                                                                                                                      | 2 m length, 30 mm diameter                            |      ~15      |
| Aluminum plate                                                                                                                                                      | 70 × 70 cm, 2 mm thickness (ground plane / reflector) |      ~35      |
| Copper tube                                                                                                                                                         | 6 mm diameter, 15 m length, **hollow**                |      ~40      |
| [SMA Connector](https://www.digikey.de/de/products/detail/te-connectivity-linx/CONSMA016-15-G/11624645)                                                             | TE Connectivity CONSMA016-15-G                        |      ~8       |
| [Pacifier](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Pacifier.stl)                   | 22 × (3D printed)                                     |       —       |
| [Pacifier Fixture](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Pacifier%20Fixture.stl) | 1 × (3D printed)                                      |       —       |
| [Cone Top](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Cone%20Top.stl)                 | 1 × (3D printed)                                      |       —       |
| [Cone Bottom](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Cone%20Bottom.stl)           | 1 × (3D printed)                                      |       —       |
| [Rope Fixture](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Rope%20Fixture.stl)         | 1 × (3D printed)                                      |       —       |
| [Winding Clamp](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Winding%20Clamp.stl)       | 1 × (3D printed)                                      |       —       |
| [Winding Help](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Winding%20Help.stl)         | 1 × (3D printed)                                      |       —       |
| M8 × 30 screws                                                                                                                                                      | 8 ×                                                   |      ~3       |
| M8 nuts                                                                                                                                                             | 8 ×                                                   |      ~2       |
| M2.5 × 10 screws                                                                                                                                                    | 4 ×                                                   |      ~2       |
| M2.5 nuts                                                                                                                                                           | 4 ×                                                   |      ~1       |
| Epoxy resin + hardener                                                                                                                                              | with syringes and mixing equipment                    |      ~20      |
| Hot glue sticks                                                                                                                                                     | for temporary fixturing                               |      ~5       |
| Isopropyl alcohol                                                                                                                                                   | for surface cleaning                                  |      ~5       |
| String / guy wire                                                                                                                                                   | for structural bracing                                |      ~5       |
| **Total (excl. 3D printing)**                                                                                                                                       |                                                       |   **~141**    |

### 3D-Printed Design Files

All 3D models are available in the [`groundstation/antenna/`](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/tree/main/groundstation/antenna/) subfolder:

- **Original Design Files** (`.f3z`): Cone Bottom, Cone Top, Pacifier Fixture, Pacifier, Rope Fixture, Winding Clamp, Winding Help
- **Auxiliary Design Files**: Same parts exported as `.stl` and `.step`

---

## Build Process

### Phase 1 — Pacifier Preparation

The "pacifiers" are 3D-printed ring fixtures that hold the copper coil at the correct spacing and angle along the fiberglass rod. They are the backbone of the antenna geometry.

|                                                                                                                                                   |                                                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ![Pacifier part](images/antenna_assembly/0001_pacifier.jpg)                                                                                       | ![Template placement](images/antenna_assembly/0002_pacifier_set_template.jpg)                                                                                       |
| [Pacifier](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Pacifier.stl) | [Pacifier Fixture](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Pacifier%20Fixture.stl) |

![Pacifier and template](images/antenna_assembly/0003_pacifier_and_template.jpg)

---

### Phase 2 — Rod Preparation & Pacifier Placement

**1. Prepare the rod**

Lay the fiberglass rod on your work surface and clean it thoroughly with isopropyl alcohol.

|                                              |                                                              |
| -------------------------------------------- | ------------------------------------------------------------ |
| ![Rod](images/antenna_assembly/0101_rod.jpg) | ![Cleaned rod](images/antenna_assembly/0102_rod_cleaned.jpg) |

**2. Set the first pacifier**

Place the first pacifier 10 cm from the top of the rod. You will work your way *down* from the top.

![First pacifier placed](images/antenna_assembly/0103_first_pacifier_10cm.jpg)

**3. Attach with hot glue**

Using the 3D-printed spacing template, position and hot-glue each pacifier. Apply a small amount first, just enough for initial stability. Wait for the glue to partially cure, remove the template, then reinforce the pacifier with more hot glue around its perimeter. 

> 📎 Cooling can be accelerated with compressed air. Our compressor had issues on build day, so we had to cool it the old-fashioned way — by blowing on a long rod for several hours. Highly recommended workout for the lungs.

Repeat for all pacifiers down the rod.

|                                                                         |                                                                              |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| ![Hot glued](images/antenna_assembly/0104_first_pacifier_hot_glued.jpg) | ![Template set](images/antenna_assembly/0105_template_set.jpg)               |
| ![Template set 2](images/antenna_assembly/0106_template_set_2.jpg)      | ![Next pacifier glued](images/antenna_assembly/0107_next_pacifier_glued.jpg) |

**Rotate the entire assembly slowly for a few seconds while the glue cools** to prevent it from sagging or setting off-axis.

|                                                                                    |                                                                            |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| ![Pacifiers set](images/antenna_assembly/0108_pacifiers_set.jpg)                   | ![Pacifiers set 2](images/antenna_assembly/0109_pacifiers_set_2.jpg)       |
| ![Rotating for cooling](images/antenna_assembly/0110_rotating_rod_for_cooling.jpg) | ![Final rod assembly](images/antenna_assembly/0111_final_rod_assembly.jpg) |

![Final rod assembly 2](images/antenna_assembly/0112_final_rod_assembly_2.jpg)

> ⚠ Due to 3D printing tolerances, the template may introduce a small angular offset between pacifiers. This is minor and acceptable. Be aware that removing all hot glue at once before the epoxy has cured may allow the pacifiers to rotate.

**4. Mount for curing**

Attach one spare pacifier to the topmost part of the rod and hang the assembly from a shelf so it cures fully upright, without placing stress on any of the pacifiers.

|                                                                 |                                                                           |
| --------------------------------------------------------------- | ------------------------------------------------------------------------- |
| ![Shelf attachment](images/antenna_assembly/0113_rod_mount.jpg) | ![Shelf attachment 2](images/antenna_assembly/0208_shelf_attachement.jpg) |

---

### Phase 3 — Epoxy Application

> ⚠ Always wear a respirator mask and eye protection when working with epoxy resin.

![Wear a mask](images/antenna_assembly/0200_wear_a_mask.jpg)

**1. Mix and draw up epoxy**

Mix the two-part epoxy resin according to the manufacturer's instructions. Draw it into syringes with large blunt-tip needles for controlled application.

|                                                              |                                                                                    |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| ![Epoxy resin](images/antenna_assembly/0201_epoxy_resin.jpg) | ![Drawing epoxy into syringe](images/antenna_assembly/0202_epoxy_syringe_draw.jpg) |

**2. First application — top side of rings**

Turn the rod upside down. Apply epoxy to the **top face** of each pacifier-to-rod junction. The bottom face is still covered by hot glue at this point, so leave it.

|                                                                              |                                                                              |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| ![Epoxy application](images/antenna_assembly/0203_epoxy_application.jpg)     | ![Epoxy application 2](images/antenna_assembly/0204_epoxy_application_2.jpg) |
| ![Epoxy application 3](images/antenna_assembly/0205_epoxy_application_3.jpg) | ![Pacifier done](images/antenna_assembly/0206_pacifier_done.jpg)             |

> 📎 Epoxy may wick into small gaps between the pacifier and rod — we assume this increases bonding strength. Wipe the rod clean of any drips periodically.

Let it cure fully, then remove the hot glue.

**3. Second application — bottom side of rings**

After removing the hot glue, apply epoxy to the previously covered bottom faces of each pacifier.

|                                                                            |                                                                                |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| ![Round two](images/antenna_assembly/0210_epoxy_application_round_two.jpg) | ![Round two 2](images/antenna_assembly/0211_epoxy_application_round_two_2.jpg) |

![All pacifiers done](images/antenna_assembly/0207_all_pacifiers_done.jpg)

Allow to cure fully, upright, before proceeding.

---

### Phase 4 — Winding the Helix Coil

**1. Prepare the bending template**

Use the 3D-printed [Winding Help](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Winding%20Help.stl) form to shape the copper tube into the correct helix diameter. Printed [Winding Clamps](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Winding%20Clamp.stl) hold the tube against the form, secured with woodworking clamps.

|                                                                                                                                                             |                                                                                                                                                               |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ![Winding template](images/antenna_assembly/0301_winding_template.jpg)                                                                                      | ![Template attachment](images/antenna_assembly/0302_winding_template_attachement.jpg)                                                                         |
| [Winding Help](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Winding%20Help.stl) | [Winding Clamp](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Winding%20Clamp.stl) |
| ![Full template](images/antenna_assembly/0303_winding_template_full.jpg)                                                                                    | ![Materials](images/antenna_assembly/0304_winding_materials.jpg)                                                                                              |  |

**2. Wind the coil**

With the tube clamped to the form, rotate it around the mandrel in a continuous helical motion, working your way along like threading a screw. The copper tube is surprisingly cooperative.

|                                                          |                                                          |
| -------------------------------------------------------- | -------------------------------------------------------- |
| ![Winding 1](images/antenna_assembly/0305_winding.jpg)   | ![Winding 2](images/antenna_assembly/0306_winding_2.jpg) |
| ![Winding 3](images/antenna_assembly/0307_winding_3.jpg) | ![Winding 4](images/antenna_assembly/0308_winding_4.jpg) |

The coil may not be perfectly straight, but this does not affect function.

|                                                                  |                                                                          |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------ |
| ![Finished side](images/antenna_assembly/0309_finished_side.jpg) | ![Finished coil top](images/antenna_assembly/0310_finished_coil_top.jpg) |

![Finished coil angle](images/antenna_assembly/0311_finished_coil_angle.jpg)

---

### Phase 5 — Inserting the Coil

With a smooth rotating motion — as if threading a giant screw — insert the finished coil into the pacifier assembly on the rod.

|                                                                    |                                                                        |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| ![Inserting coil](images/antenna_assembly/0401_inserting_coil.jpg) | ![Inserting coil 2](images/antenna_assembly/0402_inserting_coil_2.jpg) |

> 📎 This step looks like it should take about 5 minutes. Budget an afternoon. It will test your resolve, sanity, and possibly your friendships. The coil will get there.

Once fully seated, trim the copper tube flush at the last pacifier.

|                                                                                                    |                                                      |
| -------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| ![Finished coil antenna assembly](images/antenna_assembly/0403_finished_coil_antenna_assembly.jpg) | ![Cut end](images/antenna_assembly/0404_cut_end.jpg) |

---

### Phase 6 — Base Plate & Final Assembly

**1. Prepare the aluminum ground plane**

Drill a center hole through the aluminum plate sized to pass the fiberglass rod. Around it, drill holes for the cone mounting screws (M8). Add holes for the SMA connector (M2.5). A drill template is tracked in [Issue #39](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/issues/39).

> 📎 This is also a good time to drill the corner holes for the guy-wire string attachment, while the plate is already on the drill press.

|                                                  |                                                                  |
| ------------------------------------------------ | ---------------------------------------------------------------- |
| ![Cones](images/antenna_assembly/0500_cones.jpg) | ![Drilled plate](images/antenna_assembly/0501_drilled_plate.jpg) |

**2. Assemble the cones and connector**

Pass the rod through the plate. Mount the [Cone Top](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Cone%20Top.stl) from above and bolt it down with the M8 screws. Install the SMA connector using the M2.5 screws. Finally, attach the [Cone Bottom](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Cone%20Bottom.stl) from below.

|                                                                                            |                                                                                                  |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| ![Top cone screwed on (top view)](images/antenna_assembly/0502_top_cone_screwedon_top.jpg) | ![Top cone screwed on (bottom view)](images/antenna_assembly/0503_top_cone_screwedon_bottom.jpg) |
| ![SMA connector bottom](images/antenna_assembly/0504_SMA_connector_bottom.jpg)             | ![SMA connector top](images/antenna_assembly/0504_SMA_connector_top.jpg)                         |

![Finished assembly](images/antenna_assembly/0505_finished_assembly.jpg)

**3. Attach the rope fixture and guy wires**

Glue the [Rope Fixture](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Rope%20Fixture.stl) to the very top of the rod. After curing, run strings from each corner of the aluminum plate up to the fixture. This dramatically increases the structural rigidity of the assembly — far more than relying on the rod-to-plate connection alone.

![Assembly with strings](images/antenna_assembly/0601_assembly_with_strings_attached.jpg)

> 📎 If adhesion between the pacifiers and the rod seems insufficient, it is possible to design and 3D-print connector bridges between adjacent pacifiers for added rigidity. This should be integrated during Phase 2. We opted against it due to weight and material concerns, but the option exists.

---

## Build Checklist

### Phase 1 — Pacifier Preparation
- [ ] Print all 3D parts: 22 pacifiers, 2 cones, rope fixture, winding clamp, winding guide, spacing guide
- [ ] Verify pacifier fit on the fiberglass rod

### Phase 2 — Rod Preparation & Pacifier Placement
- [ ] Clean fiberglass rod with isopropyl alcohol
- [ ] Mark 10 cm from the top of the rod for the first pacifier position
- [ ] Hot-glue first pacifier in place using the spacing template
- [ ] Rotate assembly while glue cools to prevent sagging
- [ ] Remove template, reinforce with additional hot glue
- [ ] Repeat for all 22 pacifiers down the rod
- [ ] Hang rod upright from shelf using a spare pacifier to cure

### Phase 3 — Epoxy Application
- [ ] Put on respirator mask
- [ ] Mix two-part epoxy resin and draw into syringes
- [ ] Turn rod upside down, apply epoxy to top face of all pacifier junctions
- [ ] Let cure fully
- [ ] Remove all hot glue
- [ ] Apply epoxy to bottom face of all pacifier junctions
- [ ] Let cure fully, upright

### Phase 4 — Winding the Helix Coil
- [ ] Clamp copper tube to winding form using printed clamps and woodworking clamps
- [ ] Wind copper tube into helix along the full length of the form
- [ ] Remove coil from winding form

### Phase 5 — Inserting the Coil
- [ ] Insert coil into pacifier assembly with a rotating motion
- [ ] Trim copper tube flush at the last pacifier

### Phase 6 — Base Plate & Final Assembly
- [ ] Drill center hole in aluminum plate for the fiberglass rod
- [ ] Drill holes for M8 cone screws around center hole
- [ ] Drill holes for M2.5 SMA connector screws
- [ ] Drill corner holes for guy-wire string attachment
- [ ] Pass rod through plate and mount Cone Top with 8× M8×30 screws and M8 nuts
- [ ] Install SMA connector with 4× M2.5×10 screws and M2.5 nuts
- [ ] Attach Cone Bottom with M8 screws and nuts
- [ ] Glue Rope Fixture to top of rod, let cure
- [ ] Run string from each corner of aluminum plate up to rope fixture

---

## Contributing & Contact

This antenna was designed and built by members of [Spaceflight Rocketry Giessen e.V.](https://github.com/Spaceflight-Rocketry-Giessen-e-V).  
Questions, improvements, and pull requests are welcome!
