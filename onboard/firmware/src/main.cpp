/*
    onboard - main.cpp of the board computer for the ASCENT III telemetry system.
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Arduino.h"
#include "Wire.h"
#include "Radiocrafts_RC17xxHP_RC232.h"
#include "Packet.h"
#include "i2c_connectivity.h"
#include "utility.h"

int main(void)
{
  init();

  // LED Pins Initialization

  ledStruct pinLed;

  pinLed.R = PIN_PF0;
  pinLed.G = PIN_PE7;
  pinLed.B = PIN_PE6;
  pinLed.D1 = PIN_PF3;
  pinLed.D2 = PIN_PF2;
  pinLed.D3 = PIN_PF1;
  pinLed.Debug1 = PIN_PB6;
  pinLed.Debug2 = PIN_PB7;
  pinLed.Power = PIN_PD3;
  pinLed.Sens = PIN_PD4;
  pinLed.Control = PIN_PD2;

  pinLed.pinMode();

  ledUpdate(SETUPBEGIN, pinLed); // R On

  // Pin Declarations

  uint8_t pinCFG_1780 = PIN_PA5;
  uint8_t pinRST_1780 = PIN_PG7;
  uint8_t pinCTS_1780 = PIN_PA3;
  uint8_t pinRTS_1780 = PIN_PA4;
  uint8_t pinCFG_1701 = PIN_PB3;
  uint8_t pinRST_1701 = PIN_PG6;
  uint8_t pinCTS_1701 = PIN_PB1;
  uint8_t pinRTS_1701 = PIN_PB2;
  uint8_t pinSLP = PIN_PG0;
  uint8_t pinARM1 = PIN_PG1;
  uint8_t pinD26 = PIN_PF4;
  uint8_t pinD27 = PIN_PF5;
  uint8_t pinD28 = PIN_PF6;
  uint8_t pinD4 = PIN_PC6;
  uint8_t pinD5 = PIN_PC7;
  uint8_t pinBuzzer = PIN_PB0;

  // Pin Initialisations

  pinMode(pinCFG_1780, OUTPUT);
  pinMode(pinRST_1780, OUTPUT);
  pinMode(pinCTS_1780, OUTPUT);
  pinMode(pinRTS_1780, OUTPUT);
  pinMode(pinCFG_1701, OUTPUT);
  pinMode(pinRST_1701, OUTPUT);
  pinMode(pinCTS_1701, OUTPUT);
  pinMode(pinRTS_1701, OUTPUT);
  pinMode(pinSLP, OUTPUT);
  pinMode(pinARM1, OUTPUT);
  pinMode(pinBuzzer, OUTPUT);

  digitalWrite(pinCFG_1780, HIGH);
  digitalWrite(pinRST_1780, HIGH);
  digitalWrite(pinCTS_1780, HIGH);
  digitalWrite(pinRTS_1780, HIGH);
  digitalWrite(pinCFG_1701, HIGH);
  digitalWrite(pinRST_1701, HIGH);
  digitalWrite(pinCTS_1701, HIGH);
  digitalWrite(pinRTS_1701, HIGH);
  digitalWrite(pinSLP, LOW);
  digitalWrite(pinARM1, LOW);

  // UART Declarations

  HardwareSerial *SerialUSB = &Serial4;
  HardwareSerial *SerialUmbilical = &Serial1;

  uint8_t pinTX_USB = PIN_PE4;
  uint8_t pinRX_USB = PIN_PE5;
  uint8_t pinTX_Umbilical = PIN_PC0;
  uint8_t pinRX_Umbilical = PIN_PC1;

  SerialUSB->pins(pinTX_USB, pinRX_USB);
  SerialUmbilical->pins(pinTX_Umbilical, pinRX_Umbilical);

  SerialUSB->begin(115200);
  SerialUmbilical->begin(115200);

  uint8_t pinTX_1780 = PIN_PA0;
  uint8_t pinRX_1780 = PIN_PA1;
  uint8_t pinTX_1701 = PIN_PB4;
  uint8_t pinRX_1701 = PIN_PB5;

  // Initialize I2C

  Wire.pins(PIN_PC2, PIN_PC3);
  Wire.begin();

  // Initialize Radio Modules

  RC17xxHP_RC232 rc1780hp(&Serial0, pinTX_1780, pinRX_1780, pinCFG_1780, pinRST_1780, pinCTS_1780, pinRTS_1780);
  RC17xxHP_RC232 rc1701hp(&Serial3, pinTX_1701, pinRX_1701, pinCFG_1701, pinRST_1780, pinCTS_1701, pinRTS_1701);

  radioModulesSetup(rc1780hp, rc1701hp, pinLed, pinBuzzer);

  ledUpdate(2, pinLed); // B On

  dataStruct dataVariables;

  // Data Arrays Preparations

  const uint8_t uint8CountPower = 0;
  uint8_t *uint8ListPower[uint8CountPower] = {};
  const uint8_t floatCountPower = 0;
  float *floatListPower[floatCountPower] = {};

  const uint8_t uint8CountSens = 0;
  uint8_t *uint8ListSens[uint8CountSens] = {};
  const uint8_t floatCountSens = 0;
  float *floatListSens[floatCountSens] = {};

  const uint8_t uint8CountControl = 0;
  uint8_t *uint8ListControl[uint8CountControl] = {};
  const uint8_t floatCountControl = 0;
  float *floatListControl[floatCountControl] = {};

  // Subsystems Initialization

  Subsystem subsystemPower(0x50, pinLed.Power, &dataVariables.statePower, uint8ListPower, uint8CountPower, floatListPower, floatCountPower);
  Subsystem subsystemSens(0x20, pinLed.Sens, &dataVariables.stateSens, uint8ListSens, uint8CountSens, floatListSens, floatCountSens);
  Subsystem subsystemControl(0x40, pinLed.Control, &dataVariables.stateControl, uint8ListControl, uint8CountControl, floatListControl, floatCountControl);

  const uint8_t subsystemsCount = 3;
  Subsystem *subsystemList[subsystemsCount] = {&subsystemSens, &subsystemPower, &subsystemControl};

  // Setup Complete

  buzzerSound(pinBuzzer);

  ledUpdate(3, pinLed); // G On

  const uint8_t loopFrequency = 10;             // in Hz       10 Hz = 100 ms interval
  const uint8_t timeBetweenStandbyPackets = 15; // in seconds. In standby, data packets aren't send every loop

  uint8_t flightmode = 0;
  uint16_t loopCount = 0;
  uint32_t loopStartTime = 0;

  while (true)
  {
    subsystemsConnCheck(subsystemList, subsystemsCount);

    subsystemsDataGet(subsystemList, subsystemsCount);

    subsystemsLedUpdate(subsystemList, subsystemsCount);

    uint8_t command = commandReceive(rc1701hp);
    commandExecute(command);

    uint8_t packetIdentifier = packetSendCheck(&flightmode, loopFrequency, timeBetweenStandbyPackets, loopCount);
    packetSend(&rc1780hp, dataVariables, packetIdentifier);

    flashWrite(dataVariables);

    loopVariablesUpdate(&loopCount, &loopStartTime, loopFrequency, pinLed.D1);
  }

  return 0;
}
