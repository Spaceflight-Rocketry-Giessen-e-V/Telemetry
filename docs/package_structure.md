# Telemetry Radio Package Structure

The data rate of 1.2 kbps, the desired sampling rate of 10 Hz and a retained buffer of 10 % leads to a package size of 13 Byte.

This document describes the specific use of the 13 Byte and thus the data structure of each data package.

## Package Structure

The following table lists the structure and components of each data package:
| Byte position | Use | Size |
| --- | --- | --- |
| 1 | [Start byte](#Start-byte) | 8 bit |
| 2 | [COBS](#COBS) | 4 bit |
| 2 | [Address](#Address) | 4 bit |
| 3 | [Status](#Status) | 4 bit |
| 3 | [Battery level](#Battery-level) | 4 bit |
| 4 to 5 | [Height](#Height) | 16 bit |
| 6 | [Acceleration](#Acceleration) | 8 bit |
| 7 to 13 | [GNSS](#GNSS) | 56 bit |

## Data Components

### Start byte
8 bit <br>
Unique start byte to identify the begin of a package

### COBS
4 bit <br>
Consistent Overhead Byte Stuffing ([Link](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing))

### Address
4 bit <br>
0 to 127 <br>
Unique destination ID
 
### Status
4 bit <br>
128 different statuses
 
### Battery level
4 bit <br>
-50 % to 100 %, 10 % resolution

### Height
16 bit <br>
0 m to 15000 m, 0.25 m resolution

### Acceleration
8 bit <br>
tbd.

### GNSS
56 bit <br>
Global scope with around 10 cm resolution
