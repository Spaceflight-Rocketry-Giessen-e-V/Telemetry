

# File main.cpp



[**FileList**](files.md) **>** [**firmware**](dir_ad9f2de7f5f8c5340cd53f6a1e630f0d.md) **>** [**src**](dir_467a32ee08e77420135f1d1bd8b16993.md) **>** [**main.cpp**](main_8cpp.md)

[Go to the source code of this file](main_8cpp_source.md)



* `#include "header.h"`
* `#include "utility.h"`





















## Public Attributes

| Type | Name |
| ---: | :--- |
|  RC17xxHP\_RC232 rc1780hp & | [**Serial0**](#variable-serial0)  <br> |
|  RC17xxHP\_RC232 rc1701hp & | [**Serial3**](#variable-serial3)  <br> |
|  HardwareSerial \* | [**SerialUSB**](#variable-serialusb)   = `&Serial4`<br> |
|  HardwareSerial \* | [**SerialUmbilical**](#variable-serialumbilical)   = `&Serial1`<br> |
|  Packet | [**commandPacket**](#variable-commandpacket)  <br> |
|  [**dataStruct**](classdataStruct.md) | [**dataVars**](#variable-datavars)  <br> |
|  Packet | [**flightDataPacket**](#variable-flightdatapacket)  <br> |
|  uint8\_t | [**flightMode**](#variable-flightmode)   = `0`<br> |
|  const uint8\_t | [**floatCountControl**](#variable-floatcountcontrol)   = `0`<br> |
|  const uint8\_t | [**floatCountPower**](#variable-floatcountpower)   = `4`<br> |
|  const uint8\_t | [**floatCountSens**](#variable-floatcountsens)   = `6`<br> |
|  float \* | [**floatListControl**](#variable-floatlistcontrol)   = `{}`<br> |
|  float \* | [**floatListPower**](#variable-floatlistpower)   = `{&dataVars.currentUmbilical, &dataVars.currentBattery, &dataVars.voltageBattery, &dataVars.voltageBatteryCOTS}`<br> |
|  float \* | [**floatListSens**](#variable-floatlistsens)   = `{&dataVars.latitude, &dataVars.longitude, &dataVars.heightPressure, &dataVars.acceleration, &dataVars.heightGNSS, &dataVars.hdopGNSS}`<br> |
|  uint32\_t | [**loopCount**](#variable-loopcount)   = `0`<br> |
|  const uint8\_t | [**loopFrequency**](#variable-loopfrequency)   = `10`<br> |
|  uint32\_t | [**loopStartTime**](#variable-loopstarttime)   = `0`<br> |
|  uint8\_t | [**pinARM1**](#variable-pinarm1)   = `PIN\_PG1`<br> |
|  uint8\_t | [**pinBuzzer**](#variable-pinbuzzer)   = `PIN\_PB0`<br> |
|  uint8\_t | [**pinD26**](#variable-pind26)   = `PIN\_PF4`<br> |
|  uint8\_t | [**pinD27**](#variable-pind27)   = `PIN\_PF5`<br> |
|  uint8\_t | [**pinD28**](#variable-pind28)   = `PIN\_PF6`<br> |
|  uint8\_t | [**pinD4**](#variable-pind4)   = `PIN\_PC6`<br> |
|  uint8\_t | [**pinD5**](#variable-pind5)   = `PIN\_PC7`<br> |
|  [**ledStruct**](classledStruct.md) | [**pinLed**](#variable-pinled)  <br> |
|  uint8\_t | [**pinRX\_USB**](#variable-pinrx_usb)   = `PIN\_PE5`<br> |
|  uint8\_t | [**pinRX\_Umbilical**](#variable-pinrx_umbilical)   = `PIN\_PC1`<br> |
|  uint8\_t | [**pinSLP**](#variable-pinslp)   = `PIN\_PG0`<br> |
|  uint8\_t | [**pinTX\_USB**](#variable-pintx_usb)   = `PIN\_PE4`<br> |
|  uint8\_t | [**pinTX\_Umbilical**](#variable-pintx_umbilical)   = `PIN\_PC0`<br> |
|  [**Subsystem**](classSubsystem.md) | [**subsystemControl**](#variable-subsystemcontrol)  <br> |
|  [**Subsystem**](classSubsystem.md) \* | [**subsystemList**](#variable-subsystemlist)   = `{&[**subsystemSens**](main_8cpp.md#variable-subsystemsens), &[**subsystemPower**](main_8cpp.md#variable-subsystempower), &[**subsystemControl**](main_8cpp.md#variable-subsystemcontrol)}`<br> |
|  [**Subsystem**](classSubsystem.md) | [**subsystemPower**](#variable-subsystempower)  <br> |
|  [**Subsystem**](classSubsystem.md) | [**subsystemSens**](#variable-subsystemsens)  <br> |
|  const uint8\_t | [**subsystemsCount**](#variable-subsystemscount)   = `3`<br> |
|  Packet | [**telemetryDataPacket**](#variable-telemetrydatapacket)  <br> |
|  const uint8\_t | [**timeBetweenStandbyPackets**](#variable-timebetweenstandbypackets)   = `5`<br> |
|  const uint8\_t | [**uint8CountControl**](#variable-uint8countcontrol)   = `6`<br> |
|  const uint8\_t | [**uint8CountPower**](#variable-uint8countpower)   = `3`<br> |
|  const uint8\_t | [**uint8CountSens**](#variable-uint8countsens)   = `3`<br> |
|  uint8\_t \* | [**uint8ListControl**](#variable-uint8listcontrol)   = `{&dataVars.stateControl, &dataVars.flightEvents, &dataVars.stateCapacitors, &dataVars.pressureDecoupler, &dataVars.ldrDecoupler, &dataVars.continuityPyros}`<br> |
|  uint8\_t \* | [**uint8ListPower**](#variable-uint8listpower)   = `{&dataVars.statePower, &dataVars.stateUmbilical, &dataVars.temperatureBattery}`<br> |
|  uint8\_t \* | [**uint8ListSens**](#variable-uint8listsens)   = `{&dataVars.stateSens, &dataVars.satCountGNSS, &dataVars.temperatureElectronics}`<br> |
















## Public Functions

| Type | Name |
| ---: | :--- |
|  void | [**loop**](#function-loop) () <br> |
|  void | [**setup**](#function-setup) () <br> |




























## Public Attributes Documentation




### variable Serial0 

```C++
RC17xxHP_RC232 rc1780hp& Serial0;
```




<hr>



### variable Serial3 

```C++
RC17xxHP_RC232 rc1701hp& Serial3;
```




<hr>



### variable SerialUSB 

```C++
HardwareSerial* SerialUSB;
```




<hr>



### variable SerialUmbilical 

```C++
HardwareSerial* SerialUmbilical;
```




<hr>



### variable commandPacket 

```C++
Packet commandPacket;
```




<hr>



### variable dataVars 

```C++
dataStruct dataVars;
```




<hr>



### variable flightDataPacket 

```C++
Packet flightDataPacket;
```




<hr>



### variable flightMode 

```C++
uint8_t flightMode;
```




<hr>



### variable floatCountControl 

```C++
const uint8_t floatCountControl;
```




<hr>



### variable floatCountPower 

```C++
const uint8_t floatCountPower;
```




<hr>



### variable floatCountSens 

```C++
const uint8_t floatCountSens;
```




<hr>



### variable floatListControl 

```C++
float* floatListControl[floatCountControl];
```




<hr>



### variable floatListPower 

```C++
float* floatListPower[floatCountPower];
```




<hr>



### variable floatListSens 

```C++
float* floatListSens[floatCountSens];
```




<hr>



### variable loopCount 

```C++
uint32_t loopCount;
```




<hr>



### variable loopFrequency 

```C++
const uint8_t loopFrequency;
```




<hr>



### variable loopStartTime 

```C++
uint32_t loopStartTime;
```




<hr>



### variable pinARM1 

```C++
uint8_t pinARM1;
```




<hr>



### variable pinBuzzer 

```C++
uint8_t pinBuzzer;
```




<hr>



### variable pinD26 

```C++
uint8_t pinD26;
```




<hr>



### variable pinD27 

```C++
uint8_t pinD27;
```




<hr>



### variable pinD28 

```C++
uint8_t pinD28;
```




<hr>



### variable pinD4 

```C++
uint8_t pinD4;
```




<hr>



### variable pinD5 

```C++
uint8_t pinD5;
```




<hr>



### variable pinLed 

```C++
ledStruct pinLed;
```




<hr>



### variable pinRX\_USB 

```C++
uint8_t pinRX_USB;
```




<hr>



### variable pinRX\_Umbilical 

```C++
uint8_t pinRX_Umbilical;
```




<hr>



### variable pinSLP 

```C++
uint8_t pinSLP;
```




<hr>



### variable pinTX\_USB 

```C++
uint8_t pinTX_USB;
```




<hr>



### variable pinTX\_Umbilical 

```C++
uint8_t pinTX_Umbilical;
```




<hr>



### variable subsystemControl 

```C++
Subsystem subsystemControl(0x40, &pinLed.Control, &dataVars.stateControl, uint8ListControl, uint8CountControl, floatListControl, floatCountControl);
```




<hr>



### variable subsystemList 

```C++
Subsystem* subsystemList[subsystemsCount];
```




<hr>



### variable subsystemPower 

```C++
Subsystem subsystemPower(0x50, &pinLed.Power, &dataVars.statePower, uint8ListPower, uint8CountPower, floatListPower, floatCountPower);
```




<hr>



### variable subsystemSens 

```C++
Subsystem subsystemSens(0x20, &pinLed.Sens, &dataVars.stateSens, uint8ListSens, uint8CountSens, floatListSens, floatCountSens);
```




<hr>



### variable subsystemsCount 

```C++
const uint8_t subsystemsCount;
```




<hr>



### variable telemetryDataPacket 

```C++
Packet telemetryDataPacket;
```




<hr>



### variable timeBetweenStandbyPackets 

```C++
const uint8_t timeBetweenStandbyPackets;
```




<hr>



### variable uint8CountControl 

```C++
const uint8_t uint8CountControl;
```




<hr>



### variable uint8CountPower 

```C++
const uint8_t uint8CountPower;
```




<hr>



### variable uint8CountSens 

```C++
const uint8_t uint8CountSens;
```




<hr>



### variable uint8ListControl 

```C++
uint8_t* uint8ListControl[uint8CountControl];
```




<hr>



### variable uint8ListPower 

```C++
uint8_t* uint8ListPower[uint8CountPower];
```




<hr>



### variable uint8ListSens 

```C++
uint8_t* uint8ListSens[uint8CountSens];
```




<hr>
## Public Functions Documentation




### function loop 

```C++
void loop () 
```




<hr>



### function setup 

```C++
void setup () 
```




<hr>

------------------------------
The documentation for this class was generated from the following file `onboard/firmware/src/main.cpp`

