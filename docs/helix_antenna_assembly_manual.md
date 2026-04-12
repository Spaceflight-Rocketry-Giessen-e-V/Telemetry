# Helix Antenna Build Manual

This document describes how we built our helical groundstation antenna for receiving telemetry from our rockets. 

---

## Table of Contents

- [Overview](#overview)
- [Bill of Materials](#bill-of-materials)
  - [3D-Printed Design Files](#3d-printed-design-files)
- [Build Process](#build-process)
  - [Phase 1 — Rod Preparation \& Pacifier Placement](#phase-1--rod-preparation--pacifier-placement)
  - [Phase 2 — Epoxy Application](#phase-2--epoxy-application)
  - [Phase 3 — Winding the Helix Coil](#phase-3--winding-the-helix-coil)
  - [Phase 4 — Inserting the Coil](#phase-4--inserting-the-coil)
  - [Phase 5 — Base Plate \& Final Assembly](#phase-5--base-plate--final-assembly)
  - [Phase 6 — Soldering](#phase-6--soldering)
- [Build Checklist](#build-checklist)

---

## Overview

The mechanical design of the helix antenna is explained in the [design overview](design_overview.md#mechanical-design).

|![Side View](../groundstation/antenna/images/GroundstationAntenna_render_2.png) | ![Base Detail](../groundstation/antenna/images/GroundstationAntenna_render_1.png)|
|---|---|

---

## Bill of Materials

|Item|Specification|Est. Cost (€)|
|---|---|:---:|
|Fiberglass Rod|2 m length, 30 mm diameter|60|
|Aluminum Plate|70 × 70 cm, 2 mm thickness|35|
|Copper Tube|15 m length, 6 mm diameter, hollow|60|
|[SMA Connector](https://www.digikey.de/de/products/detail/te-connectivity-linx/CONSMA016-15-G/11624645)|TE Connectivity CONSMA016-15-G|7|
|[Pacifier](../groundstation/antenna/Auxiliary%20Design%20Files/Pacifier.stl)|22× (3D printed)|-|
|[Pacifier Fixture](../groundstation/antenna/Auxiliary%20Design%20Files/Pacifier%20Fixture.stl)|1× (3D printed)|-|
|[Cone Top](../groundstation/antenna/Auxiliary%20Design%20Files/Cone%20Top.stl)|1× (3D printed)|-|
|[Cone Bottom](../groundstation/antenna/Auxiliary%20Design%20Files/Cone%20Bottom.stl)|1× (3D printed)|-|
|[Rope Fixture](../groundstation/antenna/Auxiliary%20Design%20Files/Rope%20Fixture.stl)|1× (3D printed)|-|
|[Winding Clamp](../groundstation/antenna/Auxiliary%20Design%20Files/Winding%20Clamp.stl)|1× (3D printed)|-|
|[Winding Help](../groundstation/antenna/Auxiliary%20Design%20Files/Winding%20Help.stl)|1× (3D printed)|-|
|M8 × 30 Screws|8×|-|
|M8 Nuts|8×|-|
|M2.5 × 10 Screws|4×|-|
|M2.5 Nuts|4×|-|
|Epoxy Resin + Hardener|with syringes and mixing equipment|10|
|Hot Glue Sticks|for temporary fixturing|-|
|Isopropyl Alcohol|for surface cleaning|-|
|String / Guy Wire| for structural bracing, non metallic|5|
|**Total (excl. 3D printing)**||**177**|

### 3D-Printed Design Files

All 3D models are available in the [`groundstation/antenna/`](../groundstation/antenna/) subfolder:

- Original Design Files: Native `.f3z` Autodesk Fusion files
- Auxiliary Design Files: Parts exported as `.stl` and `.step`

---

## Build Process

### Phase 1 — Rod Preparation & Pacifier Placement

**1. The pacifiers**

The "pacifiers" are 3D-printed ring fixtures that hold the copper coil at the correct spacing and angle along the fiberglass rod. They are the most integral part of the assembly since they decide the final geometry.

|![Pacifier part](images/antenna_assembly/0001_pacifier.png)|![Template placement](images/antenna_assembly/0002_pacifier_set_template.png)|
|---|---|
|[Pacifier](../groundstation/antenna/Auxiliary%20Design%20Files/Pacifier.stl)|[Pacifier Spacer](../groundstation/antenna/Auxiliary%20Design%20Files/Pacifier%20Fixture.stl)|

![Pacifier and template](images/antenna_assembly/0003_pacifier_and_template.png)

**2. Prepare the rod**

Lay the fiberglass rod on your work surface and clean it thoroughly with isopropyl alcohol.

|![Rod](images/antenna_assembly/0101_rod.png)|![Cleaned rod](images/antenna_assembly/0102_rod_cleaned.png)|
|---|---|

**3. Set the first pacifier**

Place the first pacifier 10 cm from the top of the rod. You will work your way down from the top.

![First pacifier placed](images/antenna_assembly/0103_first_pacifier_10cm.png)

**4. Attach with hot glue**

Attach the first pacifier with hot glue. Using the 3D-printed pacifier spacer, position and hot-glue each pacifier. Apply a small amount first, just enough for initial stability. Wait for the glue to partially cure, remove the template, then add more hot glue around the perimeter of the pacifier. Rotate the entire assembly slowly for a few seconds while the glue cools to prevent it from sagging or setting off-axis.

Cooling can be accelerated with compressed air or a fan. Our compressor had issues on build day, so we had to cool it the old-fashioned way — by blowing on a long rod for several hours. Highly recommended workout for the lungs.

Repeat for all pacifiers down the rod.

|![Hot glued](images/antenna_assembly/0104_first_pacifier_hot_glued.png)|![Template set](images/antenna_assembly/0105_template_set.png)|
|---|---|
| ![Template set 2](images/antenna_assembly/0106_template_set_2.png)|![Next pacifier glued](images/antenna_assembly/0107_next_pacifier_glued.png)|

The result should look like this:

|![Final rod assembly 2](images/antenna_assembly/0112_final_rod_assembly_2.png)|![Final rod assembly](images/antenna_assembly/0111_final_rod_assembly.png)|
|---|---|

Due to 3D printing tolerances, the template may introduce a small angular offset between pacifiers. This is minor and acceptable.

---

### Phase 2 — Epoxy Application

Always wear a respirator mask and eye protection and open the windows when working with epoxy resin. A helmet is advised for the looks.

![Wear a mask](images/antenna_assembly/0200_wear_a_mask.png)

**1. Mount for curing**

Attach one spare pacifier to the topmost part of the rod and hang the assembly from a shelf so the epoxy can be applied and cure fully upright, without placing stress on any of the pacifiers.

|![Shelf attachment](images/antenna_assembly/0113_rod_mount.png)|![Shelf attachment 2](images/antenna_assembly/0208_shelf_attachement.png)|
|---|---|

**2. Mix and draw up epoxy**

Mix the two-part epoxy resin according to the manufacturer's instructions. Draw it into syringes with large blunt-tip needles for controlled application.

|![Epoxy resin](images/antenna_assembly/0201_epoxy_resin.png)|![Drawing epoxy into syringe](images/antenna_assembly/0202_epoxy_syringe_draw.png)|
|---|---|

**3. First application — top side of rings**

Turn the rod upside down. Apply epoxy to the top face of each pacifier-to-rod junction. The bottom face is still covered by hot glue at this point, so leave it.

|![Epoxy application](images/antenna_assembly/0203_epoxy_application.png)|![Epoxy application 2](images/antenna_assembly/0204_epoxy_application_2.png)|
|---|---|
|![Epoxy application 3](images/antenna_assembly/0205_epoxy_application_3.png)|![Pacifier done](images/antenna_assembly/0206_pacifier_done.png)|

The epoxy may wick into small gaps between the pacifier and the rod which should increase the bonding strength. However, drips are undesired and hould be wiped with acetone.

**4. Second application — bottom side of rings**

Remove the rod from the shelf fixture, turn it around and reinsert it in the fixture. 

Remove the hot glue, then apply epoxy to the previously covered bottom faces of each pacifier.

| ![Round two](images/antenna_assembly/0210_epoxy_application_round_two.png) | ![Round two 2](images/antenna_assembly/0211_epoxy_application_round_two_2.png) |
|---|---|

Allow to cure fully before proceeding.

---

### Phase 3 — Winding the Helix Coil

**1. The winding template**

Use the 3D-printed winding help form to shape the copper tube into the correct helix diameter. Printed winding clamps hold the tube against the form, secured with woodworking clamps.


|![Full template](images/antenna_assembly/0303_winding_template_full.png)|![Template attachment](images/antenna_assembly/0302_winding_template_attachement.png)|
|---|---|
|[Winding Help](../groundstation/antenna/Auxiliary%20Design%20Files/Winding%20Help.stl)|[Winding Clamp](../groundstation/antenna/Auxiliary%20Design%20Files/Winding%20Clamp.stl)|

**2. Wind the coil**

With the tube clamped to the template, rotate it around the mandrel in a continuous helical motion, and secure it after each turn with a clamp. The copper tube should more or less keep its shape.

|![Winding 1](images/antenna_assembly/0305_winding.png)|![Winding 2](images/antenna_assembly/0306_winding_2.png)|
|---|---|
|![Winding 3](images/antenna_assembly/0307_winding_3.png)|![Winding 4](images/antenna_assembly/0308_winding_4.png)|

The coil may not seem be perfectly straight due to its springy behaviour, but this does not affect function since it will be hold by the pacifiers.

|![Finished side](images/antenna_assembly/0309_finished_side.png)|![Finished coil top](images/antenna_assembly/0310_finished_coil_top.png)|
|---|---|

![Finished coil angle](images/antenna_assembly/0311_finished_coil_angle.png)

---

### Phase 4 — Inserting the Coil

**1. Insert the coil into the pacfifiers**

Insert the finished coil into the pacifier assembly on the rod with a smooth rotating motion.

|![Inserting coil](images/antenna_assembly/0401_inserting_coil.png)|![Inserting coil 2](images/antenna_assembly/0402_inserting_coil_2.png)|
|---|---|

This step is very easy and should take about 5 minutes.

**2. Trim the coil**

Once fully seated, trim the copper tube flush at the last pacifier.

|![Finished coil antenna assembly](images/antenna_assembly/0403_finished_coil_antenna_assembly.png)|![Cut end](images/antenna_assembly/0404_cut_end.png)|
|---|---|

**3. Bend the end straight**

Bend the end of the tube straight towards the groundplane.

---

### Phase 5 — Base Plate & Final Assembly

**1. Prepare the aluminum ground plane**

Drill a center hole through the aluminum plate sized to pass the fiberglass rod. Around it, drill holes for the cone mounting screws (M8). Add holes for the SMA connector (M2.5). The [included drilling template](../groundstation/antenna/drilling_template.pdf) can be used: print it and stick it on the plate with adhesive.

This is also a good time to drill the corner holes for the guy-wire string attachment, while the plate is already on the drill press.

|![Cones](images/antenna_assembly/0500_cones.png)|![Drilled plate](images/antenna_assembly/0501_drilled_plate.png)|
|---|---|

**2. Assemble the cones and connector**

Install the SMA connector using the M2.5 screws. Pass the rod through the plate. Mount the [Top Cone](../groundstation/antenna/Auxiliary%20Design%20Files/Cone%20Top.stl) from above and bolt it down with the M8 screws. Finally, attach the [Bottom Cone](../groundstation/antenna/Auxiliary%20Design%20Files/Cone%20Bottom.stl) from below, by removing the nuts from the Top Cone, and using them to bolt the Bottom Cone to the Top Cone

|![Top cone screwed on (top view)](images/antenna_assembly/0502_top_cone_screwedon_top.png)|![Top cone screwed on (bottom view)](images/antenna_assembly/0503_top_cone_screwedon_bottom.png)|
|---|---|
|![SMA connector bottom](images/antenna_assembly/0504_SMA_connector_bottom.png)|![SMA connector top](images/antenna_assembly/0504_SMA_connector_top.png)|

![Finished assembly](../groundstation/antenna/images/GroundstationAntenna_picture_2.png)

**3. Attach the rope fixture and guy wires**

Glue the [Rope Fixture](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/groundstation/antenna/Auxiliary%20Design%20Files/Rope%20Fixture.stl) with epoxy resin to the very top of the rod. After curing, run strings from each corner of the aluminum plate up to the fixture.

![Assembly with strings](images/antenna_assembly/0601_assembly_with_strings_attached.png)

If adhesion between the pacifiers and the rod seems insufficient, it is possible to design and 3D-print connector bridges between adjacent pacifiers for added rigidity. This should be integrated during Phase 2. We opted against it due to weight and material concerns, but the option exists.

---

### Phase 6 — Soldering

**1. Prepare the tube end**

Trim the straight end of the tube to the correct length. Squeeze the end with pliers and use sandpaper to rough the surface and remove the oxide layer. Clean with isopropyl alcohol.

**2. Solder copper tube to SMA connector**

Use a good amount of flux, a heat gun and a soldering iron to attach the squeezed end of the tube to the sma connector.

---

## Build Checklist

### Phase 1 — Rod Preparation & Pacifier Placement
- [ ] Verify pacifier fit on the fiberglass rod
- [ ] Clean fiberglass rod with isopropyl alcohol
- [ ] Mark 10 cm from the top of the rod for the first pacifier position
- [ ] Hot-glue first pacifier in place
- [ ] Rotate assembly while glue cools to prevent sagging
- [ ] Add next pacifier with the spacing template and add hot glue to one side
- [ ] Remove template, reinforce with additional hot glue
- [ ] Repeat for all 22 pacifiers down the rod

### Phase 2 — Epoxy Application
- [ ] Mix two-part epoxy resin and draw into syringes
- [ ] Turn rod upside down, apply epoxy to top face of all pacifier junctions
- [ ] Let cure fully
- [ ] Remove all hot glue
- [ ] Apply epoxy to bottom face of all pacifier junctions
- [ ] Let cure fully

### Phase 3 — Winding the Helix Coil
- [ ] Clamp copper tube to winding form using printed clamps and woodworking clamps
- [ ] Wind copper tube into helix along the full length of the tube and secure with clamps
- [ ] Remove coil from winding form

### Phase 4 — Inserting the Coil
- [ ] Insert coil into pacifier assembly with a rotating motion
- [ ] Trim copper tube flush at the last pacifier
- [ ] Bend the end of the tube straight

### Phase 5 — Base Plate & Final Assembly
- [ ] Drill center hole in aluminum plate for the fiberglass rod
- [ ] Drill holes for M8 cone screws around center hole
- [ ] Drill holes for M2.5 SMA connector screws
- [ ] Drill corner holes for guy-wire string attachment
- [ ] Install SMA connector with 4× M2.5×10 screws and M2.5 nuts
- [ ] Pass rod through plate and mount Top Cone with 8× M8×30 screws and M8 nuts
- [ ] Attach Bottom Cone one the M8 screws
- [ ] Glue Rope Fixture to top of rod with epoxy resin, let cure fully
- [ ] Run string from each corner of aluminum plate up to rope fixture

### Phase 6 — Soldering
- [ ] Trim the straight end of the tube
- [ ] Squeeze the end with pliers
- [ ] Prepare the surface with sandpaper and isopropyl alcohol
- [ ] Use flux and an additional heat source like a heat gun and a soldering iron to solder the end to the SMA connector