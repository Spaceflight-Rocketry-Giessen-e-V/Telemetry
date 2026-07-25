#include "header.h"
#include "i2c_connectivity.h"

// LEDs states
#define SETUPBEGIN 1
#define SETUPRADIOMODULS 2
#define SETUPEND 3
#define RADIOMODUL_ONE 4
#define RADIOMODUL_TWO 5

class ledStruct;
class dataStruct;

void buzzerSound(uint8_t pinBuzzer);

void buzzerSoundError(uint8_t pinBuzzer);

void radioModulesSetup(RC17xxHP_RC232 *rc1780hp, RC17xxHP_RC232 *rc1701hp, ledStruct *pinLed, uint8_t pinBuzzer); // Wenn Error: buzzerSoundError();
// ledUpdate aufrufen: ledUpdate(4): radiomodul 1 funktioniert: D2 anschalten,
// ledUpdate(5): radiomodul 2 funktioniert: D3 anschalten

uint8_t commandReceive(RC17xxHP_RC232 *radioModule); // Aufruf Packet Library Function, return 0
                                                     // wenn kein Command, sonst return command

void commandExecute(uint8_t command, RC17xxHP_RC232 *radioModule, dataStruct *dataVariables, uint8_t *lowPowerMode, uint8_t *flightMode, Subsystem **subsystemsList, uint8_t subsystemsCount, Subsystem *subsystemSens, Subsystem *subsystemControl, uint8_t pinArm, uint8_t pinSleep); //  Distribute Data To Subsystems etc..
                                                                                                                                                                                                                                                                                       //  Check for 0 (-> no command)

uint8_t packetSendCheck(uint8_t *flightmode, uint8_t loopFrequency, uint8_t timeBetweenStandbyPackets, uint32_t loopCount);

void packetSend(RC17xxHP_RC232 *radioModule, dataStruct *dataVariables, uint8_t packetIdentifier);

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
  // Subsystem States

  uint8_t stateTelemetry;
  uint8_t statePower;
  uint8_t stateSens;
  uint8_t stateControl;

  // Flight Data

  float acceleration;
  float heightPressure;
  uint8_t flightEvents;
  float latitude;
  float longitude;

  // Telemetry Data

  float heightGNSS;
  uint8_t satCountGNSS;
  float hdopGNSS;
  uint8_t temperatureElectronics;
  uint8_t temperatureBattery;
  uint8_t stateCapacitors;
  uint8_t continuityPyros;
  uint8_t pressureDecoupler;
  uint8_t ldrDecoupler;
  float voltageBattery;
  float currentBattery;
  float currentUmbilical;
  uint8_t stateUmbilical;
  uint8_t lowPowerMode;
  float voltageBatteryCOTS;
};
