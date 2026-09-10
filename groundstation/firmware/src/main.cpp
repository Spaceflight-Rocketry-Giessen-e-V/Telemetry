/*
    groundstation - main.cpp of the groundstation for the ASCENT III telemetry system.
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "header.h"
#include "utility.h"

// LED Pins Initialization

ledStruct pinLed;

// Button Pins Initialization

buttonStruct pinButton;

// Pin Declarations

uint8_t pinControlBox1 = PIN_PE7;
uint8_t pinControlBox2 = PIN_PE6;

// UART Declarations

HardwareSerial *SerialUSB1 = &Serial5;
HardwareSerial *SerialUSB2 = &Serial2;

uint8_t pinTX_USB1 = PIN_PG0;
uint8_t pinRX_USB1 = PIN_PG1;
uint8_t pinTX_USB2 = PIN_PF0;
uint8_t pinRX_USB2 = PIN_PF1;

// Initialize Radio Modules

// First D-Sub
RC17xxHP_RC232 rc1780hp(&Serial4, PIN_PE0, PIN_PE1, 19200, PIN_PE4, PIN_PE5, PIN_PE2, PIN_PE3);
// Second D-Sub
RC17xxHP_RC232 rc1701hp(&Serial1, PIN_PC0, PIN_PC1, 19200, PIN_PC4, PIN_PC5, PIN_PC2, PIN_PC3);

// Packet Declarations

Packet commandPacket;
Packet framePacket;
Packet flightDataPacket;
Packet telemetryDataPacket;

// 

dataStruct dataVars;

uint8_t packetBuffer[32];
uint8_t packetBufferIndex = 0;

void setup()
{
  pinLed.R = PIN_PG5;
  pinLed.G = PIN_PG4;
  pinLed.B = PIN_PG3;
  pinLed.D1 = PIN_PA0;
  pinLed.D2 = PIN_PG7;
  pinLed.D3 = PIN_PG6;
  pinLed.rssi_1 = PIN_PD7;
  pinLed.rssi_2 = PIN_PD6;
  pinLed.rssi_3 = PIN_PD5;
  pinLed.rssi_4 = PIN_PD4;
  pinLed.rssi_5 = PIN_PD3;
  pinLed.rssi_6 = PIN_PD2;
  pinLed.rssi_7 = PIN_PD1;
  pinLed.rssi_8 = PIN_PD0;

  pinLed.pinMode();

  pinButton.sw1 = PIN_PG2;
  pinButton.sw2 = PIN_PF6;
  pinButton.sw3 = PIN_PF5;
  pinButton.sw4 = PIN_PF4;
  pinButton.sw5 = PIN_PF3;
  pinButton.sw6 = PIN_PF2;

  pinButton.pinMode();

  pinMode(pinControlBox1, INPUT);
  pinMode(pinControlBox2, INPUT);

  ledUpdate(SETUPBEGIN, &pinLed); // R On

  // UART Declarations

  SerialUSB1->pins(pinTX_USB1, pinRX_USB1);
  SerialUSB2->pins(pinTX_USB2, pinRX_USB2);

  SerialUSB1->begin(115200);
  SerialUSB2->begin(115200);

  // Initialize I2C (Display)

  // Wire.pins(PIN_PC6, PIN_PC7);
  // Wire.begin();

  // Initialize Radio Modules

  radioModulesSetup(&rc1780hp, &rc1701hp, &pinLed);

  ledUpdate(SETUPRADIOMODULS, &pinLed); // B On

  // Packet Components Initializations

  commandPacket.addComponent(new parity_Component());
  commandPacket.addComponent(new char_Component(&dataVars.command));

  framePacket.addComponent(new cobs_Component(0xEE, 4));
  framePacket.addComponent(new parity_Component());
  framePacket.addComponent(new uint8_t_Component(&dataVars.packetIdentifier, 1, 0, 1));
  framePacket.addComponent(new empty_Component(18));
  framePacket.addComponent(new empty_Component(32));
  framePacket.addComponent(new empty_Component(32));
  framePacket.addComponent(new const_Component(0xEE, 8, 255));
  framePacket.addComponent(new float_Component(&dataVars.rssi, 8, -127.5, 0, 255));

  flightDataPacket.addComponent(new empty_Component(6));
  flightDataPacket.addComponent(new float_Component(&dataVars.acceleration, 10, -17, 17.1));
  flightDataPacket.addComponent(new float_Component(&dataVars.heightPressure, 15, 0, 6553.4));
  flightDataPacket.addComponent(new uint8_t_Component(&dataVars.flightEvents, 5, 0, 31));
  flightDataPacket.addComponent(new float_Component(&dataVars.latitude, 26, -90, 90));
  flightDataPacket.addComponent(new float_Component(&dataVars.longitude, 26, -180, 180));
  flightDataPacket.addComponent(new empty_Component(16));

  telemetryDataPacket.addComponent(new empty_Component(6));
  telemetryDataPacket.addComponent(new empty_Component(2));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.stateTelemetry, 2, 0, 3));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.stateControl, 2, 0, 3));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.statePower, 2, 0, 3));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.stateSens, 2, 0, 3));
  telemetryDataPacket.addComponent(new empty_Component(1));
  telemetryDataPacket.addComponent(new float_Component(&dataVars.heightGNSS, 15, 0, 6553.4));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.satCountGNSS, 4, 0, 15));
  telemetryDataPacket.addComponent(new float_Component(&dataVars.hdopGNSS, 4, 0, 7.5));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.temperatureElectronics, 4, 0, 150));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.temperatureBattery, 4, 0, 150));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.stateCapacitors, 4, 0, 15));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.continuityPyros, 2, 0, 3));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.pressureDecoupler, 1, 0, 1));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.ldrDecoupler, 1, 0, 1));
  telemetryDataPacket.addComponent(new empty_Component(2));
  telemetryDataPacket.addComponent(new float_Component(&dataVars.voltageBattery, 6, 5, 8.15));
  telemetryDataPacket.addComponent(new float_Component(&dataVars.currentBattery, 3, 0, 1.75));
  telemetryDataPacket.addComponent(new float_Component(&dataVars.currentUmbilical, 3, 0, 1.75));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.stateUmbilical, 1, 0, 1));
  telemetryDataPacket.addComponent(new uint8_t_Component(&dataVars.lowPowerMode, 1, 0, 1));
  telemetryDataPacket.addComponent(new float_Component(&dataVars.voltageBatteryCOTS, 5, 5, 11.2));
  telemetryDataPacket.addComponent(new empty_Component(11));
  telemetryDataPacket.addComponent(new empty_Component(16));

  // Setup Complete

  ledUpdate(SETUPEND, &pinLed); // G On
}

void loop()
{
  // Check both USBs for commands
  dataVars.command = commandReceive(SerialUSB1);
  commandExecute(&rc1701hp, dataVars.command, &commandPacket);
  dataVars.command = commandReceive(SerialUSB2);
  commandExecute(&rc1701hp, dataVars.command, &commandPacket);

  buttonCheck(pinButton);
  controlBoxCheck(pinControlBox1, pinControlBox2);

  if (packetReceive(&rc1780hp, packetBuffer, &packetBufferIndex, &dataVars, &framePacket, &flightDataPacket, &telemetryDataPacket) == 0)
  {
    dataSendUsb(SerialUSB1, &dataVars);
    dataSendUsb(SerialUSB2, &dataVars);

    displayUpdate(0x00, &dataVars);

    ledRssiUpdate(dataVars.rssi, &pinLed);
  }
}