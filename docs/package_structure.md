# Telemetry Radio Package Structure

The data rate of 1.2 kbps, the desired sampling rate of 10 Hz and a retained buffer of 10 % leads to a package size of 13 Byte.

This document describes the specific use of the 13 Byte and thus the data structure of each data package.

## Package Structure Overview

The following table lists the components of each data package:
| Byte position | Use | Size |
| --- | --- | --- |
| 0 | [Address](#Address) | 4 bit |
| 0 | [COBS](#COBS) | 4 bit |
| 1 | [Status](#Status) | 4 bit |
| 1 | [Battery level](#Battery-level) | 4 bit |
| 2 to 3 | [Height](#Height) | 16 bit |
| 4 | [Acceleration](#Acceleration) | 8 bit |
| 5 to 11 | [GNSS](#GNSS) | 56 bit |
| 12 | [End byte](#End-byte) | 8 bit |

## Data Components

### Address
- component size: 4 bits
- value range: 16 unique destination addresses

### COBS
- component size: 4 bits
- value range: 0 to 11

Consistent Overhead Byte Stuffing ([Link](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing)) is used to avoid multiple occurances of the unique end byte 0xDD.
If there is no occurance of 0xDD in the data bytes, the COBS value is set to 0x0.
If there is one or mulitple occurances, the COBS value is set to the byte position of the first occurance.
Then the value of the first occurance (formerly 0xDD) is set to the byte position of the second occurance and so on.
This is repeated until no 0xDD except the end byte is left. 
The last occurance will be replaced by the value 0x00 to signal the end of the COBS chain. 

The following table shows an example package with many occurances of 0xDD being modified using the described method. 
All changes are marked in italic in the modified package.
The modified package only includes one 0xDD in the end and can easily be converted back to its original shape.
Note: The byte 0 which includes the COBS value also includes the destination address (in this case 0x8)
| Byte position | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | A | B | C |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Original Package | 80 | 56 | DD | A8 | 9B | DD | 77 | 1F | DD | 0E | DD | B6 | DD |
| Modified Package | ***82*** | 56 | ***05*** | A8 | 9B | ***08*** | 77 | 1F | ***0A*** | 0E | ***00*** | B6 | DD |
 
### Status
- component size: 4 bits
- value range: 16 different statuses
 
### Battery level
- component size: 4 bits
- value range: -50 % to 100 %
- resolution: 10 % resolution

### Height
- component size: 16 bits
- value range: 0 m to 16400 m
- resolution: 0.25 m

A 16 bit integer stores values from 0 to $2^{16} - 1 = 65535$.
With our desired resolution of 0.25 m, heights from 0 m to $\approx$ 16400 m can be stored.
Since we don't expect large negative heights, all values below 0 m are set to 0 m.

### Acceleration
- component size: 8 bits
- value range: 0 g to tbd. g
- resolution: tbd. g

An 8 bit integer stores values from 0 to $2^{8} - 1 = 255$.
With our desired resolution of tbd. g, accelerations from 0 g to $\approx$ g can be stored.
> Negative Accelerations?

### GNSS
- component size: 56 bits (28 bits each for latitude and longitude)
- value range: -90 ° to 90 ° (latitude) and -180 ° to 180 ° (longitude)
- resolution: 7.5 cm (latitude) and 9.5 cm (longitude)

Latitude and Longitude are stored in two seperate 28 bit integers. 
The resolutions can be calculated using the following formula: <br> 
$\Delta x = 2 \cdot \pi \cdot R \cdot \frac{\Delta \varphi}{360 °} \cdot \frac{1}{2^{28}}$ <br>
$R$ is the radius of the circle under analysis.
When calculating the resolution along the latitude, $R$ equals the Earth's radius of 6731 km.
When calculating the resolution along the longitude, $R$ is depending on the latitude: $R = cos\left(\theta_{lat} \cdot \frac{2 \pi}{360 °}\right)$.
Gießen is located at a latitude $\theta_{lat} = 50.58 °$ which leads to $R = 4045.6$ km. <br>
$\Delta \varphi$ is the angular range and equals 180 ° for latitude and 360 ° for longitude. <br>
Thus the achievable resolution is $\Delta x \approx 7.5$ cm for latitude and $\Delta x \approx 9.5$ cm for longitude.

### End byte
- component size: 8 bits
- value: 0xDD

The unique end byte is used to identify the end of each package.
If there are multiple occurances of the end byte, the COBS method is used to encode all except the real end byte.
To avoid having the same end byte and byte 0 (COBS and adress), 0xDD was chosen as the unique end byte.
Since the 4 COBS bits in byte 0 will never reach values higher than 11 or B, 0xDD is guaranteed to be unique.
