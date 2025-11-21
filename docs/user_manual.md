# ASCENT II Telemetry System User Manual

## Electronics assembly

The process is similar for the onboard and ground station systems.

### View and edit the schematic or PCB design files

Our electronics hardware is designed using the open source EDA KiCAD. The schematic and PCB design files can be viewed and  are editable. The schematic is also included in [PDF format](../onboard/pcb/TelemetryOnboard_Schematic.pdf).

### Sourcing PCBs
The PCBs can be sourced from any PCB manufacturing service like JLCPCB or PCBWAY. We included the [Gerber Production Files](../onboard/pcb/Production%20Files/Production%20Files.zip) in the repository. We recommend ordering a solder paste stencil as well, as it simplifies the soldering process.

### Sourcing components

We source most of our electronics components from Digikey. We included a [Bill of Materials](../onboard/pcb/TelemetryOnboard_BOM.csv) where a direct link to Digikey is provided. Most of the components are also available at similar sellers like Mouser.

### SMD component assembly

First, the surface mounted components are soldered. We recommend the Chipquik TS391LT lead free, thermally stable, no-clean, low temperature solder paste, which also comes at a reasonable price. To apply the solder paste, the PCB is fixated on a table using surplus PCBs. Next, the solder paste stencil is aligned and fixated as well. A small amount of solder paste can be applied and spreaded out using a spatula or an old credit card. When completed, the stencil is removed and the components can be placed on the PCB with tweezers, starting with the smallest components.
We recommend using a hot plate like the Uyue 946C to melt the solder, but a hot air station or a reflow oven can also be used.

### THT component assembly

After the SMD components are soldered, the through hole mounted components can be soldered. by heating the part and the pad before adding the solder and using a bit of flux, good results can be obtained.

### PCB Cleaning

The PCB can be gently cleaned using a soft toothbrush and isopropyl alcohol. The thereby solved flux can be rinsed with isopropyl alcohol.

## Firmware

### View and edit the firmware

Our firmware is designed to be used with Visual Studio Code and the PlatformIO extension. The firmware folder of either the ground station or the onboard system can be directly opened in VSCode. 

### Upload the firmware

To upload the firmware to the system, an UPDI programmer like the Adafruit UPDI Friend is needed. The corresponding COM port has to be selected in VSCode.

## Operation

### Powering the system

For the system to be operational, both the 3.3 V and the 5 V lines have to be connected. Any of the respective positions on the pin headers can be used. To maintain a safe margin, a current of 1 A each should be possible.

Note: When using an external power supply, the 3.3 V lines of UPDI programmers or UART to USB adapters should never be connected.

### Serial communication

For the serial communication with the system, an UART to USB adapter has to be used. 
We recommend using a dedicated serial monitor like [Coolterm](https://freeware.the-meiers.org/), for which we included our [settings file](../groundstation/Coolterm_SerialMonitor_Settings.stc).

### Antenna

The system should never be operational without a connected antenna, as otherwise the high output power can permanently damage the radio module.

If testing the radio communication between the onboard system and the ground station system, a distance of at least 1.5 m should always be established.