# Radio Packet Structure

- [Data Budget](#data-budget)
- [Flight Data Packet Structure](#flight-data-packet-structure)
- [Telemetry Data Packet Structure](#telemetry-data-packet-structure)
- [Frame Components](#frame-components)
- [Data Components](#data-components)

<p align="center"><img src="images/packet_structure_diagram.png" width = 700/></p>

---

## Data Budget

With the data rate of 1.2 kbps, the desired sampling rate of 10 Hz and the desired packet size of 12 bytes a buffer of 20 % or 3 bytes per packet is retained to guarantee a robust and reliable data exchange.

This document describes the specific use of the 12 byte data packets.
We distinguish between [Flight Data Packets](#flight-data-packet-structure-overview), which are being sent 9 times every second, and [Telemetry Data Packets](#telemetry-data-packet-structure-overview), which are being sent once every second.

The encoding and decoding of the data packets is carried out by the included [Packet Library](/../common/libraries/Packet/).

The groundstation appends the received signal strength RSSI as the 13th byte (#12 in the following tables) during receiving. This byte is thus not transmitted and not present in the library encode functions.

## Flight Data Packet Structure

The Flight Data Packets include data necessary for mission control during flight to confirm a successful launch.

The following table lists the components of each Flight Data Package. 

| Byte position | Use | Size | Value Range | Resolution |
| --- | --- | --- | --- | --- |
| 0 | [COBS](#cobs) | 4 bits | 0 to 10 | / | 
| 0 | [Parity Bit](#parity-bit) | 1 bits | 0 or 1 | / |
| 0 | [Packet Identifier](#packet-identifier) | 1 bit | 0 | / |
| 0 to 1 | Acceleration | 10 bits | -16 g to 16 g | 0.03333 g |
| 2 to 3 | Height (Pressure) | 15 bits | 0 to 6500 m | 0.2 m |
| 3 to 4 | [Flight Events](#flight-events) | 5 bits | 0 to 31 | / |
| 4 to 7 | [GNSS Latitude](#latitude-longitude) | 26 bits | -90° to 90° | 0.0000026823° |
| 7 to 10 | [GNSS Longitude](#latitude-longitude) | 26 bits | -180° to 180° | 0.0000053645° |
| 11 | [End Byte](#end-byte) | 8 bits | `0xEE` | / |
| 12 | RSSI | 8 bits | -127.5 dBm to 0 dBm | 0.5 dBm |

## Telemetry Data Packet Structure

The Telemetry Data Packets include housekeeping data, data important during launchpad idle and buffer for future adjustments.

The following table lists the components of each Telemetry Data Package. 

| Byte position | Use | Size | Value Range | Resolution |
| --- | --- | --- | --- | --- |
| 0 | [COBS](#cobs) | 4 bits | 0 to 10 | / | 
| 0 | [Parity Bit](#parity-bit) | 1 bits | 0 or 1 | / |
| 0 | [Packet Identifier](#packet-identifier) | 1 bit | 1 | / |
| 0 | No Data | 2 bits | / | / |
| 1 | [Subsystem States](#subsystems-states) | 8 bits | 0 to 3 for four subsystems | / |
| 2 | No Data | 1 bit | / | / |
| 2 to 3 | Height (GNSS) | 15 bits | 0 to 6500 m | 0.2 m |
| 4 | GNSS Satellite Count | 4 bits | 0 to 15 | 1 |
| 4 | GNSS HDOP | 4 bits | 0 to 7.5 | 0.5 |
| 5 | Electronics Temperature | 4 bits | 0 °C to 150 °C | 10 °C |
| 5 | Battery Temperature | 4 bits | 0 °C to 150 °C | 10 °C |
| 6 | [Capacitors State](#capacitors-states) | 4 bits | 0 to 3 for two capacitors | / |
| 6 | [Pyros Continuity](#pyros-continuity) | 2 bits | 0 or 1 for two pyro channels | / |
| 6 | [Decoupler Pressure](#decoupler-pressure) | 1 bits | 0 or 1 | / |
| 6 | [Decoupler LDR](#decoupler-ldr) | 1 bits | 0 or 1 | / |
| 7 | No Data | 2 bits | / | / |
| 7 | Battery Voltage | 6 bits | 5 V to 8.15 V | 0.05 V |
| 8 | Battery Current | 3 bits | 0 A to 1.75 A | 0.25 A |
| 8 | Umbilical Current | 3 bits | 0 A to 1.75 A | 0.25 A |
| 8 | [Umbilical State](#umbilical-state) | 1 bit | 0 or 1 | / |
| 8 | [Low Power Mode](#low-power-mode) | 1 bit | 0 or 1 | / |
| 9 | COTS Battery Voltage | 5 bits | 5 V to 11.2 V | 0.2 V |
| 9 | No Data | 3 bits | / | / |
| 10 | No Data | 8 bits | / | / |
| 11 | [End Byte](#end-byte) | 8 bits | `0xEE` | / |
| 12 | RSSI | 8 bits | -127.5 dBm to 0 dBm | 0.5 dBm |

## Frame Components

### COBS

Consistent Overhead Byte Stuffing ([Link](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing)) is used to avoid multiple occurances of the unique end byte `0xEE`.
If there is no occurance of `0xEE` in the data bytes, the COBS value is set to `0x0`.
If there is one or mulitple occurances, the COBS value is set to the byte position of the first occurance.
Then the value of the first occurance (formerly `0xEE`) is set to the byte position of the second occurance and so on.
This is repeated until no `0xEE` except the end byte is left. 
The last occurance will be replaced by the value `0x00` to signal the end of the COBS chain. 

The following table shows an example package with many occurances of `0xEE` being modified using the described method. 
All changes are marked in italic in the modified package.
The modified package only includes one `0xEE` in the end and can easily be converted back to its original shape.
***Note:*** The byte `0x00` which includes the COBS value also includes other data (in this case `0x8`)
| Byte position | `0x00` | `0x01` | `0x02` | `0x03` | `0x04` | `0x05` | `0x06` | `0x07` | `0x08` | `0x09` | `0x0A` | `0x0B` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Original Package | 80 | 56 | EE | A8 | 9B | EE | 77 | 1F | EE | 0E | EE | EE |
| Modified Package | 8***2*** | 56 | ***05*** | A8 | 9B | ***08*** | 77 | 1F | ***0A*** | 0E | ***00*** | B6 |

### Parity Bit

The parity bit is chosen in a way that the total count of ones in the packet (including the parity bit) is an even number.

If the total count of ones is an odd number when receiving, a bit flip must have occured during transmission and the packet will not be decoded.

### Packet Identifier

Flight Data Packet: `0`
Telemetry Data Packet: `1`

### End byte

The unique end byte is used to identify the end of each package.
If there are multiple occurances of the end byte, the COBS method is used to encode all except the real end byte.
To avoid having the same end byte and byte 0 (COBS and remaining data), `0xEE` was chosen as the unique end byte.
Since the 4 COBS bits in byte 0 will never reach values higher than 10 or `0xA`, `0xEE` is guaranteed to be unique.

## Data Components

### Flight Events

The flight events are described in the [Operations Cheatsheet](/docs/operations_cheatsheet.md#status-events-reference).

### Latitude Longitude
- component size: 52 bits (26 bits each for latitude and longitude)
- value range: -90 ° to 90 ° (latitude) and -180 ° to 180 ° (longitude)
- resolution: 29.9 cm (latitude) and 37.9 cm (longitude)

Latitude and Longitude are stored in two seperate 28 bit integers. 
The resolutions can be calculated using the following formula: <br> 
$\Delta x = 2 \cdot \pi \cdot R \cdot \frac{\Delta \varphi}{360 °} \cdot \frac{1}{2^{26}}$ <br>
$R$ is the radius of the circle under analysis.
When calculating the resolution along the latitude, $R$ equals the Earth's radius of 6731 km.
When calculating the resolution along the longitude, $R$ is depending on the latitude: $R = cos\left(\theta_{lat} \cdot \frac{2 \pi}{360 °}\right)$.
Gießen is located at a latitude $\theta_{lat} = 50.58 °$ which leads to $R = 4045.6$ km. <br>
$\Delta \varphi$ is the angular range and equals 180 ° for latitude and 360 ° for longitude. <br>
Thus the achievable resolution is $\Delta x \approx 29.9$ cm for latitude and $\Delta x \approx 37.9$ cm for longitude.

### Subsystems States

Each of the four subsystems has four possible states:
`0`: Not connected
`1`: Connected but not operational
`2`: Connected and partly operational
`3`: Connected and operational

### Capacitors States

> Voltage levels not yet defined

Each of the two capacitors of the flight control subsystem has four possible voltage levels:
`0`: 
`1`: 
`2`: 
`3`: 

### Pyros Continuity

Each of the two pyro channel has a continuity measurement:
`0`: No continuity
`1`: Continuity

### Decoupler Pressure

`0`: Not enough pressure for operation
`1`: Enough pressure for operation

### Decoupler LDR

`0`: No decoupling detected
`1`: Decoupling detected

### Umbilical State

`0`: Umbilical connection not detected
`1`: Umbilical connection detected

### Low Power Mode

`0`: Low power mode deactivated
`1`: Low power mode activated
