# System overview

This document provides detailed information about our electronics, firmware, antenna, and GUI systems.

<p align="center"><img src="media/images/System_Block_Diagram.svg" width="400" /></p>

The whole system is designed for an effective range of 18 km. To accomplish this goal, the signal strength at the receiver must be strong enough to be processed. Our link budget calculation as outlined in [this document](linkbudget.md) ensures that our system meets this requirement.

## Electronics

**Note:** So far, the ground station and the flight computer use the same electronics hardware. We plan to design dedicated ground station hardware in the future.

### Radio frequency

The license-free frequency bands in Germany are regulated by the Bundesnetzagentur. Frequencies between 100 MHz and 1000 MHz are of primary interest to us. The relevant regulations can be found in [this document](https://www.bundesnetzagentur.de/SharedDocs/Downloads/DE/Sachgebiete/Telekommunikation/Unternehmen_Institutionen/Frequenzen/Allgemeinzuteilungen/FunkanlagenGeringerReichweite/2018_05_SRD_pdf). The frequency band between 869.40 MHz and 869.65 MHz can be used with an EIRP of up to 27 dBm or 500 mW, with a duty cycle of 10%.

### Radio modules

We have chosen the Radiocrafts RC1780HP-RC232 radio modules, which operate at frequencies from 869.41 MHz to 869.64 MHz and can achieve output powers of up to 27 dBm. The operation is straightforward due to the UART interface. The datasheet can be found [here](https://radiocrafts.com/uploads/RC17xxHP-RC232_Datasheet.pdf). Additionally, there is a separate manual for the RC232 series of radio modules that includes all configuration commands and more information, available [here](https://radiocrafts.com/uploads/RC232_user_manual.pdf). Application notes can be downloaded [here](https://radiocrafts.com/resources/document-library/?rs=Application%20Notes).

### Microcontroller

We use the AVR128DB64 microcontroller in the 64-pin LQFP version ([datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/AVR128DB28-32-48-64-DataSheet-DS40002247A.pdf)).

### PCB design

The PCB is based on the standard layout of our rocketry club, featuring a round design with a diameter of 10 cm and a flattened edge for improved cable management. Power and data are distributed via stackable pin headers located on the left and right sides. An I2C connection is employed for communication with other subsystems.

During the pcb design process, we considered the Radiocrafts [RF PCB Layout Recommendation Application Note](https://radiocrafts.com/uploads/AN061_RF_PCB_Layout_Recommendations.pdf) and a [RF PCB Design Guide](https://www.proto-electronics.com/blog/routing-guidelines-rf-pcb).
On one edge of the PCB, a ground strip is included, connected by numerous vias to the solid ground plane (layer 2).

A T-network is also included to match the antenna's impedance to 50 Ohms.

## Firmware

### General

In the setup function, pin declarations and starting conditions are established. The radio module is initialized, and the desired configurations are applied after a configuration reset. Additionally, the flight computer initializes the I2C connection to the other subsystems of the flight computer (such as sensorics) and the ground station initializes the UART connection to the ground station computer.

In the loop function, radio commands (such as ping, toggle flight mode, toggle low power mode) are exchanged, and data from the subsystems is collected and also exchanged. 
The low power mode toggles the LEDs on the board.

### Radio module library

To ensure high modularity and a clean codebase, we created a RC1780HP-RC232 code library, which can be found [here](../common/lib/RC1780HP/) together with its documentation.
The library does **not** allow the use of all the functions of the radio module but focuses only on the ones needed for our project. However, the included functions can be easily adapted for other uses.

### Data budget and packet structure

To achieve the highest possible range, we opted to use a low data rate, specifically 1.2 kbps.
As a compromise between sampling rate and packet size, we chose a sampling rate of 8 Hz, resulting in 150 bits or 18.75 bytes per packet. 
Since the data link should not operate at full capacity, we allocate a buffer of over 10%, leading to a final packet size of 15 bytes.

The packet structure is described [here](package_structure.md).

To consider the 10 % duty cycle, the flight computer starts to transmit continuously when the flight mode is toggled by a radio command. After a preset time, the continuous transmission stops and the standby transmission once every few seconds starts again.

### Packet encoding/decoding library

The encoding and decoding of packets according to our [packet structure](packet_structure.md) are handled by a dedicated library, which can be found [here](../common/lib/Packet/) along with its documentation.

## Antennas

### General

So far, we only use [dipole stick antennas](https://www.digikey.de/en/products/detail/te-connectivity-linx/ANT-868-CW-HW-SMA/5592340) for our telemetry system.
In the future, we plan to design and build our own antennas to be able to adapt them to our specific needs.
Our plan is to use a QFH antenna with a omnidirectional pattern on the flight computer and a directional helix antenna on the ground side.

### Antenna design

Viele Informationen zu Antennen:
[antenna-theory.com](https://www.antenna-theory.com/)

Informationen zu QFH-Antennen:
[jcoppens.com](https://jcoppens.com/ant/qfh/index.en.php)

Informationen zum Anschluss von QFH-Antennen:
[jcoppens.com](https://jcoppens.com/ant/qfh/adapt.en.php)

Informationen zu Helixantennen:
[jcoppens.com](https://jcoppens.com/ant/helix/index.en.php)

Artikel zu Helixantennen: [Link](https://www.microwaves101.com/encyclopedias/helix-antennas)

Paper zu Design von Helixantennen: [Link](https://bpb-us-e1.wpmucdn.com/sites.gatech.edu/dist/4/463/files/2015/06/HelixAPMagazineSubmission.pdf?bid=463)

### Antenna measurements and impedance matching

Viele Informationen zu Antennenmessungen:
[antenna-theory.com](https://www.antenna-theory.com/measurements/antenna.php)

Grundlagen zu Messgrößen bei Messungen mit einem VNA (S-Parameter):
[Youtube](https://youtu.be/-Pi0UbErHTY?si=Z9UQJC-R-1Vzc-xW)

Grundlagen zu Messgrößen bei Messungen mit einem VNA (Smith-Chart):
[Youtube](https://youtu.be/TsXd6GktlYQ?si=DfGhaZ3w0biYOcfI)

Antenne mit einem VNA vermessen und mit 4NEC2 simulieren:
[Youtube](https://youtu.be/l2c46uA50zg?si=s27nZCh-ScBlFWUF)

Antenne mit einem VNA vermessen:
[Youtube](https://youtu.be/rbXq0ZwjETo?si=DdEQ7rzXj86T0cxC)

Grundlagen zur Benutzung eines VNAs:
[Youtube](https://youtu.be/91ZRTFZ40rw?si=-yBII5ZVjXriQ2fS)

Design eines L-Matching Netzwerks mit einem VNA und einem Smith-Chart:
[Youtube](https://youtu.be/IgeRHDI-ukc?si=xvtN1C7xtP1WACcb)

Mehrteiliger Artikel zur Impedanzanpassung: [Link](https://www.electronicdesign.com/technologies/analog/whitepaper/21133206/back-to-basics-impedance-matching)

Kurzer Artikel zur Impedanzanpassung: [Link](https://www.escatec.com/blog/antenna-matching)

## GUI software