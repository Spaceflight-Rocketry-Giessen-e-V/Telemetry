/*
    onboard - main.cpp of the board computer for the ASCENT III telemetry system.
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "header.h"
#include "utility.h"

// LED Pins Initialization

ledStruct pinLed;

// Pin Declarations

uint8_t pinSLP = PIN_PG0;
uint8_t pinARM1 = PIN_PG1;
uint8_t pinD26 = PIN_PF4;
uint8_t pinD27 = PIN_PF5;
uint8_t pinD28 = PIN_PF6;
uint8_t pinD4 = PIN_PC6;
uint8_t pinD5 = PIN_PC7;
uint8_t pinBuzzer = PIN_PB0;

// UART Declarations

HardwareSerial *SerialUSB = &Serial4;
HardwareSerial *SerialUmbilical = &Serial1;

uint8_t pinTX_USB = PIN_PE4;
uint8_t pinRX_USB = PIN_PE5;
uint8_t pinTX_Umbilical = PIN_PC0;
uint8_t pinRX_Umbilical = PIN_PC1;

// Initialize Radio Modules

RC17xxHP_RC232 rc1780hp(&Serial0, PIN_PA0, PIN_PA1, 19200, PIN_PA5, PIN_PG7, PIN_PA3, PIN_PA4);
RC17xxHP_RC232 rc1701hp(&Serial3, PIN_PB4, PIN_PB5, 19200, PIN_PB3, PIN_PG6, PIN_PB1, PIN_PB2);
dataStruct dataVars;

// Data Arrays Preparations

const uint8_t uint8CountPower = 3;
uint8_t *uint8ListPower[uint8CountPower] = {&dataVars.statePower, &dataVars.stateUmbilical, &dataVars.temperatureBattery};
const uint8_t floatCountPower = 4;
float *floatListPower[floatCountPower] = {&dataVars.currentUmbilical, &dataVars.currentBattery, &dataVars.voltageBattery, &dataVars.voltageBatteryCOTS};

const uint8_t uint8CountSens = 3;
uint8_t *uint8ListSens[uint8CountSens] = {&dataVars.stateSens, &dataVars.satCountGNSS, &dataVars.temperatureElectronics};
const uint8_t floatCountSens = 6;
float *floatListSens[floatCountSens] = {&dataVars.latitude, &dataVars.longitude, &dataVars.heightPressure, &dataVars.acceleration, &dataVars.heightGNSS, &dataVars.hdopGNSS};

const uint8_t uint8CountControl = 6;
uint8_t *uint8ListControl[uint8CountControl] = {&dataVars.stateControl, &dataVars.flightEvents, &dataVars.stateCapacitors, &dataVars.pressureDecoupler, &dataVars.ldrDecoupler, &dataVars.continuityPyros};
const uint8_t floatCountControl = 0;
float *floatListControl[floatCountControl] = {};

// Subsystems Initialization

Subsystem subsystemPower(0x50, &pinLed.Power, &dataVars.statePower, uint8ListPower, uint8CountPower, floatListPower, floatCountPower);
Subsystem subsystemSens(0x20, &pinLed.Sens, &dataVars.stateSens, uint8ListSens, uint8CountSens, floatListSens, floatCountSens);
Subsystem subsystemControl(0x40, &pinLed.Control, &dataVars.stateControl, uint8ListControl, uint8CountControl, floatListControl, floatCountControl);

const uint8_t subsystemsCount = 3;
Subsystem *subsystemList[subsystemsCount] = {&subsystemSens, &subsystemPower, &subsystemControl};

const uint8_t loopFrequency = 10;            // in Hz       10 Hz = 100 ms interval
const uint8_t timeBetweenStandbyPackets = 5; // in seconds. In standby, data packets aren't send every loop

uint8_t flightMode = 0;
uint32_t loopCount = 0;
uint32_t loopStartTime = 0;

void setup()
{
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

  pinLed.lowPowerMode = new uint8_t(0);

  pinLed.pinMode();

  ledUpdate(SETUPBEGIN, &pinLed); // R On

  // Pin Initialisations

  pinMode(pinSLP, OUTPUT);
  pinMode(pinARM1, OUTPUT);
  pinMode(pinBuzzer, OUTPUT);

  digitalWrite(pinSLP, LOW);
  digitalWrite(pinARM1, LOW);

  // UART Declarations

  SerialUSB->pins(pinTX_USB, pinRX_USB);
  SerialUmbilical->pins(pinTX_Umbilical, pinRX_Umbilical);

  SerialUSB->begin(115200);
  SerialUmbilical->begin(115200);

  // Initialize I2C

  Wire.pins(PIN_PC2, PIN_PC3);
  Wire.begin();

  // Initialize Radio Modules

  radioModulesSetup(&rc1780hp, &rc1701hp, &pinLed, pinBuzzer);

  ledUpdate(SETUPRADIOMODULS, &pinLed); // B On

  // Setup Complete

  buzzerSound(pinBuzzer);
  dataVars.stateTelemetry = 3;
  ledUpdate(SETUPEND, &pinLed); // G On
}

void loop()
{
  subsystemsConnCheck(subsystemList, subsystemsCount);
  subsystemsDataGet(subsystemList, subsystemsCount);
  subsystemsLedUpdate(subsystemList, subsystemsCount, *(pinLed.lowPowerMode));

  uint8_t command = commandReceive(&rc1701hp);
  commandExecute(command, &rc1780hp, &dataVars, &pinLed, &flightMode, subsystemList, subsystemsCount, &subsystemSens, &subsystemControl, pinARM1, pinSLP);

  uint8_t packetIdentifier = packetSendCheck(&flightMode, loopFrequency, timeBetweenStandbyPackets, loopCount);
  packetSend(&rc1780hp, &dataVars, &pinLed, packetIdentifier);
  flashWrite(&dataVars);

  ledUpdate(UPDATE, &pinLed);

  loopVariablesUpdate(&loopCount, &loopStartTime, loopFrequency, pinLed.D1);
}
