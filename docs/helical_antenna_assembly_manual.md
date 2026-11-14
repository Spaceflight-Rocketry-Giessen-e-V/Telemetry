# Helical Antenna Build Manual

This document describes how we built our helical groundstation antenna for receiving telemetry from our rockets. 

The images in Phases 1 and 2 and in the ground plane preparation step of Phase 5 were taken during the build of the much larger older version of the antenna but also apply to the updated small version. The remaining images in Phases 3–6 show the newer build.

---

## Table of Contents

- [Overview](#overview)
- [Bill of Materials](#bill-of-materials)
  - [3D-Printed Design Files](#3d-printed-design-files)
- [Build Process](#build-process)
  - [Phase 1 - Rod Preparation \& Pacifier Placement](#phase-1---rod-preparation--pacifier-placement)
  - [Phase 2 - Epoxy Application](#phase-2---epoxy-application)
  - [Phase 3 - Winding the Helical Coil](#phase-3---winding-the-helical-coil)
  - [Phase 4 - Inserting the Coil](#phase-4---inserting-the-coil)
  - [Phase 5 - Base Plate \& Final Assembly](#phase-5---base-plate--final-assembly)
  - [Phase 6 - Soldering](#phase-6---soldering)
- [Build Checklist](#build-checklist)

---

## Overview

The mechanical design of the helical antenna is explained in the [design overview](design_overview.md#mechanical-design).

|![Side View](../groundstation/antenna/helical/images/GroundstationAntenna_render_2.png) | ![Base Detail](../groundstation/antenna/helical/images/GroundstationAntenna_render_1.png)|
|---|---|

---

## Bill of Materials

|Item|Specification|Est. Cost (€)|
|---|---|:---:|
|Fiberglass Rod|1 m length, 31 mm diameter|20|
|Aluminum Plate|40 × 40 cm, 1.5 mm thickness|15|
|Copper Tube|5 m length, 6 mm diameter, hollow|30|
|[SMA Connector](https://www.digikey.de/de/products/detail/te-connectivity-linx/CONSMA016-15-G/11624645)|WR-SMA Panel 4-Hole Flange|7|
|[Pacifier](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Pacifier.stl)|7x (3D printed)|-|
|[Pacifier Endcap](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Pacifier%20Endcap.stl)|1 (3D printed)|-|
|[Pacifier Fixture](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Pacifier%20Fixture.stl)|1× (3D printed)|-|
|[Cone Top](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Top%20Cone.stl)|1× (3D printed)|-|
|[Cone Bottom](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Bottom%20Cone.stl)|1× (3D printed)|-|
|[Winding Clamp](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Winding%20Clamp.stl)|3× (3D printed)|-|
|[Winding Help](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Winding%20Help.stl)|1× (3D printed)|-|
|[Drilling Template](../groundstation/antenna/helical/drilling_template.pdf)|1× (printed)|-|
|M6 × 25 Screws|6×|-|
|M6 Nuts|6×|-|
|M2.5 × 10 Screws|4×|-|
|M2.5 Nuts|4×|-|
|Epoxy Resin + Hardener|with syringes and mixing equipment|10|
|Hot Glue Sticks|for temporary fixturing|-|
|Isopropyl Alcohol|for surface cleaning|-|
|String / Guy Wire| for structural bracing, non metallic|5|
|**Total (excl. 3D printing)**||**87**|

### 3D-Printed Design Files

All 3D models are available in the [`groundstation/antenna/helical/`](../groundstation/antenna/helical/) subfolder:

- Original Design Files: Native `.f3z` / `.f3d` Autodesk Fusion files
- Auxiliary Design Files: Parts exported as `.stl` and `.step`

---

## Build Process

### Phase 1 - Rod Preparation & Pacifier Placement

**1. The pacifiers**

The "pacifiers" are 3D-printed ring fixtures that hold the copper coil at the correct spacing and angle along the fiberglass rod. They are the most integral part of the assembly since they decide the final geometry.

|![Pacifier part](images/helical_antenna_assembly/0001_pacifier.png)||![Template placement](images/helical_antenna_assembly/0002_pacifier_set_template.png)|
|---|---|---|
|[Pacifier](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Pacifier.stl)|[Pacifier Endcap](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Pacifier%20Endcap.stl)|[Pacifier Spacer](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Pacifier%20Fixture.stl)|

<p align="center">
  <img src="images/helical_antenna_assembly/0003_pacifier_and_template.png" alt="Pacifier and template">
</p>

**2. Prepare the rod**

Lay the fiberglass rod on your work surface and clean it thoroughly with isopropyl alcohol.

|![Rod](images/helical_antenna_assembly/0101_rod.png)|![Cleaned rod](images/helical_antenna_assembly/0102_rod_cleaned.png)|
|---|---|

**3. Set the endcap pacifier**

Place the endcap pacifier at the top of the rod and attach it with hot glue in the inside. You will work your way down from the top.

**4. Attach with hot glue**

Using the 3D-printed pacifier spacer, position and hot-glue each pacifier. Apply a small amount first, just enough for initial stability. Wait for the glue to partially cure, remove the template, then add more hot glue around the perimeter of the pacifier. Rotate the entire assembly slowly for a few seconds while the glue cools to prevent it from sagging or setting off-axis.

Cooling can be accelerated with compressed air or a fan. Our compressor had issues on build day, so we had to cool it the old-fashioned way - by blowing on a long rod for several hours. Highly recommended workout for the lungs.

Repeat for all pacifiers down the rod.

|![Hot glued](images/helical_antenna_assembly/0104_first_pacifier_hot_glued.png)|![Template set](images/helical_antenna_assembly/0105_template_set.png)|
|---|---|
| ![Template set 2](images/helical_antenna_assembly/0106_template_set_2.png)|![Next pacifier glued](images/helical_antenna_assembly/0107_next_pacifier_glued.png)|

The result should look like this:

|![Final rod assembly 2](images/helical_antenna_assembly/0112_final_rod_assembly_2.png)|![Final rod assembly](images/helical_antenna_assembly/0111_final_rod_assembly.png)|
|---|---|

Due to 3D printing tolerances, the template may introduce a small angular offset between pacifiers. This is minor and acceptable.

---

### Phase 2 - Epoxy Application

Always wear a respirator mask and eye protection and open the windows when working with epoxy resin. A helmet is advised for the looks.

<p align="center">
  <img src="images/helical_antenna_assembly/0200_wear_a_mask.png" alt="Wear a mask">
</p>

**1. Mount for curing**

Attach one spare pacifier to the topmost part of the rod and hang the assembly from a shelf so the epoxy can be applied and cure fully upright, without placing stress on any of the pacifiers.

|![Shelf attachment](images/helical_antenna_assembly/0113_rod_mount.png)|![Shelf attachment 2](images/helical_antenna_assembly/0208_shelf_attachement.png)|
|---|---|

**2. Mix and draw up epoxy**

Mix the two-part epoxy resin according to the manufacturer's instructions. Draw it into syringes with large blunt-tip needles for controlled application.

|![Epoxy resin](images/helical_antenna_assembly/0201_epoxy_resin.png)|![Drawing epoxy into syringe](images/helical_antenna_assembly/0202_epoxy_syringe_draw.png)|
|---|---|

**3. First application - top side of rings**

Turn the rod upside down. Apply epoxy to the top face of each pacifier-to-rod junction. The bottom face is still covered by hot glue at this point, so leave it.

|![Epoxy application](images/helical_antenna_assembly/0203_epoxy_application.png)|![Epoxy application 2](images/helical_antenna_assembly/0204_epoxy_application_2.png)|
|---|---|
|![Epoxy application 3](images/helical_antenna_assembly/0205_epoxy_application_3.png)|![Pacifier done](images/helical_antenna_assembly/0206_pacifier_done.png)|

The epoxy may wick into small gaps between the pacifier and the rod which should increase the bonding strength. However, drips are undesired and hould be wiped with acetone.

**4. Second application - bottom side of rings**

Remove the rod from the shelf fixture, turn it around and reinsert it in the fixture. 

Remove the hot glue, then apply epoxy to the previously covered bottom faces of each pacifier.

| ![Round two](images/helical_antenna_assembly/0210_epoxy_application_round_two.png) | ![Round two 2](images/helical_antenna_assembly/0211_epoxy_application_round_two_2.png) |
|---|---|

Allow to cure fully before proceeding.

---

### Phase 3 - Winding the Helical Coil

**1. The winding template**

Use the 3D-printed winding help form to shape the copper tube into the correct helix diameter. Printed winding clamps hold the tube against the form, secured with woodworking clamps.

<p align="center">
  <img src="images/helical_antenna_assembly/0302_winding_template_attachment.jpg" alt="Copper tube held against the winding template by a clamp" width="600">
</p>

[Winding Help](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Winding%20Help.stl) · [Winding Clamp](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Winding%20Clamp.stl)

**2. Wind the coil**

With the tube clamped to the template, rotate it around the mandrel in a continuous helical motion, and secure it after each turn with a clamp. The copper tube should more or less keep its shape.

<p align="center">
  <img src="images/helical_antenna_assembly/0305_winding.jpg" alt="Winding the copper coil around the template with three clamps" width="600">
</p>

The coil may not seem be perfectly straight due to its springy behaviour, but this does not affect function since it will be hold by the pacifiers.

<p align="center">
  <img src="images/helical_antenna_assembly/0309_finished_coil_on_template.jpg" alt="Wound copper coil on the template with the clamps removed" width="600">
</p>
---

### Phase 4 - Inserting the Coil

**1. Insert the coil into the pacfifiers**

Insert the finished coil into the pacifier assembly on the rod with a smooth rotating motion.

<p align="center">
  <img src="images/helical_antenna_assembly/0401_inserting_coil.jpg" alt="Inserting the copper coil through the orange pacifiers on the support rod" width="600">
</p>

This step is very easy and should take about 5 minutes.

**2. Trim the coil**

Once fully seated, trim the copper tube flush at the last pacifier. This can be done with a small multitool or a metal saw

**3. Bend the end straight**

Bend the end of the tube straight towards the groundplane.

---

### Phase 5 - Base Plate & Final Assembly

**1. Prepare the aluminum ground plane**

Drill a center hole through the aluminum plate sized to pass the fiberglass rod. Around it, drill holes for the cone mounting screws (M6). Add holes for the SMA connector (M2.5). The [included drilling template](../groundstation/antenna/helical/drilling_template.pdf) can be used: print it and stick it on the plate with adhesive.

This is also a good time to drill the corner holes for the guy-wire string attachment, while the plate is already on the drill press.

|![Cones](images/helical_antenna_assembly/0500_cones.png)|![Drilled plate](images/helical_antenna_assembly/0501_drilled_plate.png)|
|---|---|

**2. Assemble the cones and connector**

Install the SMA connector using the M2.5 screws. Pass the SMA conenctor from the Antenna side in, so it can be disassembled afterward.  Mount the [Top Cone](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Top%20Cone.stl) from above and bolt it down with the M6 screws. Finally, attach the [Bottom Cone](../groundstation/antenna/helical/Auxiliary%20Design%20Files/Bottom%20Cone.stl) from below, by removing the nuts from the Top Cone, and using them to bolt the Bottom Cone to the Top Cone

| ![SMA connector mounted through the ground plane before fitting the cone](images/helical_antenna_assembly/0504_sma_connector_plate.jpg) | ![Mounted cone and SMA connector with the copper tube positioned before soldering](images/helical_antenna_assembly/0505_sma_connector_cone.jpg) |
| --- | --- |

---

### Phase 6 - Soldering

**1. Prepare the tube end**

Trim the straight end of the tube to the correct length. Use sandpaper to rough the surface and remove the oxide layer. Clean with isopropyl alcohol.

**2. Solder copper tube to SMA connector**

Use a good amount of flux, a heat gun and a soldering iron to attach the end of the tube to the sma connector.

| ![Copper tube soldered to the SMA connector center pin](images/helical_antenna_assembly/0604_soldered.jpg) | ![Close-up of the solder joint at the copper tube end](images/helical_antenna_assembly/0605_soldered_detail.jpg) |
| --- | --- |

---

## Build Checklist

### Phase 1 - Rod Preparation & Pacifier Placement
- [ ] Verify pacifier fit on the fiberglass rod
- [ ] Clean fiberglass rod with isopropyl alcohol
- [ ] Mark 10 cm from the top of the rod for the first pacifier position
- [ ] Hot-glue first pacifier in place
- [ ] Rotate assembly while glue cools to prevent sagging
- [ ] Add next pacifier with the spacing template and add hot glue to one side
- [ ] Remove template, reinforce with additional hot glue
- [ ] Repeat for all 22 pacifiers down the rod

### Phase 2 - Epoxy Application
- [ ] Mix two-part epoxy resin and draw into syringes
- [ ] Turn rod upside down, apply epoxy to top face of all pacifier junctions
- [ ] Let cure fully
- [ ] Remove all hot glue
- [ ] Apply epoxy to bottom face of all pacifier junctions
- [ ] Let cure fully

### Phase 3 - Winding the Helical Coil
- [ ] Clamp copper tube to winding form using printed clamps and woodworking clamps
- [ ] Wind copper tube into helix along the full length of the tube and secure with clamps
- [ ] Remove coil from winding form

### Phase 4 - Inserting the Coil
- [ ] Insert coil into pacifier assembly with a rotating motion
- [ ] Trim copper tube flush at the last pacifier
- [ ] Bend the end of the tube straight

### Phase 5 - Base Plate & Final Assembly
- [ ] Drill center hole in aluminum plate for the fiberglass rod
- [ ] Drill holes for M6 cone screws around center hole
- [ ] Drill holes for M2.5 SMA connector screws
- [ ] Drill corner holes for guy-wire string attachment
- [ ] Install SMA connector with 4× M2.5×10 screws and M2.5 nuts
- [ ] Pass rod through plate and mount Top Cone with 8× M6×25 screws and M6 nuts
- [ ] Attach Bottom Cone one the M6 screws

### Phase 6 - Soldering
- [ ] Trim the straight end of the tube
- [ ] Squeeze the end with pliers or use a metal saw to cut it to length (WIP to determine which is better)
- [ ] Prepare the surface with sandpaper and isopropyl alcohol
- [ ] Use flux and an additional heat source like a heat gun and a soldering iron to solder the end to the SMA connector
