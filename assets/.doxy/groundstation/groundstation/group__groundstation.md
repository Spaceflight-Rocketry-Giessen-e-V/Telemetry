

# Group groundstation



[**Modules**](modules.md) **>** [**groundstation**](group__groundstation.md)



_Functions and data structures used by the ground-station firmware._ 
















## Classes

| Type | Name |
| ---: | :--- |
| class | [**buttonStruct**](classbuttonStruct.md) <br>_Stores the pins for the control buttons._  |
| class | [**dataStruct**](classdataStruct.md) <br>_Stores the latest housekeeping, subsystem, flight, and telemetry data._  |
| class | [**ledStruct**](classledStruct.md) <br>_Stores the debug and LED pins for._  |






















## Public Functions

| Type | Name |
| ---: | :--- |
|  void | [**buttonCheck**](#function-buttoncheck) ([**buttonStruct**](classbuttonStruct.md) pinButton) <br>_Function to use buttons as an._  |
|  void | [**commandExecute**](#function-commandexecute) (RC17xxHP\_RC232 \* radioModule, uint8\_t command, Packet \* commandPacket) <br>_Function to send the received command via USB._  |
|  uint8\_t | [**commandReceive**](#function-commandreceive) (HardwareSerial \* serialUSB) <br>_Function that reads teh USB serial input._  |
|  void | [**controlBoxCheck**](#function-controlboxcheck) (uint8\_t pin1, uint8\_t pin2) <br>_Function to connect to the control box._  |
|  void | [**dataSendUsb**](#function-datasendusb) (HardwareSerial \* serialUSB, [**dataStruct**](classdataStruct.md) \* dataVariables) <br>_Serial output function via USB._  |
|  void | [**displayUpdate**](#function-displayupdate) (uint8\_t address, [**dataStruct**](classdataStruct.md) \* dataVariables) <br>_Function to display Vlaues on a external Display._  |
|  void | [**ledRssiUpdate**](#function-ledrssiupdate) (float rssi, [**ledStruct**](classledStruct.md) \* pinLed) <br>_Function to display the rssi level via a LED array._  |
|  void | [**ledUpdate**](#function-ledupdate) (uint8\_t state, [**ledStruct**](classledStruct.md) \* pinLed) <br> |
|  uint8\_t | [**packetReceive**](#function-packetreceive) (RC17xxHP\_RC232 \* radioModule, uint8\_t \* packetBuffer, uint8\_t \* packetBufferIndex, [**dataStruct**](classdataStruct.md) \* dataVariables, Packet \* framePacket, Packet \* flightDataPacket, Packet \* telemetryDataPacket) <br>_Function that reads the received data from the Rocket and updates the data variables._  |
|  void | [**radioModulesSetup**](#function-radiomodulessetup) (RC17xxHP\_RC232 \* rc1780hp, RC17xxHP\_RC232 \* rc1701hp, [**ledStruct**](classledStruct.md) \* pinLed) <br>_Configures both radio modules; lights each module's status LED on success and sounds buzzzer._  |




























## Public Functions Documentation




### function buttonCheck 

_Function to use buttons as an._ 
```cpp
void buttonCheck (
    buttonStruct pinButton
) 
```





**Parameters:**


* `pinButton` 



**Todo**

Has to be implemented in the future.




        

<hr>



### function commandExecute 

_Function to send the received command via USB._ 
```cpp
void commandExecute (
    RC17xxHP_RC232 * radioModule,
    uint8_t command,
    Packet * commandPacket
) 
```





**Parameters:**


* `command` 
* `radioModule` 




        

<hr>



### function commandReceive 

_Function that reads teh USB serial input._ 
```cpp
uint8_t commandReceive (
    HardwareSerial * serialUSB
) 
```





**Parameters:**


* `serialUSB` 



**Returns:**

uint8\_t 





        

<hr>



### function controlBoxCheck 

_Function to connect to the control box._ 
```cpp
void controlBoxCheck (
    uint8_t pin1,
    uint8_t pin2
) 
```





**Parameters:**


* `pin1` 
* `pin2` 



**Todo**

Has to be implemented in the future.




        

<hr>



### function dataSendUsb 

_Serial output function via USB._ 
```cpp
void dataSendUsb (
    HardwareSerial * serialUSB,
    dataStruct * dataVariables
) 
```





**Parameters:**


* `serialUSB` 
* `dataVariables` 




        

<hr>



### function displayUpdate 

_Function to display Vlaues on a external Display._ 
```cpp
void displayUpdate (
    uint8_t address,
    dataStruct * dataVariables
) 
```





**Parameters:**


* `address` 
* `dataVariables` 



**Todo**

Has to be implemented in the future.




        

<hr>



### function ledRssiUpdate 

_Function to display the rssi level via a LED array._ 
```cpp
void ledRssiUpdate (
    float rssi,
    ledStruct * pinLed
) 
```





**Parameters:**


* `rssi` 
* `pinLed` 




        

<hr>



### function ledUpdate 

```cpp
void ledUpdate (
    uint8_t state,
    ledStruct * pinLed
) 
```





**Parameters:**


* `state` 
* `pinLed` 




        

<hr>



### function packetReceive 

_Function that reads the received data from the Rocket and updates the data variables._ 
```cpp
uint8_t packetReceive (
    RC17xxHP_RC232 * radioModule,
    uint8_t * packetBuffer,
    uint8_t * packetBufferIndex,
    dataStruct * dataVariables,
    Packet * framePacket,
    Packet * flightDataPacket,
    Packet * telemetryDataPacket
) 
```





**Parameters:**


* `radioModule` 
* `packetBuffer` 
* `packetBufferIndex` 
* `dataVariables` 



**Returns:**

uint8\_t 





        

<hr>



### function radioModulesSetup 

_Configures both radio modules; lights each module's status LED on success and sounds buzzzer._ 
```cpp
void radioModulesSetup (
    RC17xxHP_RC232 * rc1780hp,
    RC17xxHP_RC232 * rc1701hp,
    ledStruct * pinLed
) 
```





**Parameters:**


* `rc1780hp` 
* `rc1701hp` 
* `pinLed` 




        

<hr>

------------------------------


