#include "header.h"

// LEDs states
#define SETUPBEGIN 1
#define SETUPRADIOMODULS 2
#define SETUPEND 3
#define RADIOMODUL_ONE 4
#define RADIOMODUL_TWO 5

class dataStruct;
class ledStruct;
class buttonStruct;

void radioModulesSetup(RC17xxHP_RC232 *rc1780hp, RC17xxHP_RC232 *rc1701hp, ledStruct pinLed);

uint8_t commandReceive(HardwareSerial *serialUSB);

void commandExecute(uint8_t command, RC17xxHP_RC232 *radioModule);

void packetReceive(RC17xxHP_RC232 *radioModule, uint8_t *packetBuffer, uint8_t *packetBufferIndex, dataStruct dataVariables);

void dataSendUsb(HardwareSerial *serialUSB, dataStruct dataVariables);

void ledUpdate(uint8_t state, ledStruct pinLed);

void ledRssiUpdate(float rssi, ledStruct pinLed);

void displayUpdate(uint8_t address, dataStruct dataVariables);

void buttonCheck(buttonStruct pinButton);

void controlBoxCheck(uint8_t pin1, uint8_t pin2);

class dataStruct // :)
{
public:

  float rssi;
  uint32_t timestampLastPacket = 0;

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

class buttonStruct // :)
{
public:
  uint8_t sw1;
  uint8_t sw2;
  uint8_t sw3;
  uint8_t sw4;
  uint8_t sw5;
  uint8_t sw6;

  void pinMode();
};
