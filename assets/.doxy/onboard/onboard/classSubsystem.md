

# Class Subsystem



[**ClassList**](annotated.md) **>** [**Subsystem**](classSubsystem.md)



_Class to dynamically initialise different subsystems._ 

* `#include <i2c_connectivity.h>`





































## Public Functions

| Type | Name |
| ---: | :--- |
|   | [**Subsystem**](#function-subsystem) (uint8\_t i2cAddress, uint8\_t \* pinLed, uint8\_t \* subsystemStatus, uint8\_t \*\* uint8List, uint8\_t uint8Count, float \*\* floatList, uint8\_t floatCount) <br> |
|  void | [**connectionCheck**](#function-connectioncheck) () <br> |
|  void | [**dataGet**](#function-dataget) () <br> |
|  void | [**ledUpdate**](#function-ledupdate) (uint8\_t lowPowerMode) <br> |
|  uint8\_t | [**statusGet**](#function-statusget) () <br> |
|  void | [**write**](#function-write) (uint8\_t byte) <br> |




























## Public Functions Documentation




### function Subsystem 

```C++
Subsystem::Subsystem (
    uint8_t i2cAddress,
    uint8_t * pinLed,
    uint8_t * subsystemStatus,
    uint8_t ** uint8List,
    uint8_t uint8Count,
    float ** floatList,
    uint8_t floatCount
) 
```




<hr>



### function connectionCheck 

```C++
void Subsystem::connectionCheck () 
```




<hr>



### function dataGet 

```C++
void Subsystem::dataGet () 
```




<hr>



### function ledUpdate 

```C++
void Subsystem::ledUpdate (
    uint8_t lowPowerMode
) 
```




<hr>



### function statusGet 

```C++
uint8_t Subsystem::statusGet () 
```




<hr>



### function write 

```C++
void Subsystem::write (
    uint8_t byte
) 
```




<hr>

------------------------------
The documentation for this class was generated from the following file `onboard/firmware/include/i2c_connectivity.h`

