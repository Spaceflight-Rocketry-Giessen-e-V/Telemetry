#include "Arduino.h"

void radioModulesSetup(RC17xxHP_RC232 rc1780hp, RC17xxHP_RC232 rc1701hp, ledStruct pinLed, uint8_t pinBuzzer);

void packetReceive(RC17xxHP_RC232 *radioModule, dataStruct dataVariables, uint8_t packetIdentifier);

void loopVariablesUpdate(uint16_t *loopCount, uint32_t *loopStartTime, uint8_t loopFrequency, uint8_t pinLedLoop);

void ledUpdate(uint8_t state, ledStruct &pinLed);

void buttonCheck(buttonStruct &pinButton);

void launchControlCheck(uint8_t pinRX, uint8_t pinTX);

uint8_t commandSend(RC17xxHP_RC232 radioModule, uint8_t command);
class ledStruct
{
public:
  uint8_t R;
  uint8_t G;
  uint8_t B;
  uint8_t D1;
  uint8_t D2;
  uint8_t D3;
  uint8_t rssi_1;
  uint8_t rssi_2;
  uint8_t rssi_3;
  uint8_t rssi_4;
  uint8_t rssi_5;
  uint8_t rssi_6;
  uint8_t rssi_7;
  uint8_t rssi_8;
  void pinMode();
};

class dataStruct // :)
{
public:
  // Subsystem States

  uint8_t statePower;
  uint8_t stateSens;
  uint8_t stateControl;
  uint8_t stateTelemetry;

  // Flight Data

  uint8_t flightEvents;
  float latitude;
  float longitude;
  float heightPressure;
  float acceleration;

  // Telemetry Data

  uint8_t lowPowerMode;
  float heightGNSS;
  uint8_t hdopGNSS;
  uint8_t satCountGNSS;
  uint8_t stateUmbilical;
  float currentUmbilical;
  uint8_t pressureDecoupler;
  uint8_t ldrDecoupler;
  uint8_t continuityPyros;
  float currentBattery;
  float voltageBattery;
  float voltageBatteryCOTS;
  uint8_t temperatureBattery;
  uint8_t temperatureElectronics;
};

class buttonStruct // :)
{
public:
  uint8_t sws1;
  uint8_t sws2;
  uint8_t sws3;
  uint8_t sws4;
  uint8_t sws5;
  uint8_t sws6;
  uint8_t sws7;
  uint8_t sws8;
}
