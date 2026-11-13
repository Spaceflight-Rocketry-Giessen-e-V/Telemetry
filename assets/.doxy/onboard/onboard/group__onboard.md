

# Group onboard



[**Modules**](modules.md) **>** [**onboard**](group__onboard.md)



_Functions and data structures used by the onboard firmware._ 
















## Classes

| Type | Name |
| ---: | :--- |
| class | [**dataStruct**](classdataStruct.md) <br>_Class for the telemetry and flight data._  |
| class | [**ledStruct**](classledStruct.md) <br>_Class for all LEDs._  |






















## Public Functions

| Type | Name |
| ---: | :--- |
|  void | [**buzzerSound**](#function-buzzersound) (uint8\_t pinBuzzer) <br>_Function to play a sound when the setup is completed._  |
|  void | [**buzzerSoundError**](#function-buzzersounderror) (uint8\_t pinBuzzer) <br>_Function to play a sound according to a error during setup._  |
|  void | [**commandExecute**](#function-commandexecute) (uint8\_t command, RC17xxHP\_RC232 \* radioModule, [**dataStruct**](classdataStruct.md) \* dataVariables, [**ledStruct**](classledStruct.md) \* pinLed, uint8\_t \* flightMode, [**Subsystem**](classSubsystem.md) \*\* subsystemsList, uint8\_t subsystemsCount, [**Subsystem**](classSubsystem.md) \* subsystemSens, [**Subsystem**](classSubsystem.md) \* subsystemControl, Packet \* flightDataPacket, Packet \* telemetryDataPacket, uint8\_t pinArm, uint8\_t pinSleep) <br>_Changes the values of the loop variables and therefore the state of flight computer._  |
|  void | [**commandReceive**](#function-commandreceive) (RC17xxHP\_RC232 \* radioModule, Packet \* commandPacket) <br>_Returns the latest single-byte command from the uplink module (rc1701hp, on Serial3), or 0 if command is bad/unknown._  |
|  void | [**flashWrite**](#function-flashwrite) ([**dataStruct**](classdataStruct.md) \* dataVariables) <br>_Function to write to the onbaord flash. f._  |
|  void | [**ledUpdate**](#function-ledupdate) (uint8\_t state, [**ledStruct**](classledStruct.md) \* pinLed) <br>_Function to update LEDs to display different states of the system._  |
|  void | [**loopVariablesUpdate**](#function-loopvariablesupdate) (uint32\_t \* loopCount, uint32\_t \* loopStartTime, uint8\_t loopFrequency, uint8\_t pinLedLoop) <br>_Function that update the loop variables._  |
|  void | [**packetSend**](#function-packetsend) (RC17xxHP\_RC232 \* radioModule, uint8\_t packetType, Packet \* flightDataPacket, Packet \* telemetryDataPacket) <br>_Function to build up the package depending on an identifyer._  |
|  uint8\_t | [**packetSendCheck**](#function-packetsendcheck) (uint8\_t \* flightmode, uint8\_t loopFrequency, uint8\_t timeBetweenStandbyPackets, uint32\_t loopCount) <br>_Function that handle the decision of sending a package depending on the timeBetweenStandbyPackets. In addition handles the decision of sending either the telemetry or flight package._  |
|  void | [**radioModulesSetup**](#function-radiomodulessetup) (RC17xxHP\_RC232 \* rc1780hp, RC17xxHP\_RC232 \* rc1701hp, [**ledStruct**](classledStruct.md) \* pinLed, uint8\_t pinBuzzer) <br>_Configures both radio modules; lights each module's status LED on success and sounds buzzzer._  |




























## Public Functions Documentation




### function buzzerSound 

_Function to play a sound when the setup is completed._ 
```cpp
void buzzerSound (
    uint8_t pinBuzzer
) 
```





**Parameters:**


* `pinBuzzer` 




        

<hr>



### function buzzerSoundError 

_Function to play a sound according to a error during setup._ 
```cpp
void buzzerSoundError (
    uint8_t pinBuzzer
) 
```





**Parameters:**


* `pinBuzzer` 




        

<hr>



### function commandExecute 

_Changes the values of the loop variables and therefore the state of flight computer._ 
```cpp
void commandExecute (
    uint8_t command,
    RC17xxHP_RC232 * radioModule,
    dataStruct * dataVariables,
    ledStruct * pinLed,
    uint8_t * flightMode,
    Subsystem ** subsystemsList,
    uint8_t subsystemsCount,
    Subsystem * subsystemSens,
    Subsystem * subsystemControl,
    Packet * flightDataPacket,
    Packet * telemetryDataPacket,
    uint8_t pinArm,
    uint8_t pinSleep
) 
```





**Parameters:**


* `command` 
* `radioModule` 
* `dataVariables` 
* `pinLed` 
* `flightMode` 
* `subsystemsList` 
* `subsystemsCount` 
* `subsystemSens` 
* `subsystemControl` 
* `pinArm` 
* `pinSleep` 




        

<hr>



### function commandReceive 

_Returns the latest single-byte command from the uplink module (rc1701hp, on Serial3), or 0 if command is bad/unknown._ 
```cpp
void commandReceive (
    RC17xxHP_RC232 * radioModule,
    Packet * commandPacket
) 
```





**Parameters:**


* `radioModule` 



**Returns:**

uint8\_t 





        

<hr>



### function flashWrite 

_Function to write to the onbaord flash. f._ 
```cpp
void flashWrite (
    dataStruct * dataVariables
) 
```





**Parameters:**


* `dataVariables` 




        

<hr>



### function ledUpdate 

_Function to update LEDs to display different states of the system._ 
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



### function loopVariablesUpdate 

_Function that update the loop variables._ 
```cpp
void loopVariablesUpdate (
    uint32_t * loopCount,
    uint32_t * loopStartTime,
    uint8_t loopFrequency,
    uint8_t pinLedLoop
) 
```





**Parameters:**


* `loopCount` 
* `loopStartTime` 
* `loopFrequency` 
* `pinLedLoop` 




        

<hr>



### function packetSend 

_Function to build up the package depending on an identifyer._ 
```cpp
void packetSend (
    RC17xxHP_RC232 * radioModule,
    uint8_t packetType,
    Packet * flightDataPacket,
    Packet * telemetryDataPacket
) 
```





**Parameters:**


* `radioModule` 
* `dataVariables` 
* `pinLed` 
* `packetIdentifier` 




        

<hr>



### function packetSendCheck 

_Function that handle the decision of sending a package depending on the timeBetweenStandbyPackets. In addition handles the decision of sending either the telemetry or flight package._ 
```cpp
uint8_t packetSendCheck (
    uint8_t * flightmode,
    uint8_t loopFrequency,
    uint8_t timeBetweenStandbyPackets,
    uint32_t loopCount
) 
```





**Parameters:**


* `flightmode` 
* `loopFrequency` 
* `timeBetweenStandbyPackets` 
* `loopCount` 



**Returns:**

uint8\_t 





        

<hr>



### function radioModulesSetup 

_Configures both radio modules; lights each module's status LED on success and sounds buzzzer._ 
```cpp
void radioModulesSetup (
    RC17xxHP_RC232 * rc1780hp,
    RC17xxHP_RC232 * rc1701hp,
    ledStruct * pinLed,
    uint8_t pinBuzzer
) 
```





**Parameters:**


* `rc1780hp` 
* `rc1701hp` 
* `pinLed` 
* `pinBuzzer` 




        

<hr>

------------------------------


