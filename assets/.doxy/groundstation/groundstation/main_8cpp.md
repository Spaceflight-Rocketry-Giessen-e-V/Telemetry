

# File main.cpp



[**FileList**](files.md) **>** [**firmware**](dir_9593cad69041603fae40c4ffc2ee0f0b.md) **>** [**src**](dir_378fe0f8ac021523c9dbb2c9a3fe9bca.md) **>** [**main.cpp**](main_8cpp.md)

[Go to the source code of this file](main_8cpp_source.md)



* `#include "header.h"`
* `#include "utility.h"`





















## Public Attributes

| Type | Name |
| ---: | :--- |
|  RC17xxHP\_RC232 rc1701hp & | [**Serial1**](#variable-serial1)  <br> |
|  RC17xxHP\_RC232 rc1780hp & | [**Serial4**](#variable-serial4)  <br> |
|  HardwareSerial \* | [**SerialUSB1**](#variable-serialusb1)   = `&Serial5`<br> |
|  HardwareSerial \* | [**SerialUSB2**](#variable-serialusb2)   = `&Serial2`<br> |
|  Packet | [**commandPacket**](#variable-commandpacket)  <br> |
|  [**dataStruct**](classdataStruct.md) | [**dataVars**](#variable-datavars)  <br> |
|  Packet | [**flightDataPacket**](#variable-flightdatapacket)  <br> |
|  Packet | [**framePacket**](#variable-framepacket)  <br> |
|  uint8\_t | [**packetBuffer**](#variable-packetbuffer)  <br> |
|  uint8\_t | [**packetBufferIndex**](#variable-packetbufferindex)   = `0`<br> |
|  [**buttonStruct**](classbuttonStruct.md) | [**pinButton**](#variable-pinbutton)  <br> |
|  uint8\_t | [**pinControlBox1**](#variable-pincontrolbox1)   = `PIN\_PE7`<br> |
|  uint8\_t | [**pinControlBox2**](#variable-pincontrolbox2)   = `PIN\_PE6`<br> |
|  [**ledStruct**](classledStruct.md) | [**pinLed**](#variable-pinled)  <br> |
|  uint8\_t | [**pinRX\_USB1**](#variable-pinrx_usb1)   = `PIN\_PG1`<br> |
|  uint8\_t | [**pinRX\_USB2**](#variable-pinrx_usb2)   = `PIN\_PF1`<br> |
|  uint8\_t | [**pinTX\_USB1**](#variable-pintx_usb1)   = `PIN\_PG0`<br> |
|  uint8\_t | [**pinTX\_USB2**](#variable-pintx_usb2)   = `PIN\_PF0`<br> |
|  Packet | [**telemetryDataPacket**](#variable-telemetrydatapacket)  <br> |
















## Public Functions

| Type | Name |
| ---: | :--- |
|  void | [**loop**](#function-loop) () <br> |
|  void | [**setup**](#function-setup) () <br> |




























## Public Attributes Documentation




### variable Serial1 

```C++
RC17xxHP_RC232 rc1701hp& Serial1;
```




<hr>



### variable Serial4 

```C++
RC17xxHP_RC232 rc1780hp& Serial4;
```




<hr>



### variable SerialUSB1 

```C++
HardwareSerial* SerialUSB1;
```




<hr>



### variable SerialUSB2 

```C++
HardwareSerial* SerialUSB2;
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



### variable framePacket 

```C++
Packet framePacket;
```




<hr>



### variable packetBuffer 

```C++
uint8_t packetBuffer[32];
```




<hr>



### variable packetBufferIndex 

```C++
uint8_t packetBufferIndex;
```




<hr>



### variable pinButton 

```C++
buttonStruct pinButton;
```




<hr>



### variable pinControlBox1 

```C++
uint8_t pinControlBox1;
```




<hr>



### variable pinControlBox2 

```C++
uint8_t pinControlBox2;
```




<hr>



### variable pinLed 

```C++
ledStruct pinLed;
```




<hr>



### variable pinRX\_USB1 

```C++
uint8_t pinRX_USB1;
```




<hr>



### variable pinRX\_USB2 

```C++
uint8_t pinRX_USB2;
```




<hr>



### variable pinTX\_USB1 

```C++
uint8_t pinTX_USB1;
```




<hr>



### variable pinTX\_USB2 

```C++
uint8_t pinTX_USB2;
```




<hr>



### variable telemetryDataPacket 

```C++
Packet telemetryDataPacket;
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
The documentation for this class was generated from the following file `groundstation/firmware/src/main.cpp`

