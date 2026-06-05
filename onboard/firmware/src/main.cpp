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

  ledStruct pinLed;
  pinLed.D1 = PIN_PF3;
  
  pinLed.pinMode();

  ledUpdate(SETUPBEGIN, pinLed); // R On

  // Pin Declarations
  // Pin Initialisations
  // UART Declarations
  
  // Initialize I2C
  Wire.pins(PIN_PC2, PIN_PC3);
  Wire.begin();

  //RC17xxHP_RC232 rc1780hp();
  //RC17xxHP_RC232 rc1701hp();
  RC17xxHP_RC232 rc1780hp(&Serial1, cfgpin1780, rstpin1780, ctspin1780, rtspin1780);
  RC17xxHP_RC232 rc1701hp(&Serial2, cfgpin1701, rstpin1701, ctspin1701, rtspin1701);

  radioModulesSetup(rc1780hp, rc1701hp);

  ledUpdate(2, pinLed); // B On
  
  dataStruct dataVariables;
  
  // Data Arrays Preparations

  const uint8_t uint8CountPower = 0;
  uint8_t* uint8ListPower[uint8CountPower] = {};
  const uint8_t floatCountPower = 0;
  float* floatListPower[floatCountPower] = {};

  const uint8_t uint8CountSens = 0;
  uint8_t* uint8ListSens[uint8CountSens] = {};
  const uint8_t floatCountSens = 0;
  float* floatListSens[floatCountSens] = {};

  const uint8_t uint8CountControl = 0;
  uint8_t* uint8ListControl[uint8CountControl] = {};
  const uint8_t floatCountControl = 0;
  float* floatListControl[floatCountControl] = {};

  // Subsystems Initialization

  Subsystem subsystemPower(0x50, pinLed.Power, &dataVariables.statePower, uint8ListPower, uint8CountPower, floatListPower, floatCountPower);
  Subsystem subsystemSens(0x20, pinLed.Sens, &dataVariables.stateSens, uint8ListSens, uint8CountSens, floatListSens, floatCountSens);
  Subsystem subsystemControl(0x40, pinLed.Control, &dataVariables.stateControl, uint8ListControl, uint8CountControl, floatListControl, floatCountControl);

  const uint8_t subsystemsCount = 3;
  Subsystem* subsystemList[subsystemsCount] = {&subsystemSens, &subsystemPower, &subsystemControl};

  // Setup Complete

  buzzerSound();

  ledUpdate(3, pinLed); // G On

  const uint8_t loopFrequency = 10;  // in Hz       10 Hz = 100 ms interval
  const uint8_t timeBetweenStandbyPackets = 15; // in seconds. In standby, data packets aren't send every loop
  
  uint8_t flightmode = 0;
  uint16_t loopCount = 0;
  uint32_t loopStartTime = 0;
  
  while(true)
  {
    subsystemsConnCheck(subsystemList, subsystemsCount);

    subsystemsDataGet(subsystemList, subsystemsCount);

    subsystemsLedUpdate(subsystemList, subsystemsCount);

    uint8_t command = commandReceive(rc1701hp);
    commandExecute(command);

    uint8_t packetIdentifier = packetSendCheck(flightmode, loopFrequency, timeBetweenStandbyPackets, loopCount);
    packetSend(rc1780hp, dataVariables, packetIdentifier);

    flashWrite(dataVariables);

    loopVariablesUpdate(&loopCount, &loopStartTime, loopFrequency, pinLed.D1);
  }

  return 0;
}

