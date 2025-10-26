# ASCENT II Telemetry System User Manual

## Electronics

The PCB assembly process is similar for the onboard and ground station systems.

### View and edit the schematic or PCB

Our electronics hardware is designed using the open source EDA KiCAD. Here, the schematic and PCB design files can be viewed and edited. The schematic is also included in [PDF format](../onboard/pcb/TelemetryOnboard_Schematic.pdf).

### Sourcing components

We source most of our electronics components from Digikey. We included a [Bill of Materials](../onboard/pcb/TelemetryOnboard_BOM.csv) where a direct link to Digikey is provided. The components are also mostly available at similar sellers like Mouser.

The PCBs can be sourced from any PCB manufacturing service like JLCPCB or PCBWAY. We included the [Gerber Production Files](../onboard/pcb/Production%20Files/Production%20Files.zip) as well. We recommend ordering a solder paste stencil as well, as it simplifies the soldering process.

### SMD components

First, the surface mounted components are soldered. We recommend the Chipquik TS391LT lead free, thermally stable, no-clean, low temperature solder paste, which also comes at a reasonable price. To apply the solder paste, the PCB is fixated on a table using surplus PCBs. Next, the solder paste stencil is aligned and fixated as well. A small amount of solder paste can be applied and spreaded out using a spatula or an old credit card. When completed, the stencil is removed and the components can be placed on the PCB with tweezers, starting with the smallest components.
We recommend using a hot plate like the Uyue 946C to melt the solder, but a hot air station or a reflow oven can also be used.

### THT components

After the SMD components are soldered, the through hole mounted components can be soldered. Using a bit of flux, good results can be obtained.

### Cleaning

The PCB can be gently cleaned using a soft toothbrush and isopropyl alcohol.

## Firmware

### View, edit and upload the firmware

Our firmware is designed to be used with Visual Studio Code and the PlatformIO extension. The firmware folder of either the ground station or the onboard system can be directly opened in VSCode. To upload the firmware to the system, an UPDI programmer like the Adafruit UPDI Friend is needed. The corresponding COM port has to be selected in VSCode.

### Serial communication

For the serial communication with the system, an UART to USB adapter has to be used. 
We recommend using a dedicated serial monitor like [Coolterm](https://freeware.the-meiers.org/), for which we included our [settings file](../groundstation/Coolterm_SerialMonitor_Settings.stc).