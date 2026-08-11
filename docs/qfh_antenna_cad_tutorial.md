# QFH Antenna CAD Tutorial

### Using Autodesk Fusion

- [Copper Wire](#copper-wire)
    - [Step 1: Create Two Triangular Coils](#step-1-create-two-triangular-coils)
    - [Step 2: Turn The Coils Into A 3D Sketch](#step-2-turn-the-coils-into-a-3d-sketch)
    - [Step 3: Add Horizontal Sections](#step-3-add-horizontal-sections)
    - [Step 4: Add Corner Bending](#step-4-add-corner-bending)
    - [Step 5: Create The Copper Wire](#step-5-create-the-copper-wire)
    - [Step 6: Clean Up The Project](#step-6-clean-up-the-project)
- [Winding Help](#winding-help)
    - [Step 1: Create Cylindrical Bodies](#step-1-create-cylindrical-bodies)
    - [Step 2: Create Wire Grooves](#step-2-create-wire-grooves)
    - [Step 3: Create Corner Grooves](#step-3-create-corner-grooves)

---

# Copper Wire

## Step 1: Create Two Triangular Coils

Use `Create &rarr; Coil` with the shown settings and adjust the diameter and height if needed. Be aware of the correct rotation for RHCP and LHCP antennas. For RHCP, the rotation should be counter-clockwise (as shown in the screenshot).

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/1.png' width = 500></p>

Use `Move/Copy` to create a copy of the coil. Turn it by 180° around the origin.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/2.png' width = 500></p>

## Step 2: Turn The Coils Into A 3D Sketch

Use `Create &rarr; Sketch` to create a sketch in die horizontal plane. Activate the `Sketch Palette &rarr; 3D Sketch` Checkbox.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/3.png' width = 500></p>

Use `Create &rarr; Project/Include &rarr; Include 3D Geometry`. Click the outer profile of each of the coils.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/4.png' width = 500></p>

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/5.png' width = 500></p>

Click on one of the projection, click on the small symbol and press delete to delete the projection and create a spline. Repeat for the other projection.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/6.png' width = 500></p>

The result should look like this:

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/7.png' width = 500></p>

## Step 3: Add Horizontal Sections

Pick one end of one spline. Use `Create &rarr; Line` to draw a line from the end point towards the origin. The length should equal your desired bending radius. 

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/8.png' width = 500></p>

Repeat for all four spline ends and connect the two top sections and two bottom sections. The result should look like this:

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/9.png' width = 500></p>

## Step 4: Add Corner Bending

Pick one end of one spline. Use `Create &rarr; Line` to draw a line.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/10.png' width = 500></p>

Drag the line along the spline until the length reaches the bending radius. It is important that the line snaps to the spline, you might zoom in a bin. In the screenshot it looks off, but the look of the cross is important. 

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/11.png' width = 500></p>

Use `Modify &rarr; Trim` to trim the spline section between the two intersections with the drawn line.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/12.png' width = 500></p>

Use `Modify &rarr; Blend Curve` to connect the remaining spline to the horizontal line.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/13.png' width = 500></p>

Repeat for all four corners.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/14.png' width = 500></p>

## Step 5: Create The Copper Wire

Use `Create &rarr; Pipe` to create the copper wire along the profile and choose the wire diameter.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/15.png' width = 500></p>

## Step 6: Clean Up The Project

Use `Remove` (not `Delete`!) to remove the two triangular spirals.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/copper wire/16.png' width = 500></p>

---

# Winding Help

## Step 1: Create Cylindrical Bodies

Use `Create &rarr; Sketch` to create a sketch in the horizontal plane and draw a circle with the diameter of the QFH antenna.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/1.png' width = 500></p>

Use `Create &rarr; Extrude` to extrude a cylinder with a positive offset of half the wire thickness to the top of the QFH.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/2.png' width = 500></p>

Use `Create &rarr; Extrude` to extrude a cylinder with a positive offset of half the wire thickness downwards.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/3.png' width = 500></p>

## Step 2: Create Wire Grooves

Use `Modify &rarr; Combine` to combine the wire with the big cylinder. Use the `Cut` operation and `Keep Tools` option.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/4.png' width = 500></p>

Use `Modify &rarr; Combine` to combine the wire with the small cylinder. Use the `Cut` operation and `Keep Tools` option.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/5.png' width = 500></p>

Use `Create &rarr; Sketch` to create a sketch in the vertical plane. Use `Draw &rarr; Circle` to draw a circle with the diameter of the wire and the center in the origin. Use `Draw &rarr; Circle` to draw a flat top and sides. Extrude the profile symmetrically and use the `Cut` operation to cut a groove into the lower cylinder.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/6.png' width = 500></p>

## Step 3: Create Corner Grooves

Pick one of the corners. Use `Construct &rarr; Plane Through Three Points` to construct a plane through the three corner points of the wire sketch (two intersection points of the blend curve and the outermost corner point).

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/7.png' width = 500></p>

Use `Create &rarr; Sketch` to create a sketch in the new plane. Use `Draw &rarr; Line` to draw a line between the two intersection points of the blend curve. Use `Draw &rarr; Rectangle` to draw a rectangle between the outermost corner point and the intersection of the blend curve with the QFH spline.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/8.png' width = 500></p>

Project the small horizontal segment and the blend curve into the sketch.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/9.png' width = 500></p>

Use `Create &rarr; Extrude` to extrude the innermost round profile symmetrically with thickness of half the wire diameter.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/10.png' width = 500></p>

Use `Construct &rarr; Tangent Plane` to construct a plane tangent to the cylinder side.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/11.png' width = 500></p>

Use `Create &rarr; Sketch` to create a sketch on the new plane. Project the outward facing side of the round extrusion onto the sketch.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/12.png' width = 500></p>

Extrude this profile with `To Object` Extend Type and `Cut` Operation and select the round profile as the end.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/13.png' width = 500></p>

`Remove` the round extrusion.

Use `Create &rarr; Extrude` to extrude the rest of the three point plane sketch towards the sharp corner, use the `Cut` option but only cut the big cylinder.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/14.png' width = 500></p>

The result should look like this.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/15.png' width = 500></p>

Repeat for all four corners.

<p align="center"><image src='images/qfh_antenna_cad_tutorial/winding help/16.png' width = 500></p>