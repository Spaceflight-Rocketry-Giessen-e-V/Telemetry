The data rate of 1.2 kbps, the desired sampling rate of 10 Hz and a retained buffer of 10 % leads to a package size of 13 Byte.

This document describes the specific use of the 13 Byte and thus the data structure of each data package.

The following table lists the structure and components of each data package:
| Byte(s) | Use | Size | Data range |
| --- | --- | --- | --- |
| 1 | start byte | 8 bit | tbd. |
| 2 | COBS | 4 bit | - |
| 2 | address | 4 bit | 0 to 127 |
| 3 | status | 4 bit | 128 different statuses |
| 3 | battery level | 4 bit | -50 % to 100 %, 10 % resolution |
| 4 to 5 | height | 16 bit | 0 m to 15000 m, 0.25 m resolution |
| 6 | acceleration | 8 bit | tbd. |
| 7 to 13 | 2D GNSS | 56 bit | ~ 10 cm resolution |
