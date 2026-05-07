# ASCENT Experimental Rocket Telemetry System

|<img src="/onboard/pcb/images/Onboard_PCB_Rendering_QFH.png" width="400" /></p> | <img src="/groundstation/pcb/Motherboard/images/Motherboard_PCB_Rendering.png" width="400" /></p><img src="/groundstation/pcb/Daughterboard/images/Daughterboard_PCB_Rendering.png" width="400" /></p>|
|---|---|
|<p style="text-align: center;">[The Onboard System](/onboard/)</p>|<p style="text-align: center;">[The Groundstation System](/groundstation/)</p>|

---

## Overview
The ASCENT telemetry system is part of the ASCENT flight computer of the student rocketry club [Spaceflight Rocketry Gießen e.V.](https://spaceflight-rocketry-giessen.de/), developed for the PIPE 2 and ARCHER experimental rockets.  
This dual-frequency 169/869 MHz telemetry system based on Radiocrafts RC232 allows bidirectional data exchange between rockets and ground stations with a range of 20 km and a minimum data rate of 1.2 kbps.
The design can also be used in areas outside of rocketry like Smart Home or RC.

<p align="center"><img src="/docs/images/System_Block_Diagram.svg" /></p>

## Basic functionality

- Receiving flight data from our rockets
- Sending radio commands to our rockets
- Displaying live telemetry on a screen or UI
- Storing flight data for post-flight analysis

## Actual performance
In January 2026, we performed our first long range test over a distance of 2 km. Despite poor weather conditions and object inside the first Fresnel zone, the received signal strength was on par with the theoretical maximum without any connection losses. This test ruled out major design flaws which could result in large losses.

This excellent performance was confirmed by multiple medium range tests.

<p align="center"><img src="/docs/images/long_range_test.png" width="600" /></p>

In April 2026, the system was successfully tested on the PIPE 2 rocket to an altitude of 350 m.

<p align="center"><img src="/docs/images/pipe2_launch.png" width="600" /></p>

---

## Repository Contents
This repository contains all files necessary to reproduce the telemetry system, including hardware, firmware, and software.
It also includes [user manuals](/docs/user_manual.md) and [design rationals](/docs/design_overview.md) which help to understand and adapt the system.

### 1. Antenna Hardware
So far, this repository includes [design files](/groundstation/antenna/) and [assembly instructions](/docs/helix_antenna_assembly_manual.md) for our helical 869 MHz groundstation antenna.

<p align="center"><img src="/groundstation/antenna/images/GroundstationAntenna_picture_3.jpg" width="600" /></p>

We also do our own FDTD-simulations to verify the antenna design and will include them in the repository soon.

<p align="center"><img src="/groundstation/antenna/images/GroundstationAntenna_simulation.png" width="600" /></p>

In the future, the repository will also contain an 869 MHz QFH design.

### 2. Electronics Hardware
<p align="center"><img src="onboard/pcb/images/Onboard_PCB.png" width="600"/></p>

Separate [onboard](/onboard/pcb/) and [groundstation](/groundstation/pcb/) electronics.

Included: 
- Schematics
- PCB design files
- Bill of Materials
- 3D models

### 3. Electronics Firmware

Included:
- [Onboard](/onboard/firmware/) and [ground station](/groundstation/firmware/) electronics firmware 
- [Radiocrafts RC1780HP-RC232 code library](/common/libraries/Radiocrafts_RC17xxHP_RC232/)
- [Package encoding and decoding code library](/common/libraries/Packet/)

### 4. Groundstation UI Software
  <img src="groundstation/gui/example_images/main_view.png" width="600" />

[Python-based software](/groundstation/gui/) to display telemetry data on a modern, minimalistic interface with the ability to store flight data. In the future, sending radio command directly in UI will be possible.

Included:
- GNSS map view
- Height plot over time
- Acceleration indicator
- Battery voltage indicator with visual warnings
- Status event indicator

---

## Legal notice
Please note that radio systems may be subject to local regulations. Ensure that any testing or deployment of these systems complies with national and regional laws regarding RF transmission. The project maintainers are not responsible for misuse or regulatory violations.  

## License

Copyright Spaceflight Rocketry Giessen e.V. 2026.<br />
This source describes Open Hardware and is licensed under the CERN-OHL-S v2.<br />
You may redistribute and modify this source and make products using it under the terms of the [CERN-OHL-S v2 or any later version](LICENSE).<br />
This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY, INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A PARTICULAR PURPOSE. Please see the CERN-OHL-S v2 for applicable conditions.<br />
Source location: https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry<br />
As per CERN-OHL-S v2 section 4, should you produce hardware based on this source, you must where practicable maintain the Source Location in its documentation or license information.<br />
