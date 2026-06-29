/*
    groundstation - main.cpp of the groundstation for the ASCENT III telemetry system.
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "header.h"
#include "utility.h"

// LED Pins Initialization

ledStruct pinLed;
// MISSING: PIN DECLARATIONS

// Button Pins Initialization

buttonStruct pinButton;
// MISSING: PIN DECLARATIONS

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
RC17xxHP_RC232 rc1780hp(&Serial1, PIN_PC1, PIN_PC0, 19200, PIN_PC4, PIN_PC5, PIN_PC2, PIN_PC3);
// Second D-Sub
RC17xxHP_RC232 rc1701hp(&Serial0, PIN_PA4, PIN_PA5, 19200, PIN_PA3, PIN_PA6, PIN_PA1, PIN_PA2);

dataStruct dataVars;

uint8_t packetBuffer[32];

void setup()
{
  pinLed.pinMode();
  pinButton.pinMode();

  ledUpdate(SETUPBEGIN, pinLed); // R On

  // UART Declarations

  SerialUSB1->pins(pinTX_USB1, pinRX_USB1);
  SerialUSB2->pins(pinTX_USB2, pinRX_USB2);

  SerialUSB1->begin(115200);
  SerialUSB2->begin(115200);

  // Initialize I2C (Display)

  Wire.pins(PIN_PC6, PIN_PC7);
  Wire.begin();

  // Initialize Radio Modules

  radioModulesSetup(&rc1780hp, &rc1701hp, pinLed);

  ledUpdate(SETUPRADIOMODULS, pinLed); // B On

  // Setup Complete

  ledUpdate(SETUPEND, pinLed); // G On
}

void loop()
{
  // Check both USBs for commands
  uint8_t command = commandReceive(SerialUSB1);
  commandExecute(command, &rc1701hp);
  uint8_t command = commandReceive(SerialUSB2);
  commandExecute(command, &rc1701hp);

  buttonCheck(pinButton);
  controlBoxCheck(pinControlBox1, pinControlBox2);

  packetReceive(&rc1780hp, packetBuffer, dataVars);

  dataSendUsb(SerialUSB1);
  dataSendUsb(SerialUSB2);

  displayUpdate(0x00, dataVars);

  ledRssiUpdate(dataVars.rssi, pinLed);
}