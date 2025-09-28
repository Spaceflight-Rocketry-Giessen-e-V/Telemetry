# Telemetry Radio Packet Structure

The data rate of 1.2 kbps, the desired sampling rate of 8 Hz and a retained buffer of at least 10 % demand a packet size of 16 Byte at most. We chose 15 Bytes with a retained buffer of 3.75 bytes per packet to guarantee a robust and reliable data exchange.

This document describes the specific use of individual 15 byte data packets.

## Packet Structure Overview

The following table lists the components of each data package. 
The 16th byte (#15), the received signal strength, is appended after receiving the packet and is thus not transmitted.
| Byte position | Use | Size |
| --- | --- | --- |
| 0 | [Address](#Address) | 4 bits |
| 0 | [COBS](#COBS) | 4 bits |
| 1 | [Status](#Status) | 6 bits |
| 1 to 2 | [Acceleration](#Acceleration) | 10 bits |
| 3 to 4 | [Height (Pressure)](#Height-(Pressure)) | 16 bits |
| 5 to 6 | [Height (GNSS)](#Height-(GNSS)) | 16 bits |
| 7 to 13 | [GNSS (Lat+Lon)](#GNSS-(Lat+Lon)) | 52 bits |
| 13 | [Battery level](#Battery-level) | 4 bits |
| 14 | [End byte](#End-byte) | 8 bits |
| 15 | [RSSI](#RSSI) | 8 bits |

## Data Components

### Address
- component size: 4 bits
- value range: 16 unique destination addresses

The addressing can be used, when multiple flight computers or ground stations are in operation simultaneously.

### COBS
- component size: 4 bits
- value range: 0 to 11

Consistent Overhead Byte Stuffing ([Link](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing)) is used to avoid multiple occurances of the unique end byte 0xEE.
If there is no occurance of 0xEE in the data bytes, the COBS value is set to 0x0.
If there is one or mulitple occurances, the COBS value is set to the byte position of the first occurance.
Then the value of the first occurance (formerly 0xEE) is set to the byte position of the second occurance and so on.
This is repeated until no 0xEE except the end byte is left. 
The last occurance will be replaced by the value 0x00 to signal the end of the COBS chain. 

The following table shows an example package with many occurances of 0xEE being modified using the described method. 
All changes are marked in italic in the modified package.
The modified package only includes one 0xEE in the end and can easily be converted back to its original shape.
Note: The byte 0 which includes the COBS value also includes the destination address (in this case 0x8)
| Byte position | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | A | B | C | D | E |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Original Package | 80 | 56 | EE | A8 | 9B | EE | 77 | 1F | EE | 0E | EE | B6 | 2A | 5C | EE |
| Modified Package | ***82*** | 56 | ***05*** | A8 | 9B | ***08*** | 77 | 1F | ***0A*** | 0E | ***00*** | B6 | 2A | 5C | EE |
 
### Status
- component size: 6 bits
- value range: indication for flight mode, low power mode, overall status and 8 individual launch events

The status component includes one bit for indicating the flight mode (rocket is armed and telemetry starts sending data at 8 Hz), low power mode (all LEDs are turned off) and overall flight computer status (all subsystems are good) respectively.
The remaining 3 bits are used to represent 8 individual launch events like *standby*, *launch detected*, *apogee detected*, *landing detected*.

### Acceleration
- component size: 10 bits
- value range: -32 g to 32 g
- resolution: 0.0625 g

An 10 bit integer stores values from 0 to $2^{10} - 1 = 1023$.
We expect our rocket to remain between -32 g and +32 g, which results in a resolution of 0.0625 g.

### Height (Pressure)
- component size: 16 bits
- value range: 0 m to 16400 m
- resolution: 0.25 m

A 16 bit integer stores values from 0 to $2^{16} - 1 = 65535$.
With our desired resolution of 0.25 m, heights from 0 m to $\approx$ 16400 m can be stored.
Since we don't expect large negative heights, all values below 0 m are set to 0 m.

### Height (GNSS)
- component size: 16 bits
- value range: 0 m to 16400 m
- resolution: 0.25 m

The same calculation as for the pressure height applies.

### GNSS (Lat+Lon)
- component size: 52 bits (26 bits each for latitude and longitude)
- value range: -90 ° to 90 ° (latitude) and -180 ° to 180 ° (longitude)
- resolution: 7.5 cm (latitude) and 9.5 cm (longitude)

Latitude and Longitude are stored in two seperate 28 bit integers. 
The resolutions can be calculated using the following formula: <br> 
$\Delta x = 2 \cdot \pi \cdot R \cdot \frac{\Delta \varphi}{360 °} \cdot \frac{1}{2^{26}}$ <br>
$R$ is the radius of the circle under analysis.
When calculating the resolution along the latitude, $R$ equals the Earth's radius of 6731 km.
When calculating the resolution along the longitude, $R$ is depending on the latitude: $R = cos\left(\theta_{lat} \cdot \frac{2 \pi}{360 °}\right)$.
Gießen is located at a latitude $\theta_{lat} = 50.58 °$ which leads to $R = 4045.6$ km. <br>
$\Delta \varphi$ is the angular range and equals 180 ° for latitude and 360 ° for longitude. <br>
Thus the achievable resolution is $\Delta x \approx 29.9$ cm for latitude and $\Delta x \approx 37.9$ cm for longitude.
 
### Battery level
- component size: 4 bits
- value range: 5.4 V to 8.4 V
- resolution: 0.2 V

The lowest value is chosen due to the minimum input voltage of the voltage regulator given at 5.4 V. 
With 4 bits and a resolution of 0.2 V, the maximum value is 8.4 V which covers most of the commonly used battery types like 2s lithium ion batteries.

### End byte
- component size: 8 bits
- value: 0xEE

The unique end byte is used to identify the end of each package.
If there are multiple occurances of the end byte, the COBS method is used to encode all except the real end byte.
To avoid having the same end byte and byte 0 (COBS and adress), 0xEE was chosen as the unique end byte.
Since the 4 COBS bits in byte 0 will never reach values higher than 13 or 0xD, 0xEE is guaranteed to be unique.

### RSSI
- component size: 8 bits
- value range: -127.5 dBm to 0 dBm
- resolution: 0.5 dBm

The Received Signal Strength Indicator (RSSI) is appended by the receiving radio module and is not transmitted.
