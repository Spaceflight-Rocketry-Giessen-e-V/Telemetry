

# File i2c\_connectivity.cpp



[**FileList**](files.md) **>** [**firmware**](dir_ad9f2de7f5f8c5340cd53f6a1e630f0d.md) **>** [**src**](dir_467a32ee08e77420135f1d1bd8b16993.md) **>** [**i2c\_connectivity.cpp**](i2c__connectivity_8cpp.md)

[Go to the source code of this file](i2c__connectivity_8cpp_source.md)



* `#include "i2c_connectivity.h"`





































## Public Functions

| Type | Name |
| ---: | :--- |
|  void | [**subsystemsConnCheck**](#function-subsystemsconncheck) ([**Subsystem**](classSubsystem.md) \*\* subsystemsList, uint8\_t subsystemsCount) <br>_Function to check if a system is connected._  |
|  void | [**subsystemsDataGet**](#function-subsystemsdataget) ([**Subsystem**](classSubsystem.md) \*\* subsystemsList, uint8\_t subsystemsCount) <br>_Function to request data from the Subsystems._  |
|  void | [**subsystemsLedUpdate**](#function-subsystemsledupdate) ([**Subsystem**](classSubsystem.md) \*\* subsystemsList, uint8\_t subsystemsCount, uint8\_t lowPowerMode) <br>_Function to update the sub systems LEDs._  |




























## Public Functions Documentation




### function subsystemsConnCheck 

_Function to check if a system is connected._ 
```C++
void subsystemsConnCheck (
    Subsystem ** subsystemsList,
    uint8_t subsystemsCount
) 
```





**Parameters:**


* `subsystemsList` 
* `subsystemsCount` 




        

<hr>



### function subsystemsDataGet 

_Function to request data from the Subsystems._ 
```C++
void subsystemsDataGet (
    Subsystem ** subsystemsList,
    uint8_t subsystemsCount
) 
```





**Parameters:**


* `subsystemsList` 
* `subsystemsCount` 




        

<hr>



### function subsystemsLedUpdate 

_Function to update the sub systems LEDs._ 
```C++
void subsystemsLedUpdate (
    Subsystem ** subsystemsList,
    uint8_t subsystemsCount,
    uint8_t lowPowerMode
) 
```





**Parameters:**


* `subsystemsList` 
* `subsystemsCount` 
* `lowPowerMode` 




        

<hr>

------------------------------
The documentation for this class was generated from the following file `onboard/firmware/src/i2c_connectivity.cpp`

