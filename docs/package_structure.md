# Telemetry Radio Package Structure

The data rate of 1.2 kbps, the desired sampling rate of 10 Hz and a retained buffer of 10 % leads to a package size of 13 Byte.

This document describes the specific use of the 13 Byte and thus the data structure of each data package.

## Package Structure Overview

The following table lists the components of each data package:
| Byte position | Use | Size |
| --- | --- | --- |
| 0 | [COBS](#COBS) | 4 bit |
| 0 | [Address](#Address) | 4 bit |
| 1 | [Status](#Status) | 4 bit |
| 1 | [Battery level](#Battery-level) | 4 bit |
| 2 to 3 | [Height](#Height) | 16 bit |
| 4 | [Acceleration](#Acceleration) | 8 bit |
| 5 to 11 | [GNSS](#GNSS) | 56 bit |
| 12 | [End byte](#End-byte) | 8 bit |

## Data Components

### COBS
4 bit <br>
Consistent Overhead Byte Stuffing ([Link](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing))

### Address
4 bit <br>
0 to 15 <br>
Unique destination ID
 
### Status
4 bit <br>
16 different statuses
 
### Battery level
4 bit <br>
-50 % to 100 %, 10 % resolution

### Height
16 bit <br>
0 m to 16400 m, 0.25 m resolution <br><br>
A 16 bit integer stores values from 0 to $2^{16} - 1 = 65535$.
With our desired resolution of 0.25 m, heights from 0 m to $\approx$ 16400 m can be stored.
Since we don't expect large negative heights, all values below 0 m are set to 0 m.

### Acceleration
8 bit <br>
0 to tbd. g, tbd. g resolution <br><br>
An 8 bit integer stores values from 0 to $2^{8} - 1 = 255$.
With our desired resolution of tbd. g, accelerations from 0 g to $\approx$ g can be stored.
> Negative Accelerations?

### GNSS
56 bit <br>
Global scope with around 10 cm resolution <br><br>
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
8 bit <br>
0xDD <br><br>
The unique end byte is used to identify the end of each package.
If there are multiple occurances of the end byte, the COBS method is used to encode all except the real end byte.
To avoid having the same end byte and byte 0 (COBS and adress), 0xDD was chosen as the unique end byte.
Since the 4 COBS bits in byte 0 will never reach values higher than 11 or B, 0xDD is guaranteed to be unique.
