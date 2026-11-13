

# File i2c\_connectivity.h



[**FileList**](files.md) **>** [**firmware**](dir_ad9f2de7f5f8c5340cd53f6a1e630f0d.md) **>** [**include**](dir_a732e032cd315c441c4d5e82e1db6a92.md) **>** [**i2c\_connectivity.h**](i2c__connectivity_8h.md)

[Go to the source code of this file](i2c__connectivity_8h_source.md)



* `#include "header.h"`















## Classes

| Type | Name |
| ---: | :--- |
| class | [**Subsystem**](classSubsystem.md) <br>_Class to dynamically initialise different subsystems._  |






















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
The documentation for this class was generated from the following file `onboard/firmware/include/i2c_connectivity.h`

