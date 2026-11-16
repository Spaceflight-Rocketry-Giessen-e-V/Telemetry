

# File utility.h

[**File List**](files.md) **>** [**firmware**](dir_ad9f2de7f5f8c5340cd53f6a1e630f0d.md) **>** [**include**](dir_a732e032cd315c441c4d5e82e1db6a92.md) **>** [**utility.h**](utility_8h.md)

[Go to the documentation of this file](utility_8h.md)


```C++
#include "header.h"
#include "i2c_connectivity.h"

// LEDs states
#define SETUPBEGIN 1
#define SETUPRADIOMODULS 2
#define SETUPEND 3
#define RADIOMODUL_ONE 4
#define RADIOMODUL_TWO 5
#define UPDATE 255

class ledStruct;
class dataStruct;

void buzzerSound(uint8_t pinBuzzer);

void buzzerSoundError(uint8_t pinBuzzer);

void radioModulesSetup(RC17xxHP_RC232 *rc1780hp, RC17xxHP_RC232 *rc1701hp, ledStruct *pinLed, uint8_t pinBuzzer); // Wenn Error: buzzerSoundError();
// ledUpdate aufrufen: ledUpdate(4): radiomodul 1 funktioniert: D2 anschalten,
// ledUpdate(5): radiomodul 2 funktioniert: D3 anschalten

void commandReceive(RC17xxHP_RC232 *radioModule, Packet *commandPacket); // Aufruf Packet Library Function, return 0
                                                     // wenn kein Command, sonst return command

void commandExecute(uint8_t command, RC17xxHP_RC232 *radioModule, dataStruct *dataVariables, ledStruct *pinLed, uint8_t *flightMode, Subsystem **subsystemsList, uint8_t subsystemsCount, Subsystem *subsystemSens, Subsystem *subsystemControl, Packet *flightDataPacket, Packet *telemetryDataPacket, uint8_t pinArm, uint8_t pinSleep); //  Distribute Data To Subsystems etc..
                                                                                                                                                                                                                                                                                    //  Check for 0 (-> no command)

uint8_t packetSendCheck(uint8_t *flightmode, uint8_t loopFrequency, uint8_t timeBetweenStandbyPackets, uint32_t loopCount);

void packetSend(RC17xxHP_RC232 *radioModule, uint8_t packetType, Packet *flightDataPacket, Packet *telemetryDataPacket);

void flashWrite(dataStruct *dataVariables);

void loopVariablesUpdate(uint32_t *loopCount, uint32_t *loopStartTime, uint8_t loopFrequency, uint8_t pinLedLoop);

void ledUpdate(uint8_t state, ledStruct *pinLed); // Switch Case

class ledStruct
{
public:
  uint8_t R;
  uint8_t G;
  uint8_t B;
  uint8_t D1;
  uint8_t D2;
  uint8_t D3;
  uint8_t Debug1;
  uint8_t Debug2;
  uint8_t Power;
  uint8_t Sens;
  uint8_t Control;
  uint8_t *lowPowerMode;
  void pinMode();
};

class dataStruct // :)
{
public:

  uint8_t command = 0;

  // Subsystem States

  uint8_t stateTelemetry = 0;
  uint8_t statePower = 0;
  uint8_t stateSens = 0;
  uint8_t stateControl = 0;

  // Flight Data

  float acceleration = 0;
  float heightPressure = 0;
  uint8_t flightEvents = 0;
  float latitude = 0;
  float longitude = 0;

  // Telemetry Data

  float heightGNSS = 0;
  uint8_t satCountGNSS = 0;
  float hdopGNSS = 0;
  uint8_t temperatureElectronics = 0;
  uint8_t temperatureBattery = 0;
  uint8_t stateCapacitors = 0;
  uint8_t continuityPyros = 0;
  uint8_t pressureDecoupler = 0;
  uint8_t ldrDecoupler = 0;
  float voltageBattery = 0;
  float currentBattery = 0;
  float currentUmbilical = 0;
  uint8_t stateUmbilical = 0;
  float voltageBatteryCOTS = 0;
};
```


